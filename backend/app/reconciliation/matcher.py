import re
from typing import List, Tuple
from rapidfuzz import fuzz
from app.models.fact import Fact
from app.reconciliation.normalizer import get_metric_family, compatible_units


def _norm_entity(e: str) -> str:
    e = e.lower().strip()
    e = re.sub(r'\b(limited|ltd|pvt|private|inc|corp|corporation|the)\b', '', e)
    return re.sub(r'\s+', ' ', e).strip()


def _norm_metric(m: str) -> str:
    m = m.lower().strip()
    m = m.replace('revenue from services', 'revenue from operations')
    m = m.replace('revenue from customers', 'revenue from operations')
    m = m.replace('net loss', 'profit after tax')
    m = m.replace('loss for the year', 'profit after tax')
    return re.sub(r'\s+', ' ', m).strip()


def entity_sim(e1: str, e2: str) -> float:
    return fuzz.token_sort_ratio(_norm_entity(e1), _norm_entity(e2)) / 100.0


def metric_sim(m1: str, m2: str) -> float:
    return fuzz.token_sort_ratio(_norm_metric(m1), _norm_metric(m2)) / 100.0


def find_candidate_pairs(
    facts: List[Fact],
    entity_threshold: float = 0.75,
    metric_threshold: float = 0.58,
) -> List[Tuple[Fact, Fact]]:
    """Find candidate pairs of facts across different documents with explicit compatibility gates."""
    pairs: List[Tuple[Fact, Fact]] = []
    seen: set = set()

    for i, f1 in enumerate(facts):
        for j, f2 in enumerate(facts):
            if i >= j:
                continue
            if f1.document_id == f2.document_id:
                continue

            key = tuple(sorted([f1.id, f2.id]))
            if key in seen:
                continue
            seen.add(key)

            # Gate 1: Entity match
            if entity_sim(f1.entity, f2.entity) < entity_threshold:
                continue

            # Gate 2: Dimension / Unit compatibility check
            if not compatible_units(f1, f2):
                continue

            # Gate 3: Metric similarity or Metric Family match
            fam1 = get_metric_family(f1.metric_name)
            fam2 = get_metric_family(f2.metric_name)
            same_fam = (fam1 == fam2 and len(fam1) > 2)

            ms = metric_sim(f1.metric_name, f2.metric_name)

            # For semantic facts, allow topical overlap in quote or metric
            if f1.data_type == "semantic_statement" and f2.data_type == "semantic_statement":
                quote_overlap = fuzz.token_set_ratio(f1.verbatim_quote, f2.verbatim_quote) / 100.0
                if ms >= 0.50 or same_fam or quote_overlap >= 0.55:
                    pairs.append((f1, f2))
                continue

            if same_fam or ms >= metric_threshold:
                pairs.append((f1, f2))

    return pairs
