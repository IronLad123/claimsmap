import re
from typing import Optional
from app.models.fact import Fact


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


def same_unit(f1: Fact, f2: Fact) -> bool:
    if f1.normalized_unit in ('UNKNOWN', '') or f2.normalized_unit in ('UNKNOWN', ''):
        return False
    return f1.normalized_unit == f2.normalized_unit


def same_scope(f1: Fact, f2: Fact) -> bool:
    b1 = (f1.accounting_basis or '').lower().strip()
    b2 = (f2.accounting_basis or '').lower().strip()
    if not b1 or not b2:
        return True
    return b1 == b2
