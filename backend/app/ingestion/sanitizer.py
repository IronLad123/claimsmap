import re
from typing import Optional, Dict

_PARENS_NEG = re.compile(r'\(([0-9][0-9,\.]+)\)')
_FOOTNOTE = re.compile(r'([0-9,\.]+)\s*\(\d+\)')
_SUPER_BRACKET = re.compile(r'([0-9,\.]+)\s*\[\d+\]')
_FY_SHORT = re.compile(r'\bFY\s*(\d{2})\b')
_FY_LONG = re.compile(r'\bFY\s*(\d{4})\b')
_FY_SLASH = re.compile(r'\bFY\s*(\d{4})/(\d{2,4})\b')
_FY_DASH = re.compile(r'\bFY\s*(\d{4})-(\d{2,4})\b')


def sanitize_text(text: str) -> str:
    """Apply all sanitization passes to raw PDF extracted text."""
    # Pass 1: parenthetical negatives  (217) -> -217
    text = _PARENS_NEG.sub(lambda m: f'-{m.group(1)}', text)
    # Pass 2a: footnote markers  18,793(1) -> 18,793
    text = _FOOTNOTE.sub(lambda m: m.group(1), text)
    # Pass 2b: bracket markers  18,793[1] -> 18,793
    text = _SUPER_BRACKET.sub(lambda m: m.group(1), text)
    return text


def parse_fy_to_iso(label: str) -> Dict[str, str]:
    """Parse Indian fiscal year label to ISO date interval dict {start, end}.
    Indian FY: April 1 of start_year to March 31 of start_year+1.
    """
    if not label:
        return {}

    # FY2023/24 or FY2023-24
    m = _FY_SLASH.search(label) or _FY_DASH.search(label)
    if m:
        start_year = int(m.group(1))
        return {"start": f"{start_year}-04-01", "end": f"{start_year + 1}-03-31"}

    # FY2024 (four digits)
    m = _FY_LONG.search(label)
    if m:
        y = int(m.group(1))
        # FY2024 = April 2023 to March 2024
        return {"start": f"{y - 1}-04-01", "end": f"{y}-03-31"}

    # FY24 (two digits)
    m = _FY_SHORT.search(label)
    if m:
        y = 2000 + int(m.group(1))
        return {"start": f"{y - 1}-04-01", "end": f"{y}-03-31"}

    # Try to extract a 4-digit calendar year as point-in-time
    yr = re.search(r'\b(20\d{2})\b', label)
    if yr:
        y = int(yr.group(1))
        return {"start": f"{y}-01-01", "end": f"{y}-12-31"}

    return {}


def clean_numeric(val: str) -> Optional[float]:
    """Parse a numeric string like '81,415.38' or '-404' to float."""
    if not val:
        return None
    try:
        cleaned = (
            val.replace(',', '')
               .replace('\u20b9', '')
               .replace('$', '')
               .replace('%', '')
               .replace('>', '')
               .replace('<', '')
               .strip()
        )
        return float(cleaned)
    except (ValueError, AttributeError):
        return None
