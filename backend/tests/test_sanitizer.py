from app.ingestion.sanitizer import sanitize_text, parse_fy_to_iso, clean_numeric


def test_parens_negative_simple():
    assert sanitize_text('EBITDA (217) million') == 'EBITDA -217 million'


def test_parens_negative_large():
    assert sanitize_text('Loss (10,077.79) million') == 'Loss -10,077.79 million'


def test_parens_negative_only():
    assert sanitize_text('(404)') == '-404'


def test_footnote_strip():
    assert sanitize_text('18,793(1)') == '18,793'
    assert sanitize_text('(217)') == '-217'
    assert sanitize_text('18,793(1) with loss (217)') == '18,793 with loss -217'
    assert sanitize_text('>2.8Bn[1] shipments') == '>2.8Bn shipments'


def test_fy24_short():
    iso = parse_fy_to_iso('FY24')
    assert iso['start'] == '2023-04-01'
    assert iso['end'] == '2024-03-31'


def test_fy2024_long():
    iso = parse_fy_to_iso('FY2024')
    assert iso['start'] == '2023-04-01'
    assert iso['end'] == '2024-03-31'


def test_fy_slash():
    iso = parse_fy_to_iso('FY2023/24')
    assert iso['start'] == '2023-04-01'
    assert iso['end'] == '2024-03-31'


def test_fy_dash():
    iso = parse_fy_to_iso('FY2023-24')
    assert iso['start'] == '2023-04-01'
    assert iso['end'] == '2024-03-31'


def test_clean_numeric():
    assert clean_numeric('81,415.38') == 81415.38
    assert clean_numeric('-2,491.86') == -2491.86
    assert clean_numeric('8,142') == 8142.0
    assert clean_numeric('abc') is None
    assert clean_numeric('') is None
