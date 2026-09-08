from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class DocumentOut(BaseModel):
    id: str
    filename: str
    domain: str
    upload_timestamp: datetime
    page_count: int


class FactOut(BaseModel):
    id: str
    document_id: str
    entity: str
    metric_name: str
    raw_value: str
    numeric_value: Optional[float]
    raw_unit: str
    normalized_unit: str
    normalized_magnitude: Optional[float]
    data_type: str
    temporal_label: str
    temporal_start: Optional[str]
    temporal_end: Optional[str]
    accounting_basis: Optional[str]
    verbatim_quote: str
    page_number: int
    confidence: float


class LinkOut(BaseModel):
    id: str
    source_fact_id: str
    target_fact_id: str
    relation_type: str
    reconciliation_explanation: str
    mathematical_delta: Optional[float]
    confidence: float


class ShowcaseCase(BaseModel):
    case_number: str
    case_type: str
    title: str
    source_a: FactOut
    source_b: FactOut
    link: LinkOut


class ShowcaseResponse(BaseModel):
    cases: List[ShowcaseCase]


class IngestResponse(BaseModel):
    document_id: str
    filename: str
    page_count: int
    fact_count: int
    link_count: int
    demo_mode: bool
