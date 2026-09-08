from typing import Optional, List, Tuple
from sqlmodel import Session, select

from app.models.fact import Fact, CrossDocumentLink, Document
from app.reconciliation.normalizer import (
    temporal_overlap, value_delta, compatible_units, same_scope,
    detect_methodology_difference, get_metric_family
)
from app.reconciliation.matcher import find_candidate_pairs, metric_sim
from app.extraction.gemini import generate_explanation

RATIONALES = {
    'CORROBORATED': (
        'Both facts report the same metric for the same entity, same time period, and same '
        'accounting scope. Their numerical values agree within a 1.5% tolerance after unit '
        'normalization, confirming they describe the same underlying reality.'
    ),
    'RECONCILED_TEMPORAL': (
        'The facts cover different time periods. The numerical difference reflects longitudinal '
        'progression over time — not a factual conflict between sources.'
    ),
    'RECONCILED_SCOPE': (
        'The facts cover the same time period but differ in accounting perimeter '
        '(e.g. standalone parent entity vs consolidated group including subsidiaries). '
        'The difference is structurally expected under dual reporting requirements.'
    ),
    'RECONCILED_METHODOLOGY': (
        'The facts use different measurement methodologies or metric definitions for the same '
        'underlying concept (e.g. trailing merchandise vs prospective imports, or cash EBITDA vs statutory PAT). '
        'Both are accurate within their respective frameworks.'
    ),
    'GENUINE_CONTRADICTION': (
        'The facts assert different values for the same metric, same entity, same time period, '
        'and same accounting scope, with no documented methodological or perimeter explanation '
        'for the divergence. This is a direct factual conflict between sources.'
    ),
}


def classify_pair(f1: Fact, f2: Fact) -> Optional[str]:
    """Classify a fact pair across semantic and numerical dimensions."""
    if not compatible_units(f1, f2):
        return None

    # Path 1: Semantic statements (workforce definitions, executive roles, governance)
    if f1.data_type == "semantic_statement" and f2.data_type == "semantic_statement":
        same_T = temporal_overlap(f1, f2)
        if not same_T:
            return "RECONCILED_TEMPORAL"
        if not same_scope(f1, f2):
            return "RECONCILED_SCOPE"
        # If verbatim definitions diverge significantly despite same context, genuine contradiction
        from rapidfuzz import fuzz
        text_sim = fuzz.token_sort_ratio(f1.verbatim_quote, f2.verbatim_quote) / 100.0
        if text_sim < 0.70:
            return "GENUINE_CONTRADICTION"
        return "CORROBORATED"

    # Path 2: Numerical facts
    delta = value_delta(f1, f2)
    same_T = temporal_overlap(f1, f2)
    same_S = same_scope(f1, f2)
    method_diff = detect_methodology_difference(f1, f2)

    # Step 1: Corroborated within 1.5% tolerance
    if delta is not None and delta <= 0.015 and same_T and same_S and not method_diff:
        return 'CORROBORATED'

    # Step 2: Methodology divergence (e.g. EBITDA vs PAT, or merchandise vs prospective import cover)
    if method_diff:
        return 'RECONCILED_METHODOLOGY'

    # Step 3: Different time periods
    if not same_T:
        return 'RECONCILED_TEMPORAL'

    # Step 4: Accounting perimeter / scope difference (Standalone vs Consolidated)
    if same_T and not same_S:
        return 'RECONCILED_SCOPE'

    # Step 5: Metric name divergence within same family
    m_sim = metric_sim(f1.metric_name, f2.metric_name)
    if same_T and same_S and m_sim < 0.85:
        return 'RECONCILED_METHODOLOGY'

    # Step 6: Genuine contradiction if delta > 5% and no context differences
    if delta is not None and delta > 0.05:
        return 'GENUINE_CONTRADICTION'

    return None


def run_reconciliation(all_facts: List[Fact], session: Session) -> List[CrossDocumentLink]:
    pairs = find_candidate_pairs(all_facts)
    links: List[CrossDocumentLink] = []
    doc_names: dict = {}

    for f1, f2 in pairs:
        relation_type = classify_pair(f1, f2)
        if not relation_type:
            continue

        existing = session.exec(
            select(CrossDocumentLink).where(
                CrossDocumentLink.source_fact_id == f1.id,
                CrossDocumentLink.target_fact_id == f2.id,
            )
        ).first()
        if existing:
            continue

        for did in (f1.document_id, f2.document_id):
            if did not in doc_names:
                doc = session.get(Document, did)
                doc_names[did] = doc.filename if doc else did

        rationale = RATIONALES.get(relation_type, '')
        delta = value_delta(f1, f2)

        explanation = generate_explanation(
            relation_type=relation_type,
            doc_a=doc_names.get(f1.document_id, f1.document_id),
            page_a=f1.page_number,
            quote_a=f1.verbatim_quote,
            doc_b=doc_names.get(f2.document_id, f2.document_id),
            page_b=f2.page_number,
            quote_b=f2.verbatim_quote,
            rationale=rationale,
        )

        link = CrossDocumentLink(
            source_fact_id=f1.id,
            target_fact_id=f2.id,
            relation_type=relation_type,
            reconciliation_explanation=explanation,
            mathematical_delta=delta,
            confidence=0.99 if relation_type == 'CORROBORATED' else 0.88,
        )
        session.add(link)
        links.append(link)

    session.commit()
    return links
