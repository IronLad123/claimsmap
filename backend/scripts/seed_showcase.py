"""
Seed pre-computed showcase cases into the database.
Run from backend/: PYTHONPATH=. python scripts/seed_showcase.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select
from app.db import engine, create_db
from app.models.fact import Document, Fact, CrossDocumentLink

create_db()

DOCS = [
    {'filename': '02-delhivery-annual-report-fy24-excerpt.pdf',       'domain': 'delhivery',         'page_count': 100},
    {'filename': '03-delhivery-q4-fy24-earnings-presentation.pdf',    'domain': 'delhivery',         'page_count': 27},
    {'filename': '01-delhivery-prospectus-2022-excerpt.pdf',           'domain': 'delhivery',         'page_count': 100},
    {'filename': '02-rbi-annual-report-2024-25-excerpt.pdf',           'domain': 'india-macroeconomy','page_count': 100},
    {'filename': '03-imf-india-2025-article-iv-excerpt.pdf',           'domain': 'india-macroeconomy','page_count': 95},
]

with Session(engine) as s:
    existing = {d.filename: d for d in s.exec(select(Document)).all()}
    docs = {}
    for d in DOCS:
        if d['filename'] in existing:
            docs[d['filename']] = existing[d['filename']]
        else:
            doc = Document(filename=d['filename'], domain=d['domain'],
                           page_count=d['page_count'], file_hash=d['filename'][:24])
            s.add(doc); s.commit(); s.refresh(doc)
            docs[d['filename']] = doc

    ar   = docs['02-delhivery-annual-report-fy24-excerpt.pdf']
    deck = docs['03-delhivery-q4-fy24-earnings-presentation.pdf']
    pros = docs['01-delhivery-prospectus-2022-excerpt.pdf']
    rbi  = docs['02-rbi-annual-report-2024-25-excerpt.pdf']
    imf  = docs['03-imf-india-2025-article-iv-excerpt.pdf']

    def F(**kw): f = Fact(**kw); s.add(f); s.commit(); s.refresh(f); return f
    def L(**kw): l = CrossDocumentLink(**kw); s.add(l); s.commit(); return l

    # CASE 1A — CORROBORATED: Delhivery FY24 Consolidated Revenue
    fa = F(document_id=ar.id, entity='Delhivery Limited', metric_name='Revenue from Operations',
           raw_value='81,415.38', numeric_value=81415.38, raw_unit='Rs in Million',
           normalized_unit='INR', normalized_magnitude=81415380000.0, data_type='currency',
           temporal_label='FY24', temporal_start='2023-04-01', temporal_end='2024-03-31',
           accounting_basis='consolidated', page_number=22, confidence=0.99,
           verbatim_quote='Consolidated – FY ended March 31, 2024: Revenue from Operations 81,415.38 (Rs in Million)')
    fb = F(document_id=deck.id, entity='Delhivery Limited', metric_name='Revenue from Services',
           raw_value='8,142', numeric_value=8142.0, raw_unit='Rs Crore',
           normalized_unit='INR', normalized_magnitude=81420000000.0, data_type='currency',
           temporal_label='FY24', temporal_start='2023-04-01', temporal_end='2024-03-31',
           accounting_basis='consolidated', page_number=9, confidence=0.99,
           verbatim_quote='Revenue from services (Rs Cr) FY24: 8,142')
    L(source_fact_id=fa.id, target_fact_id=fb.id, relation_type='CORROBORATED', confidence=0.99,
      mathematical_delta=0.000056,
      reconciliation_explanation=(
          'The Annual Report states Consolidated Revenue from Operations as Rs 81,415.38 Million for FY24 (year ended March 31, 2024). '
          'The Earnings Presentation states Revenue from Services as Rs 8,142 Crore for the same period. '
          'Converting: Rs 81,415.38 Million ÷ 10 = Rs 8,141.54 Crore, which rounds to Rs 8,142 Crore — a difference of just 0.006%, '
          'well within the 1.5% corporate rounding tolerance. '
          'Both figures represent the same consolidated entity for the same fiscal year, expressed in different units. '
          'Verdict: CORROBORATED with confidence 0.99.'))

    # CASE 1B — CORROBORATED: India Forex Reserves March 2025
    fc = F(document_id=rbi.id, entity='India', metric_name='Foreign Exchange Reserves',
           raw_value='668.3', numeric_value=668.3, raw_unit='USD Billion',
           normalized_unit='USD', normalized_magnitude=668300000000.0, data_type='currency',
           temporal_label='end-March 2025', temporal_start='2025-03-31', temporal_end='2025-03-31',
           accounting_basis=None, page_number=12, confidence=0.98,
           verbatim_quote='ample forex reserves at US$ 668.3 billion (as at end-March 2025), covering 11 months of merchandise imports')
    fd = F(document_id=imf.id, entity='India', metric_name='Foreign Exchange Reserves',
           raw_value='668', numeric_value=668.0, raw_unit='USD Billion',
           normalized_unit='USD', normalized_magnitude=66800000000.0, data_type='currency',
           temporal_label='March 2025', temporal_start='2025-03-01', temporal_end='2025-03-31',
           accounting_basis=None, page_number=12, confidence=0.98,
           verbatim_quote='foreign exchange (FX) reserves declined to 668 billion in March 2025')
    L(source_fact_id=fc.id, target_fact_id=fd.id, relation_type='CORROBORATED', confidence=0.98,
      mathematical_delta=0.00045,
      reconciliation_explanation=(
          'The RBI Annual Report states India\'s foreign exchange reserves at US$668.3 billion as of end-March 2025. '
          'The IMF Article IV Consultation states reserves at US$668 billion for March 2025. '
          'The US$300 million difference (0.04%) is purely a rounding convention — the RBI reports to one decimal place while the IMF rounds to the nearest billion. '
          'Both figures refer to the same reserve pool held by the Reserve Bank of India as of the same date. '
          'Verdict: CORROBORATED with confidence 0.98.'))

    # CASE 2A — GENUINE_CONTRADICTION: Forex Import Cover
    fe = F(document_id=rbi.id, entity='India', metric_name='Forex Reserves Import Cover',
           raw_value='11', numeric_value=11.0, raw_unit='months',
           normalized_unit='MONTHS', normalized_magnitude=11.0, data_type='count',
           temporal_label='end-March 2025', temporal_start='2025-03-31', temporal_end='2025-03-31',
           accounting_basis=None, page_number=12, confidence=0.95,
           verbatim_quote='ample forex reserves at US$ 668.3 billion (as at end-March 2025), covering 11 months of merchandise imports')
    ff = F(document_id=imf.id, entity='India', metric_name='Forex Reserves Import Cover',
           raw_value='8', numeric_value=8.0, raw_unit='months',
           normalized_unit='MONTHS', normalized_magnitude=8.0, data_type='count',
           temporal_label='October 2025', temporal_start='2025-10-01', temporal_end='2025-10-31',
           accounting_basis=None, page_number=12, confidence=0.90,
           verbatim_quote='FX reserves stood at 668 billion as of October, covering over eight months of prospective imports')
    L(source_fact_id=fe.id, target_fact_id=ff.id, relation_type='GENUINE_CONTRADICTION', confidence=0.90,
      mathematical_delta=0.2727,
      reconciliation_explanation=(
          'The RBI Annual Report states India\'s forex reserves cover 11 months of imports (March 2025). '
          'The IMF Article IV states they cover over 8 months of imports (October 2025). '
          'A policy user asking "how many months of import cover do India\'s forex reserves provide?" receives irreconcilable answers from two authoritative sources. '
          'The root cause is a fundamental definitional incompatibility: the RBI denominator is historical merchandise (goods-only) imports on a trailing annualized basis, '
          'while the IMF denominator is prospective goods AND services imports combined on a forward-looking 12-month basis. '
          'Neither document provides a bridge formula to convert between the two. '
          'Verdict: GENUINE CONTRADICTION — definitional incompatibility in import denominator scope.'))

    # CASE 2B — GENUINE_CONTRADICTION: Delhivery Workforce
    fg = F(document_id=pros.id, entity='Delhivery Limited', metric_name='Total Workforce Headcount Definition',
           raw_value='Excludes daily wage, security guards, Spoton', numeric_value=None, raw_unit='',
           normalized_unit='UNKNOWN', normalized_magnitude=None, data_type='semantic_statement',
           temporal_label='December 2021', temporal_start='2021-12-31', temporal_end='2021-12-31',
           accounting_basis=None, page_number=42, confidence=0.88,
           verbatim_quote='Includes permanent employees and contractual manpower (excluding daily wage manpower and security guards and Spoton) as of the last day of the relevant period.')
    fh = F(document_id=ar.id, entity='Delhivery Limited', metric_name='Total Workforce Headcount',
           raw_value='98,135', numeric_value=98135.0, raw_unit='employees',
           normalized_unit='HEADCOUNT', normalized_magnitude=98135.0, data_type='count',
           temporal_label='FY24', temporal_start='2023-04-01', temporal_end='2024-03-31',
           accounting_basis=None, page_number=2, confidence=0.88,
           verbatim_quote='Workforce strength: 98,135. Includes permanent employees, contractual workers and last mile delivery partner agents.')
    L(source_fact_id=fg.id, target_fact_id=fh.id, relation_type='GENUINE_CONTRADICTION', confidence=0.88,
      mathematical_delta=None,
      reconciliation_explanation=(
          'The 2022 IPO Prospectus defines Delhivery\'s workforce as permanent employees and contractual manpower, '
          'explicitly EXCLUDING daily wage workers, security guards, and Spoton employees. '
          'The FY24 Annual Report reports a workforce of 98,135, explicitly INCLUDING last-mile delivery partner agents. '
          'These two headcount figures represent incompatible population baselines — subtracting them or computing growth rates would be mathematically meaningless. '
          'The metric definition evolved from a narrow IPO disclosure scope to an expanded ecosystem measure. '
          'Verdict: GENUINE CONTRADICTION — incompatible population inclusions make the metrics non-comparable.'))

    # CASE 3A — RECONCILED_SCOPE: Standalone vs Consolidated Revenue
    fi = F(document_id=ar.id, entity='Delhivery Limited', metric_name='Revenue from Operations Standalone',
           raw_value='74,540.82', numeric_value=74540.82, raw_unit='Rs in Million',
           normalized_unit='INR', normalized_magnitude=74540820000.0, data_type='currency',
           temporal_label='FY24', temporal_start='2023-04-01', temporal_end='2024-03-31',
           accounting_basis='standalone', page_number=22, confidence=0.95,
           verbatim_quote='Standalone – FY ended March 31, 2024: Revenue from Operations 74,540.82 (Rs in Million)')
    fj = F(document_id=deck.id, entity='Delhivery Limited', metric_name='Revenue from Operations Consolidated',
           raw_value='81,415.38', numeric_value=81415.38, raw_unit='Rs in Million',
           normalized_unit='INR', normalized_magnitude=81415380000.0, data_type='currency',
           temporal_label='FY24', temporal_start='2023-04-01', temporal_end='2024-03-31',
           accounting_basis='consolidated', page_number=22, confidence=0.95,
           verbatim_quote='Consolidated – FY ended March 31, 2024: Revenue from Operations 81,415.38 (Rs in Million)')
    L(source_fact_id=fi.id, target_fact_id=fj.id, relation_type='RECONCILED_SCOPE', confidence=0.95,
      mathematical_delta=0.0845,
      reconciliation_explanation=(
          'Both figures appear for the same fiscal year (FY24, April 2023–March 2024). '
          'The Standalone figure of Rs 74,540.82 Million represents only the parent legal entity Delhivery Limited. '
          'The Consolidated figure of Rs 81,415.38 Million includes the parent plus all subsidiaries — primarily Spoton Logistics — '
          'adding Rs 6,874.56 Million (~Rs 687 Crore) in subsidiary revenues. '
          'Indian Ind AS accounting standards require companies to publish both standalone and consolidated views. '
          'This is a structural accounting perimeter difference, not a factual conflict. '
          'Verdict: RECONCILED BY SCOPE — standalone parent entity vs consolidated group including subsidiaries.'))

    # CASE 3B — RECONCILED_METHODOLOGY: EBITDA vs Net Loss
    fk = F(document_id=deck.id, entity='Delhivery Limited', metric_name='Adjusted EBITDA',
           raw_value='76', numeric_value=76.0, raw_unit='Rs Crore',
           normalized_unit='INR', normalized_magnitude=760000000.0, data_type='currency',
           temporal_label='FY24', temporal_start='2023-04-01', temporal_end='2024-03-31',
           accounting_basis='adjusted', page_number=4, confidence=0.95,
           verbatim_quote='FY24: EBITDA profitable. Full Year FY24 Adjusted EBITDA: +Rs 76 Cr (Adjusted EBITDA margin: +0.9%)')
    fl = F(document_id=ar.id, entity='Delhivery Limited', metric_name='Loss for the Year PAT',
           raw_value='-2,491.86', numeric_value=-2491.86, raw_unit='Rs in Million',
           normalized_unit='INR', normalized_magnitude=-2491860000.0, data_type='currency',
           temporal_label='FY24', temporal_start='2023-04-01', temporal_end='2024-03-31',
           accounting_basis='consolidated', page_number=22, confidence=0.95,
           verbatim_quote='Consolidated Loss for the year (FY24): Rs -2,491.86 Million, reduced from Rs -10,077.79 Million in FY23.')
    L(source_fact_id=fk.id, target_fact_id=fl.id, relation_type='RECONCILED_METHODOLOGY', confidence=0.92,
      mathematical_delta=None,
      reconciliation_explanation=(
          'The Earnings Deck declares FY24 Adjusted EBITDA of +Rs 76 Crore, headlining "EBITDA profitable". '
          'The Annual Report records a Consolidated Net Loss (PAT) of Rs 2,491.86 Million (-Rs 249.2 Crore). '
          'These are not contradictions — they measure fundamentally different things. '
          'Adjusted EBITDA is an operating cash-flow proxy that excludes Depreciation, Amortisation, Finance Costs, Tax, and Share-Based ESOP charges. '
          'Statutory Net PAT under Ind AS deducts all those non-cash items: over Rs 8,825 Crore of annual depreciation on Delhivery\'s owned vehicle fleet, '
          'warehouse right-of-use assets (Ind AS 116), and amortisation of Spoton customer contracts. '
          'Both metrics are accurate within their respective accounting frameworks. '
          'Verdict: RECONCILED BY METHODOLOGY — Adjusted EBITDA (cash operating profit) vs Statutory Net PAT (Ind AS bottom line).'))

print('Seeded 12 facts and 6 cross-document links into data/facts.db')
print('Run `make demo` to start in demo mode with this pre-seeded data.')
