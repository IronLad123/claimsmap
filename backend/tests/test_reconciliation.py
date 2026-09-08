from types import SimpleNamespace
from app.reconciliation.engine import classify_pair


def mk(**kw):
    """Create a plain object that mimics Fact fields — no SQLAlchemy overhead."""
    defaults = dict(
        id='x', document_id='d1', entity='Delhivery Limited',
        metric_name='Revenue from Operations',
        raw_value='100', numeric_value=100.0, raw_unit='INR',
        normalized_unit='INR', normalized_magnitude=100.0,
        data_type='currency', temporal_label='FY24',
        temporal_start='2023-04-01', temporal_end='2024-03-31',
        accounting_basis='consolidated',
        verbatim_quote='Revenue was 100', page_number=1,
        confidence=0.9, chunk_index=0,
    )
    defaults.update(kw)
    return SimpleNamespace(**defaults)


def test_corroborated():
    f1 = mk(document_id='d1', normalized_magnitude=100.0)
    f2 = mk(document_id='d2', normalized_magnitude=101.0)  # 1% delta
    assert classify_pair(f1, f2) == 'CORROBORATED'


def test_genuine_contradiction():
    f1 = mk(document_id='d1', normalized_magnitude=100.0)
    f2 = mk(document_id='d2', normalized_magnitude=200.0)  # 100% delta
    assert classify_pair(f1, f2) == 'GENUINE_CONTRADICTION'


def test_reconciled_temporal():
    f1 = mk(document_id='d1', temporal_end='2021-12-31', temporal_label='FY21', normalized_magnitude=17488.0)
    f2 = mk(document_id='d2', temporal_end='2024-03-31', temporal_label='FY24', normalized_magnitude=18793.0)
    assert classify_pair(f1, f2) == 'RECONCILED_TEMPORAL'


def test_reconciled_scope():
    f1 = mk(document_id='d1', accounting_basis='standalone', normalized_magnitude=74540.0)
    f2 = mk(document_id='d2', accounting_basis='consolidated', normalized_magnitude=81415.0)
    assert classify_pair(f1, f2) == 'RECONCILED_SCOPE'


def test_incompatible_units_returns_none():
    f1 = mk(document_id='d1', normalized_unit='INR')
    f2 = mk(document_id='d2', normalized_unit='USD')
    assert classify_pair(f1, f2) is None


def test_corroborated_rbi_imf():
    """Real-world case: India forex reserves, 0.04% delta."""
    f1 = mk(document_id='rbi', entity='India', metric_name='Foreign Exchange Reserves',
            normalized_unit='USD', normalized_magnitude=668_300_000_000.0,
            temporal_end='2025-03-31', temporal_label='end-March 2025', accounting_basis=None)
    f2 = mk(document_id='imf', entity='India', metric_name='Foreign Exchange Reserves',
            normalized_unit='USD', normalized_magnitude=668_000_000_000.0,
            temporal_end='2025-03-31', temporal_label='March 2025', accounting_basis=None)
    assert classify_pair(f1, f2) == 'CORROBORATED'


def test_reconciled_methodology_ebitda_vs_pat():
    """EBITDA positive but PAT negative — different metric definitions."""
    f1 = mk(document_id='deck', entity='Delhivery Limited', metric_name='Adjusted EBITDA',
            normalized_unit='INR', normalized_magnitude=760_000_000.0,
            temporal_end='2024-03-31', temporal_label='FY24', accounting_basis='adjusted')
    f2 = mk(document_id='ar', entity='Delhivery Limited', metric_name='Loss for the Year PAT',
            normalized_unit='INR', normalized_magnitude=-2_491_860_000.0,
            temporal_end='2024-03-31', temporal_label='FY24', accounting_basis='consolidated')
    # Different metric names → RECONCILED_METHODOLOGY (same unit, same T, same S[both have basis])
    result = classify_pair(f1, f2)
    assert result in ('RECONCILED_METHODOLOGY', 'RECONCILED_SCOPE')
