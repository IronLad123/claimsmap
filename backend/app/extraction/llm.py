import json
import logging
import time
from typing import List, Dict, Any, Optional
import httpx
from sqlmodel import Session, select

from app.config import (
    GEMINI_API_KEY, DEMO_MODE,
    LLM_PROVIDER, OLLAMA_BASE_URL, OLLAMA_MODEL,
    OPENAI_COMPAT_BASE_URL, OPENAI_COMPAT_API_KEY, OPENAI_COMPAT_MODEL,
)
from app.models.fact import ChunkCache

logger = logging.getLogger("fact_layer.llm")

_pro_client = None
_flash_client = None


class LLMExtractionError(Exception):
    """Raised when LLM extraction fails."""
    pass


def _get_gemini_pro():
    global _pro_client
    if _pro_client is None and GEMINI_API_KEY:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        _pro_client = genai.GenerativeModel("gemini-1.5-pro")
    return _pro_client


def _get_gemini_flash():
    global _flash_client
    if _flash_client is None and GEMINI_API_KEY:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        _flash_client = genai.GenerativeModel("gemini-1.5-flash")
    return _flash_client


EXTRACTION_PROMPT = """You are a precise structured fact extractor for financial and policy documents.
Extract ALL meaningful numerical and semantic facts from the text chunk below (document "{document_id}", page {page_number}).

For each fact, produce a JSON object with these exact keys:
- "entity": string — entity name (e.g. "Delhivery Limited", "India", "Reserve Bank of India")
- "metric_name": string — descriptive label derived from text (e.g. "Revenue from Operations", "Forex Reserves", "Adjusted EBITDA", "Total Workforce Headcount")
- "raw_value": string — value exactly as written in text (e.g. "81,415.38", "-2,491.86", "11", "Excludes daily wage")
- "raw_unit": string — unit if applicable (e.g. "Rs in Million", "Rs Crore", "USD Billion", "months", "PIN codes")
- "data_type": one of: "currency" | "volume" | "percentage" | "count" | "semantic_statement"
- "temporal_label": string — period label (e.g. "FY24", "Q4 FY24", "March 2025", "December 2021")
- "accounting_basis": one of: "standalone" | "consolidated" | "adjusted" | null
- "verbatim_quote": string — exact sentence from this chunk containing the fact

RULES:
- Never fabricate numbers or facts.
- verbatim_quote must be an exact substring from the text below.
- Return a JSON object with a "facts" array: {{"facts": [...]}}

CHUNK TEXT:
{chunk_text}"""


EXPLANATION_PROMPT = """Two facts from different documents have been classified as {relation_type}.

Fact A (from "{doc_a}", page {page_a}):
"{quote_a}"

Fact B (from "{doc_b}", page {page_b}):
"{quote_b}"

Rationale: {rationale}

In 2-4 sentences, explain clearly and specifically WHY these facts are {relation_type}.
Reference the actual numbers, accounting scopes, or definitions. Be concise and precise."""


def is_ollama_online() -> bool:
    """Check if local Ollama server is responding."""
    try:
        r = httpx.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=1.5)
        return r.status_code == 200
    except Exception:
        return False


def query_ollama_json(prompt: str, model: str = OLLAMA_MODEL) -> List[Dict[str, Any]]:
    """Query local Ollama with JSON mode constraint."""
    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
    }
    with httpx.Client(timeout=60.0) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        raw_response = data.get("response", "{}")
        parsed = json.loads(raw_response)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            return parsed.get("facts", parsed.get("data", []))
        return []


def query_ollama_text(prompt: str, model: str = OLLAMA_MODEL) -> str:
    """Query local Ollama for free-form text response."""
    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }
    with httpx.Client(timeout=45.0) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json().get("response", "").strip()


def query_openai_compat_json(prompt: str) -> List[Dict[str, Any]]:
    """Query any OpenAI-compatible API (OrcaRouter, Groq, Together…) for JSON fact extraction."""
    url = f"{OPENAI_COMPAT_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_COMPAT_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": OPENAI_COMPAT_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a precise financial fact extractor. "
                    "Always respond with valid JSON only — no markdown, no explanation. "
                    'Return exactly: {"facts": [...]}'
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.0,
        "max_tokens": 2048,
    }
    with httpx.Client(timeout=60.0) as client:
        resp = client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"].strip()
        # Strip markdown fences if model wraps response
        if content.startswith("```"):
            content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        parsed = json.loads(content)
        if isinstance(parsed, list):
            return parsed
        return parsed.get("facts", parsed.get("data", []))


