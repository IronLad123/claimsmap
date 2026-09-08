from typing import List, Optional
from sqlmodel import Session

from app.ingestion.parser import Chunk
from app.ingestion.sanitizer import parse_fy_to_iso, clean_numeric
from app.extraction.gemini import extract_facts_from_chunk
from app.models.fact import Fact

UNIT_MAP = {
    "rs in million": ("INR", 1_000_000),
    "inr million": ("INR", 1_000_000),
    "rs million": ("INR", 1_000_000),
    "rs in crore": ("INR", 10_000_000),
    "rs cr": ("INR", 10_000_000),
    "rs crore": ("INR", 10_000_000),
    "inr crore": ("INR", 10_000_000),
    "crore": ("INR", 10_000_000),
    "million": ("INR", 1_000_000),
    "usd billion": ("USD", 1_000_000_000),
    "us$ billion": ("USD", 1_000_000_000),
    "$ billion": ("USD", 1_000_000_000),
    "billion": ("USD", 1_000_000_000),
    "usd million": ("USD", 1_000_000),
    "% of gdp": ("PCT", 1),
    "%": ("PCT", 1),
    "percent": ("PCT", 1),
    "million shipments": ("SHIPMENTS", 1_000_000),
    "mn shipments": ("SHIPMENTS", 1_000_000),
    "mn": ("UNITS_MN", 1_000_000),
    "pin codes": ("PIN_CODES", 1),
    "months": ("MONTHS", 1),
    "employees": ("HEADCOUNT", 1),
    "workforce": ("HEADCOUNT", 1),
}


def _normalize_unit(raw_unit: str):
    key = raw_unit.lower().strip()
    for k, v in UNIT_MAP.items():
        if k in key:
            return v
    return ("UNKNOWN", 1)


def process_chunks(chunks: List[Chunk], document_id: str, session: Session) -> List[Fact]:
    """Extract, validate and persist facts from all chunks."""
    facts: List[Fact] = []
    seen_quotes: set = set()

    for chunk in chunks:
        raw_facts = extract_facts_from_chunk(
            chunk_text=chunk.raw_text,
            document_id=document_id,
            page_number=chunk.page_number,
            chunk_hash=chunk.hash(),
            session=session,
        )

        for rf in raw_facts:
            try:
                quote = str(rf.get("verbatim_quote", "")).strip()
                if not quote or len(quote) < 10:
                    continue
                if quote in seen_quotes:
                    continue
                seen_quotes.add(quote)

                raw_unit = str(rf.get("raw_unit", ""))
                norm_unit, multiplier = _normalize_unit(raw_unit)
                raw_val = str(rf.get("raw_value", ""))
                num_val = clean_numeric(raw_val)
                norm_mag = (num_val * multiplier) if num_val is not None else None

                temporal_label = str(rf.get("temporal_label", ""))
                iso = parse_fy_to_iso(temporal_label)

                ab = rf.get("accounting_basis")
                accounting_basis = None if (not ab or str(ab).lower() in ("null", "none", "")) else str(ab)

                fact = Fact(
                    document_id=document_id,
                    entity=str(rf.get("entity", "Unknown")).strip()[:200],
                    metric_name=str(rf.get("metric_name", "Unknown")).strip()[:300],
                    raw_value=raw_val[:100],
                    numeric_value=num_val,
                    raw_unit=raw_unit[:100],
                    normalized_unit=norm_unit,
                    normalized_magnitude=norm_mag,
                    data_type=str(rf.get("data_type", "semantic_statement")),
                    temporal_label=temporal_label[:100],
                    temporal_start=iso.get("start"),
                    temporal_end=iso.get("end"),
                    accounting_basis=accounting_basis,
                    verbatim_quote=quote[:1000],
                    page_number=chunk.page_number,
                    confidence=0.85,
                    chunk_index=chunk.chunk_index,
                )
                session.add(fact)
                facts.append(fact)
            except Exception:
                continue

    session.commit()
    return facts
