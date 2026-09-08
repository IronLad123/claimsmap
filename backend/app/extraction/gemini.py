import hashlib
import json
from typing import List, Dict, Any
from sqlmodel import Session, select

from app.config import GEMINI_API_KEY, DEMO_MODE
from app.models.fact import ChunkCache

_pro_client = None
_flash_client = None


def _get_pro():
    global _pro_client
    if _pro_client is None and GEMINI_API_KEY:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        _pro_client = genai.GenerativeModel("gemini-1.5-pro")
    return _pro_client


def _get_flash():
    global _flash_client
    if _flash_client is None and GEMINI_API_KEY:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        _flash_client = genai.GenerativeModel("gemini-1.5-flash")
    return _flash_client


EXTRACTION_PROMPT = """You are a precise structured fact extractor for financial and policy documents.
Given the text chunk below from document "{document_id}" (page {page_number}), extract ALL meaningful numerical and semantic facts.

For each fact output a JSON object with exactly these fields:
- entity: string — company, country, or institution name (e.g. "Delhivery Limited", "India", "Reserve Bank of India")
- metric_name: string — open-ended label derived from context (e.g. "Revenue from Operations", "Forex Reserves", "Express Parcel Shipments")
- raw_value: string — exact value as it appears in the text
- raw_unit: string — e.g. "Rs in Million", "USD Billion", "% of GDP", "months", "PIN codes"
- data_type: one of: currency | volume | percentage | count | semantic_statement
- temporal_label: string — e.g. "FY24", "Q4 FY24", "end-March 2025", "as of December 31 2021"
- accounting_basis: one of: standalone | consolidated | adjusted | pro_forma | null
- verbatim_quote: exact sentence(s) from this chunk that contain the fact

RULES:
- Do NOT invent facts. Extract only what is explicitly stated.
- metric_name is free-form — derive it entirely from document context. No fixed list.
- Negative values are already in -N format (pre-processed before this prompt).
- verbatim_quote must be a real substring of the chunk text.
- For semantic facts (appointments, governance), set data_type to semantic_statement.
- If no extractable facts exist, return an empty array [].

Output: a valid JSON array only. No markdown fences, no explanation.

CHUNK TEXT:
{chunk_text}"""


EXPLANATION_PROMPT = """Two facts from different documents have been classified as {relation_type}.

Fact A — from "{doc_a}", page {page_a}:
"{quote_a}"

Fact B — from "{doc_b}", page {page_b}:
"{quote_b}"

Classification rationale: {rationale}

In 2-4 sentences, explain clearly and specifically WHY these facts are {relation_type}.
Reference the actual numbers, time periods, accounting scopes, or definitions involved.
Be precise. No vague language. No bullet points — write flowing prose."""


def extract_facts_from_chunk(
    chunk_text: str,
    document_id: str,
    page_number: int,
    chunk_hash: str,
    session: Session,
) -> List[Dict[str, Any]]:
    """Extract facts from a chunk, using cache if available."""
    cached = session.exec(
        select(ChunkCache).where(
            ChunkCache.document_id == document_id,
            ChunkCache.chunk_hash == chunk_hash,
        )
    ).first()
    if cached:
        try:
            return json.loads(cached.extracted_json)
        except Exception:
            return []

    if DEMO_MODE:
        return []

    client = _get_pro()
    if not client:
        return []

    prompt = EXTRACTION_PROMPT.format(
        document_id=document_id,
        page_number=page_number,
        chunk_text=chunk_text[:4000],
    )

    try:
        response = client.generate_content(prompt)
        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]
            raw = raw.rsplit("```", 1)[0].strip()
        facts = json.loads(raw)
        if not isinstance(facts, list):
            facts = []
    except Exception:
        facts = []

    cache_entry = ChunkCache(
        document_id=document_id,
        chunk_hash=chunk_hash,
        extracted_json=json.dumps(facts),
    )
    session.add(cache_entry)
    session.commit()

    return facts


def generate_explanation(
    relation_type: str,
    doc_a: str,
    page_a: int,
    quote_a: str,
    doc_b: str,
    page_b: int,
    quote_b: str,
    rationale: str,
) -> str:
    """Generate human-readable explanation for a cross-document link."""
    if DEMO_MODE:
        return rationale

    client = _get_flash()
    if not client:
        return rationale

    prompt = EXPLANATION_PROMPT.format(
        relation_type=relation_type,
        doc_a=doc_a, page_a=page_a, quote_a=quote_a[:400],
        doc_b=doc_b, page_b=page_b, quote_b=quote_b[:400],
        rationale=rationale,
    )

    try:
        response = client.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return rationale
