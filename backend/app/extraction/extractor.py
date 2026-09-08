import re
import logging
from typing import List, Optional, Tuple, Dict, Any
from sqlmodel import Session

from app.ingestion.parser import Chunk
from app.ingestion.sanitizer import parse_fy_to_iso, clean_numeric
from app.extraction.gemini import extract_facts_from_chunk, GeminiExtractionError
from app.models.fact import Fact

logger = logging.getLogger("fact_layer.extractor")

# Ordered exact unit mapping.
# Specific composite units MUST appear before general single-word units
EXACT_UNIT_MAP: Dict[str, Tuple[str, float]] = {
    # Shipments & counts (evaluated first to prevent "million shipments" matching currency)
    "million shipments": ("SHIPMENTS", 1_000_000),
    "mn shipments": ("SHIPMENTS", 1_000_000),
    "billion shipments": ("SHIPMENTS", 1_000_000_000),
    "shipments": ("SHIPMENTS", 1),
    "pin codes": ("PIN_CODES", 1),
    "pincodes": ("PIN_CODES", 1),
    "months": ("MONTHS", 1),
    "month": ("MONTHS", 1),
    "employees": ("HEADCOUNT", 1),
    "workforce": ("HEADCOUNT", 1),
    "contractual manpower": ("HEADCOUNT", 1),
    "people": ("HEADCOUNT", 1),
    # INR Currency
    "rs in million": ("INR", 1_000_000),
    "inr million": ("INR", 1_000_000),
    "rs million": ("INR", 1_000_000),
    "million inr": ("INR", 1_000_000),
    "rs in crore": ("INR", 10_000_000),
    "rs crore": ("INR", 10_000_000),
    "rs cr": ("INR", 10_000_000),
    "inr crore": ("INR", 10_000_000),
    "inr cr": ("INR", 10_000_000),
    "crore": ("INR", 10_000_000),
    "cr": ("INR", 10_000_000),
    # USD Currency
    "usd billion": ("USD", 1_000_000_000),
    "us$ billion": ("USD", 1_000_000_000),
    "$ billion": ("USD", 1_000_000_000),
    "billion usd": ("USD", 1_000_000_000),
    "usd bn": ("USD", 1_000_000_000),
    "usd million": ("USD", 1_000_000),
    "us$ million": ("USD", 1_000_000),
    "$ million": ("USD", 1_000_000),
    # Percentages & ratios
    "% of gdp": ("PCT", 1),
    "percent of gdp": ("PCT", 1),
    "%": ("PCT", 1),
    "percent": ("PCT", 1),
    "percentage": ("PCT", 1),
}


def normalize_unit(raw_unit: str) -> Tuple[str, float]:
    """Normalize raw unit string with exact match priority and ordered composite fallback."""
    if not raw_unit:
        return ("UNKNOWN", 1.0)

    clean_key = re.sub(r"\s+", " ", raw_unit.lower().strip())

    # 1. Exact match
    if clean_key in EXACT_UNIT_MAP:
        return EXACT_UNIT_MAP[clean_key]

    # 2. Guard: if unit explicitly refers to physical volume or counts, never match as currency
    if any(w in clean_key for w in ("shipment", "parcel", "box", "package")):
        if "mn" in clean_key or "million" in clean_key:
            return ("SHIPMENTS", 1_000_000)
        return ("SHIPMENTS", 1)

    if any(w in clean_key for w in ("pin", "code", "center", "hub", "facility")):
        return ("PIN_CODES", 1)

    if any(w in clean_key for w in ("employee", "worker", "headcount", "manpower", "agent")):
        return ("HEADCOUNT", 1)

    if "month" in clean_key:
        return ("MONTHS", 1)

    # 3. Ordered prefix/substring match
    for k, v in EXACT_UNIT_MAP.items():
        if k in clean_key:
            return v

    # 4. Fallback for standalone million/billion (check currency markers)
    if "billion" in clean_key or "bn" in clean_key:
        if "$" in clean_key or "usd" in clean_key:
            return ("USD", 1_000_000_000)
        return ("UNITS_BN", 1_000_000_000)

    if "million" in clean_key or "mn" in clean_key:
        if "rs" in clean_key or "₹" in clean_key or "inr" in clean_key:
            return ("INR", 1_000_000)
        return ("UNITS_MN", 1_000_000)

    return ("UNKNOWN", 1.0)


def verify_grounding(quote: str, chunk_text: str) -> bool:
    """Validate that the verbatim quote exists in the source text chunk."""
    if not quote or not chunk_text:
        return False
    # Exact substring match
    if quote in chunk_text:
        return True
    # Normalized whitespace match
    norm_quote = re.sub(r"\s+", " ", quote.strip().lower())
    norm_chunk = re.sub(r"\s+", " ", chunk_text.strip().lower())
    return norm_quote in norm_chunk


