from app.extraction.extractor import normalize_unit, verify_grounding


def test_shipment_unit_not_inr():
    unit, mult = normalize_unit("million shipments")
    assert unit == "SHIPMENTS"
    assert mult == 1_000_000

    unit, mult = normalize_unit("mn shipments")
    assert unit == "SHIPMENTS"
    assert mult == 1_000_000


def test_inr_currency_units():
    unit, mult = normalize_unit("rs in million")
    assert unit == "INR"
    assert mult == 1_000_000

    unit, mult = normalize_unit("rs crore")
    assert unit == "INR"
    assert mult == 10_000_000

    unit, mult = normalize_unit("rs cr")
    assert unit == "INR"
    assert mult == 10_000_000


def test_usd_currency_units():
    unit, mult = normalize_unit("usd billion")
    assert unit == "USD"
    assert mult == 1_000_000_000

    unit, mult = normalize_unit("us$ billion")
    assert unit == "USD"
    assert mult == 1_000_000_000


def test_counts_and_metrics():
    unit, mult = normalize_unit("pin codes")
    assert unit == "PIN_CODES"
    assert mult == 1

    unit, mult = normalize_unit("months")
    assert unit == "MONTHS"
    assert mult == 1


def test_verify_grounding_exact_and_normalized():
    chunk = "In FY24, consolidated Revenue from Operations was Rs 81,415.38 Million."
    assert verify_grounding("Revenue from Operations was Rs 81,415.38 Million", chunk) is True
    assert verify_grounding("revenue  from operations was   rs 81,415.38 million", chunk) is True
    assert verify_grounding("Revenue from Operations was Rs 99,999.00 Million", chunk) is False
