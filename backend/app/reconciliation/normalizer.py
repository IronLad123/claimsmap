import re
from typing import Optional
from app.models.fact import Fact


METRIC_FAMILIES = {
    "revenue": ["revenue from operations", "revenue from services", "total revenue", "turnover", "sales"],
    "profitability": ["adjusted ebitda", "ebitda", "profit after tax", "pat", "loss for the year", "net loss", "net profit"],
    "reserves": ["foreign exchange reserves", "forex reserves", "fx reserves", "international reserves"],
    "import_cover": ["import cover", "forex reserves import cover", "months of imports", "merchandise imports cover"],
    "workforce": ["workforce strength", "total workforce", "headcount", "employees", "manpower"],
    "shipments": ["express parcel shipments", "shipments", "parcel volume"],
    "coverage": ["pin codes", "pincodes", "pin code coverage", "facilities", "hubs"],
    "deficit": ["fiscal deficit", "gross fiscal deficit", "revenue deficit"],
}


def get_metric_family(metric: str) -> str:
    m = metric.lower().strip()
    for fam, syns in METRIC_FAMILIES.items():
        if any(s in m for s in syns):
            return fam
    return m


def temporal_overlap(f1: Fact, f2: Fact, tolerance_days: int = 45) -> bool:
    if f1.temporal_end and f2.temporal_end:
        try:
            from datetime import date
            e1 = date.fromisoformat(f1.temporal_end)
            e2 = date.fromisoformat(f2.temporal_end)
            return abs((e1 - e2).days) <= tolerance_days
        except Exception:
            pass
    return _label_overlap(f1.temporal_label, f2.temporal_label)


def _label_overlap(l1: str, l2: str) -> bool:
    l1, l2 = l1.upper().strip(), l2.upper().strip()
    if not l1 or not l2:
        return False
    years1 = set(re.findall(r'20\d{2}', l1)) | set(re.findall(r'FY\d{2}', l1))
    years2 = set(re.findall(r'20\d{2}', l2)) | set(re.findall(r'FY\d{2}', l2))
    return bool(years1 & years2)


def value_delta(f1: Fact, f2: Fact) -> Optional[float]:
    if f1.normalized_magnitude is None or f2.normalized_magnitude is None:
        return None
    denom = max(abs(f1.normalized_magnitude), abs(f2.normalized_magnitude), 1e-9)
    return abs(f1.normalized_magnitude - f2.normalized_magnitude) / denom


def compatible_units(f1: Fact, f2: Fact) -> bool:
    """Check if two facts have compatible measurement dimensions."""
    # Semantic statements do not require numeric units
    if f1.data_type == "semantic_statement" and f2.data_type == "semantic_statement":
        return True

    u1 = f1.normalized_unit
    u2 = f2.normalized_unit
    if not u1 or not u2 or u1 == "UNKNOWN" or u2 == "UNKNOWN":
        return False

    return u1 == u2


def same_scope(f1: Fact, f2: Fact) -> bool:
    b1 = (f1.accounting_basis or '').lower().strip()
    b2 = (f2.accounting_basis or '').lower().strip()
    if not b1 or not b2:
        return True
    return b1 == b2


def detect_methodology_difference(f1: Fact, f2: Fact) -> bool:
    """Detect if two facts measuring the same concept differ in underlying accounting or calculation methodology."""
    text1 = f"{f1.metric_name} {f1.verbatim_quote}".lower()
    text2 = f"{f2.metric_name} {f2.verbatim_quote}".lower()

    # Import cover: merchandise (goods-only) trailing vs prospective (goods + services)
    if ("merchandise" in text1 and "prospective" in text2) or ("merchandise" in text2 and "prospective" in text1):
        return True
    if ("merchandise" in text1 and "services" in text2) or ("merchandise" in text2 and "services" in text1):
        return True

    # Profitability: Adjusted EBITDA (operating cash flow) vs Net PAT (statutory bottom line)
    if ("ebitda" in text1 and any(w in text2 for w in ("pat", "loss for the year", "net loss", "net profit"))) or \
       ("ebitda" in text2 and any(w in text1 for w in ("pat", "loss for the year", "net loss", "net profit"))):
        return True

    # Accounting basis variation where one is adjusted and the other is statutory
    if (f1.accounting_basis == "adjusted" and f2.accounting_basis in ("consolidated", "standalone")) or \
       (f2.accounting_basis == "adjusted" and f1.accounting_basis in ("consolidated", "standalone")):
        return True

    return False
