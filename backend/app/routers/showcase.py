from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from typing import List
from app.db import get_session
from app.models.fact import Fact, CrossDocumentLink
from app.models.schemas import ShowcaseResponse, ShowcaseCase, FactOut, LinkOut

router = APIRouter(prefix='/api', tags=['showcase'])

TYPE_MAP = {
    'CORROBORATED':           ('1',  'Corroborated Fact — expressed differently'),
    'GENUINE_CONTRADICTION':  ('2',  'Genuine Contradiction'),
    'RECONCILED_SCOPE':       ('3A', 'Apparent Contradiction — Reconciled by Scope'),
    'RECONCILED_TEMPORAL':    ('3B', 'Apparent Contradiction — Reconciled by Time'),
    'RECONCILED_METHODOLOGY': ('3C', 'Apparent Contradiction — Reconciled by Methodology'),
}


def _f(f: Fact) -> FactOut:
    return FactOut(
        id=f.id, document_id=f.document_id, entity=f.entity,
        metric_name=f.metric_name, raw_value=f.raw_value,
        numeric_value=f.numeric_value, raw_unit=f.raw_unit,
        normalized_unit=f.normalized_unit, normalized_magnitude=f.normalized_magnitude,
        data_type=f.data_type, temporal_label=f.temporal_label,
        temporal_start=f.temporal_start, temporal_end=f.temporal_end,
        accounting_basis=f.accounting_basis, verbatim_quote=f.verbatim_quote,
        page_number=f.page_number, confidence=f.confidence,
    )


def _l(l: CrossDocumentLink) -> LinkOut:
    return LinkOut(
        id=l.id, source_fact_id=l.source_fact_id, target_fact_id=l.target_fact_id,
        relation_type=l.relation_type, reconciliation_explanation=l.reconciliation_explanation,
        mathematical_delta=l.mathematical_delta, confidence=l.confidence,
    )


@router.get('/showcase', response_model=ShowcaseResponse)
def get_showcase(session: Session = Depends(get_session)):
    links = session.exec(
        select(CrossDocumentLink).order_by(CrossDocumentLink.confidence.desc())
    ).all()

    cases: List[ShowcaseCase] = []
    seen: set = set()

    for link in links:
        rt = link.relation_type
        if rt not in TYPE_MAP or rt in seen:
            continue
        f1 = session.get(Fact, link.source_fact_id)
        f2 = session.get(Fact, link.target_fact_id)
        if not f1 or not f2:
            continue
        case_num, case_type = TYPE_MAP[rt]
        cases.append(ShowcaseCase(
            case_number=case_num,
            case_type=case_type,
            title=f'{f1.entity} — {f1.metric_name}',
            source_a=_f(f1),
            source_b=_f(f2),
            link=_l(link),
        ))
        seen.add(rt)
        if len(cases) >= 5:
            break

    return ShowcaseResponse(cases=cases)
