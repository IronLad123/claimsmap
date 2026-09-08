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
    grounding_verified: bool = True
    chunk_hash: str = ""
    extractor_model: str = "gemini-1.5-pro"


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
    job_id: Optional[str] = None
    document_id: Optional[str] = None
    filename: str
    status: str = "completed"
    page_count: int = 0
    fact_count: int = 0
    link_count: int = 0
    demo_mode: bool = False


class IngestionJobOut(BaseModel):
    job_id: str
    document_id: Optional[str] = None
    filename: str
    status: str
    stage: str
    progress: float
    message: str
    fact_count: int = 0
    link_count: int = 0
    error_detail: Optional[str] = None
    demo_mode: bool = False