def extract_deterministic_facts(
    chunk_text: str,
    page_number: int,
    document_id: str,
) -> List[Dict[str, Any]]:
    """Deterministic, rule-based factual extractor used in DEMO_MODE or as fallback.
    Guarantees every extracted fact is 100% grounded with an exact quote.
    """
    facts: List[Dict[str, Any]] = []

    # Detect entity context
    entity = "Delhivery Limited" if "delhivery" in chunk_text.lower() else (
        "Reserve Bank of India" if "reserve bank" in chunk_text.lower() or "rbi" in chunk_text.lower() else (
            "International Monetary Fund" if "imf" in chunk_text.lower() else "India"
        )
    )

    lines = chunk_text.split("\n")
    for line in lines:
        line_clean = line.strip()
        if len(line_clean) < 15 or len(line_clean) > 300:
            continue

        # Pattern 1: Revenue or Financial statements
        # e.g., "Revenue from Operations: 81,415.38 (Rs in Million)"
        rev_match = re.search(
            r"(Revenue from Operations|Revenue from Services|Adjusted EBITDA|Loss for the year|PAT|Net Loss)"
            r"[^0-9\-]*([\-–]?[0-9,]+\.?[0-9]*)\s*([A-Za-z\$\%₹\(\) ]*)",
            line_clean,
            re.IGNORECASE,
        )
        if rev_match:
            metric = rev_match.group(1).strip()
            val = rev_match.group(2).strip().replace("–", "-")
            unit_str = rev_match.group(3).strip()
            unit_str = re.sub(r"[\(\)]", "", unit_str).strip()
            basis = "standalone" if "standalone" in line_clean.lower() else (
                "consolidated" if "consolidated" in line_clean.lower() else (
                    "adjusted" if "adjusted" in metric.lower() else None
                )
            )
            fy_match = re.search(r"(FY\s*\d{2,4}|Q[1-4]\s*FY\s*\d{2,4})", line_clean, re.IGNORECASE)
            temporal = fy_match.group(1).strip() if fy_match else "FY24"

            facts.append({
                "entity": entity,
                "metric_name": metric,
                "raw_value": val,
                "raw_unit": unit_str or "Rs in Million",
                "data_type": "currency",
                "temporal_label": temporal,
                "accounting_basis": basis,
                "verbatim_quote": line_clean,
            })
            continue

        # Pattern 2: Foreign Exchange Reserves or Macro metrics
        macro_match = re.search(
            r"(forex reserves|foreign exchange reserves|import cover|fiscal deficit)"
            r"[^0-9]*([0-9,]+\.?[0-9]*)\s*(billion|months|percent|%)?",
            line_clean,
            re.IGNORECASE,
        )
        if macro_match:
            metric_raw = macro_match.group(1).title()
            val = macro_match.group(2)
            unit_hint = (macro_match.group(3) or "").strip()
            dtype = "count" if "month" in unit_hint else ("percentage" if "%" in unit_hint else "currency")
            unit_val = "months" if "month" in unit_hint else ("USD Billion" if "billion" in unit_hint else "%")

            facts.append({
                "entity": "India",
                "metric_name": metric_raw,
                "raw_value": val,
                "raw_unit": unit_val,
                "data_type": dtype,
                "temporal_label": "March 2025" if "2025" in line_clean else "FY25",
                "accounting_basis": None,
                "verbatim_quote": line_clean,
            })
            continue

        # Pattern 3: Operational metrics (PIN codes, express parcel shipments, headcount)
        ops_match = re.search(
            r"([0-9,]+)\s*(PIN codes|express parcel shipments|workforce strength|employees)",
            line_clean,
            re.IGNORECASE,
        )
        if ops_match:
            val = ops_match.group(1)
            metric_raw = ops_match.group(2).title()
            facts.append({
                "entity": entity,
                "metric_name": metric_raw,
                "raw_value": val,
                "raw_unit": metric_raw.lower(),
                "data_type": "count",
                "temporal_label": "FY24",
                "accounting_basis": None,
                "verbatim_quote": line_clean,
            })

    return facts


def process_chunks(
    chunks: List[Chunk],
    document_id: str,
    session: Session,
    file_hash: str = "",
    allow_fallback: bool = True,
) -> List[Fact]:
    """Extract, validate, ground, and persist facts from document chunks.
    Raises GeminiExtractionError if in live mode and Gemini fails.
    """
    facts: List[Fact] = []
    seen_quotes: set = set()

    for chunk in chunks:
        raw_facts = None
        used_model = "gemini-1.5-pro"

        # Try primary extraction
        try:
            raw_facts = extract_facts_from_chunk(
                chunk_text=chunk.raw_text,
                document_id=document_id,
                page_number=chunk.page_number,
                chunk_hash=chunk.hash(),
                session=session,
            )
        except GeminiExtractionError as e:
            if not allow_fallback:
                raise
            logger.warning("Gemini failed on chunk %s: %s. Using deterministic extractor fallback.", chunk.hash()[:8], e)
            raw_facts = None

        # Fallback to deterministic rule-based extractor
        if raw_facts is None:
            raw_facts = extract_deterministic_facts(
                chunk_text=chunk.raw_text,
                page_number=chunk.page_number,
                document_id=document_id,
            )
            used_model = "deterministic-rule-v1"

        for rf in raw_facts:
            try:
                quote = str(rf.get("verbatim_quote", "")).strip()
                if not quote or len(quote) < 8:
                    continue
                if quote in seen_quotes:
                    continue
                seen_quotes.add(quote)

                # Grounding verification
                is_grounded = verify_grounding(quote, chunk.raw_text)
                if not is_grounded:
                    logger.warning("Fact rejected: quote not found in chunk (hallucination guard): '%s'", quote[:60])
                    continue

                raw_unit = str(rf.get("raw_unit", ""))
                norm_unit, multiplier = normalize_unit(raw_unit)
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
                    confidence=0.95 if is_grounded else 0.50,
                    chunk_index=chunk.chunk_index,
                    file_hash=file_hash,
                    chunk_hash=chunk.hash(),
                    extractor_model=used_model,
                    prompt_version="v2.1",
                    grounding_verified=is_grounded,
                )
                session.add(fact)
                facts.append(fact)
            except Exception as e:
                logger.error("Error creating Fact instance: %s", e)
                continue

    session.commit()
    logger.info("Persisted %d facts for document %s", len(facts), document_id)
    return facts