def query_openai_compat_text(prompt: str) -> str:
    """Query any OpenAI-compatible API for a free-form text response."""
    url = f"{OPENAI_COMPAT_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_COMPAT_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": OPENAI_COMPAT_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 512,
    }
    with httpx.Client(timeout=45.0) as client:
        resp = client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()


def extract_facts_from_chunk(
    chunk_text: str,
    document_id: str,
    page_number: int,
    chunk_hash: str,
    session: Session,
    max_retries: int = 2,
) -> Optional[List[Dict[str, Any]]]:
    """Extract facts from a chunk using available provider (Ollama or Gemini).
    Checks cache first.
    Returns None if no LLM provider is available (signals deterministic fallback).
    """
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
            pass

    prompt = EXTRACTION_PROMPT.format(
        document_id=document_id,
        page_number=page_number,
        chunk_text=chunk_text[:3500],
    )

    def _save_cache(facts_list):
        cache_entry = ChunkCache(
            document_id=document_id,
            chunk_hash=chunk_hash,
            extracted_json=json.dumps(facts_list),
        )
        session.add(cache_entry)
        session.commit()

    # Provider 1: OpenAI-compatible (OrcaRouter, Groq, Together, etc.)
    if LLM_PROVIDER == "openai_compat" and OPENAI_COMPAT_BASE_URL and OPENAI_COMPAT_API_KEY:
        for attempt in range(max_retries + 1):
            try:
                logger.info(
                    "Extracting chunk %s with OpenAI-compat provider %s (attempt %d)",
                    chunk_hash[:8], OPENAI_COMPAT_MODEL, attempt + 1,
                )
                facts = query_openai_compat_json(prompt)
                _save_cache(facts)
                return facts
            except Exception as e:
                logger.warning("OpenAI-compat attempt %d failed: %s", attempt + 1, e)
                if attempt < max_retries:
                    time.sleep(1.0)
        logger.error("OpenAI-compat provider exhausted retries for chunk %s", chunk_hash[:8])
        return None  # Deterministic fallback

    # Provider 2: Ollama (local)
    if LLM_PROVIDER == "ollama" or is_ollama_online():
        try:
            logger.info("Extracting chunk %s with local Ollama (%s)", chunk_hash[:8], OLLAMA_MODEL)
            facts = query_ollama_json(prompt, model=OLLAMA_MODEL)
            _save_cache(facts)
            return facts
        except Exception as e:
            logger.warning("Ollama extraction failed on chunk %s: %s", chunk_hash[:8], e)
            if not GEMINI_API_KEY:
                return None

    # Provider 3: Gemini
    if GEMINI_API_KEY and not DEMO_MODE:
        client = _get_gemini_pro()
        if client:
            for attempt in range(max_retries + 1):
                try:
                    logger.info("Extracting chunk %s with Gemini Pro (attempt %d)", chunk_hash[:8], attempt + 1)
                    res = client.generate_content(prompt)
                    raw = res.text.strip()
                    if raw.startswith("```"):
                        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
                    parsed = json.loads(raw)
                    facts = parsed if isinstance(parsed, list) else parsed.get("facts", [])
                    _save_cache(facts)
                    return facts
                except Exception as e:
                    logger.warning("Gemini attempt %d failed: %s", attempt + 1, e)
                    if attempt < max_retries:
                        time.sleep(1.0)
                    else:
                        raise LLMExtractionError(f"Gemini failed: {e}")

    return None


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
    """Generate narrative explanation using Ollama, Gemini, or fallback rationale."""
    prompt = EXPLANATION_PROMPT.format(
        relation_type=relation_type,
        doc_a=doc_a, page_a=page_a, quote_a=quote_a[:350],
        doc_b=doc_b, page_b=page_b, quote_b=quote_b[:350],
        rationale=rationale,
    )

    # Provider 1: OpenAI-compatible (OrcaRouter, Groq, Together, etc.)
    if LLM_PROVIDER == "openai_compat" and OPENAI_COMPAT_BASE_URL and OPENAI_COMPAT_API_KEY:
        try:
            return query_openai_compat_text(prompt)
        except Exception as e:
            logger.warning("OpenAI-compat explanation generation failed: %s", e)

    # Provider 2: Ollama (local)
    if LLM_PROVIDER == "ollama" or is_ollama_online():
        try:
            return query_ollama_text(prompt, model=OLLAMA_MODEL)
        except Exception as e:
            logger.warning("Ollama explanation generation failed: %s", e)

    # Provider 3: Gemini
    if GEMINI_API_KEY and not DEMO_MODE:
        client = _get_gemini_flash()
        if client:
            try:
                res = client.generate_content(prompt)
                return res.text.strip()
            except Exception:
                pass

    return rationale
