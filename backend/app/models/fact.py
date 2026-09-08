from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
import uuid


class Document(SQLModel, table=True):
    __tablename__ = "documents"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    filename: str
    domain: str = "custom"
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)
    page_count: int = 0
    file_hash: str = ""


class Fact(SQLModel, table=True):
    __tablename__ = "facts"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    document_id: str = Field(foreign_key="documents.id")
    entity: str
    metric_name: str
    raw_value: str
    numeric_value: Optional[float] = None
    raw_unit: str = ""
    normalized_unit: str = ""
    normalized_magnitude: Optional[float] = None
    data_type: str = "semantic_statement"
    temporal_start: Optional[str] = None
    temporal_end: Optional[str] = None
    temporal_label: str = ""
    accounting_basis: Optional[str] = None
    verbatim_quote: str
    page_number: int = 0
    confidence: float = 0.8
    chunk_index: int = 0
    file_hash: str = Field(default="")
    chunk_hash: str = Field(default="")
    extractor_model: str = Field(default="gemini-1.5-pro")
    prompt_version: str = Field(default="v2.1")
    grounding_verified: bool = Field(default=True)


class CrossDocumentLink(SQLModel, table=True):
    __tablename__ = "cross_document_links"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    source_fact_id: str = Field(foreign_key="facts.id")
    target_fact_id: str = Field(foreign_key="facts.id")
    relation_type: str
    reconciliation_explanation: str
    mathematical_delta: Optional[float] = None
    confidence: float = 0.8


class ChunkCache(SQLModel, table=True):
    __tablename__ = "chunk_cache"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    document_id: str
    chunk_hash: str
    extracted_json: str


class IngestionJob(SQLModel, table=True):
    __tablename__ = "ingestion_jobs"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    document_id: Optional[str] = None
    filename: str
    status: str = "queued"  # queued, parsing, extracting, reconciling, completed, failed
    stage: str = "queued"
    progress: float = 0.0
    message: str = "Job created"
    fact_count: int = 0
    link_count: int = 0
    error_detail: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

