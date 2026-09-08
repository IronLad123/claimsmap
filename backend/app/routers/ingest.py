import hashlib
import os
import re
import tempfile
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlmodel import Session, select

from app.db import engine, get_session
from app.models.fact import Document, Fact, CrossDocumentLink, IngestionJob
from app.models.schemas import IngestResponse, IngestionJobOut
from app.ingestion.parser import extract_document, get_page_count
from app.extraction.extractor import process_chunks
from app.reconciliation.engine import run_reconciliation
from app.config import DEMO_MODE, MAX_UPLOAD_SIZE_BYTES, MAX_PAGE_COUNT

logger = logging.getLogger("fact_layer.ingest")
router = APIRouter(prefix='/api', tags=['ingest'])


def _sanitize_filename(filename: str) -> str:
    base = Path(filename or "document.pdf").name
    return re.sub(r'[^a-zA-Z0-9_.-]', '_', base)[:120]


def process_ingestion_background(
    job_id: str,
    tmp_path_str: str,
    safe_filename: str,
    file_hash: str,
):
    """Background ingestion worker updating IngestionJob state transitions."""
    tmp_path = Path(tmp_path_str)
    with Session(engine) as session:
        job = session.get(IngestionJob, job_id)
        if not job:
            logger.error("Job %s not found in background worker", job_id)
            if tmp_path.exists():
                os.unlink(tmp_path)
            return

        try:
            # 1. Page count & Document registration
            page_count = get_page_count(tmp_path)
            if page_count > MAX_PAGE_COUNT:
                raise ValueError(f"Document exceeds maximum page limit of {MAX_PAGE_COUNT} (got {page_count} pages)")

            doc = session.exec(select(Document).where(Document.file_hash == file_hash)).first()
            if not doc:
                doc = Document(filename=safe_filename, page_count=page_count, file_hash=file_hash)
                session.add(doc)
                session.commit()
                session.refresh(doc)

            job.document_id = doc.id
            job.status = "parsing"
            job.stage = "parsing"
            job.progress = 0.25
            job.message = f"Parsing {page_count} pages and extracting structured tables..."
            job.updated_at = datetime.utcnow()
            session.add(job)
            session.commit()

            # 2. Extract chunks
            chunks = extract_document(tmp_path, doc.id)
            if not chunks:
                raise ValueError("Could not extract any readable text or tables from this PDF.")

            # 3. Extract facts
            job.status = "extracting"
            job.stage = "extracting"
            job.progress = 0.55
            mode_desc = "deterministic rule engine (demo mode)" if DEMO_MODE else "Gemini 1.5 Pro"
            job.message = f"Extracting and grounding facts using {mode_desc}..."
            job.updated_at = datetime.utcnow()
            session.add(job)
            session.commit()

            new_facts = process_chunks(
                chunks=chunks,
                document_id=doc.id,
                session=session,
                file_hash=file_hash,
                allow_fallback=True,
            )

            # 4. Reconcile across all facts in database
            job.status = "reconciling"
            job.stage = "reconciling"
            job.progress = 0.85
            job.message = "Running cross-document comparability gates and reconciliation..."
            job.updated_at = datetime.utcnow()
            session.add(job)
            session.commit()

            all_facts = list(session.exec(select(Fact)).all())
            new_links = run_reconciliation(all_facts, session)

            # 5. Completed
            job.status = "completed"
            job.stage = "completed"
            job.progress = 1.0
            job.fact_count = len(new_facts)
            job.link_count = len(new_links)
            job.message = f"Successfully extracted {len(new_facts)} facts and identified {len(new_links)} cross-document links."
            job.updated_at = datetime.utcnow()
            session.add(job)
            session.commit()
            logger.info("Ingestion job %s completed successfully", job_id)

        except Exception as e:
            logger.exception("Ingestion job %s failed: %s", job_id, e)
            job.status = "failed"
            job.stage = "failed"
            job.progress = 1.0
            job.error_detail = str(e)
            job.message = f"Extraction failed: {str(e)}"
            job.updated_at = datetime.utcnow()
            session.add(job)
            session.commit()

        finally:
            if tmp_path.exists():
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass


@router.post('/ingest', response_model=IngestResponse)
async def ingest_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    safe_filename = _sanitize_filename(file.filename or "")

    # Security check 1: extension
    if not safe_filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail='Only PDF files (.pdf) are accepted.')

    # Read contents with size guard
    contents = await file.read()

    # Security check 2: max upload size
    if len(contents) > MAX_UPLOAD_SIZE_BYTES:
        max_mb = MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
        raise HTTPException(status_code=413, detail=f"File exceeds maximum allowed size of {max_mb} MB.")

    # Security check 3: PDF magic bytes validation (%PDF-)
    if not contents.startswith(b'%PDF-'):
        raise HTTPException(status_code=400, detail='Invalid file format: Missing PDF magic header (%PDF-).')

    file_hash = hashlib.sha256(contents).hexdigest()[:24]

    # Idempotency check: if document already exists with facts, return immediately
    existing_doc = session.exec(select(Document).where(Document.file_hash == file_hash)).first()
    if existing_doc:
        doc_facts = session.exec(select(Fact).where(Fact.document_id == existing_doc.id)).all()
        if doc_facts:
            all_links = session.exec(select(CrossDocumentLink)).all()
            doc_fact_ids = {f.id for f in doc_facts}
            link_count = sum(1 for lnk in all_links if lnk.source_fact_id in doc_fact_ids or lnk.target_fact_id in doc_fact_ids)

            # Create an already-completed job record for status tracking
            job = IngestionJob(
                document_id=existing_doc.id,
                filename=existing_doc.filename,
                status="completed",
                stage="completed",
                progress=1.0,
                message="Document was previously ingested.",
                fact_count=len(doc_facts),
                link_count=link_count,
            )
            session.add(job)
            session.commit()
            session.refresh(job)

            return IngestResponse(
                job_id=job.id,
                document_id=existing_doc.id,
                filename=existing_doc.filename,
                status="completed",
                page_count=existing_doc.page_count,
                fact_count=len(doc_facts),
                link_count=link_count,
                demo_mode=DEMO_MODE,
            )

    # Save to secure temporary file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        tmp.write(contents)
        tmp_path = Path(tmp.name)

    # Create IngestionJob record
    job = IngestionJob(
        filename=safe_filename,
        status="queued",
        stage="queued",
        progress=0.05,
        message="Upload received, queued for processing...",
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    # Dispatch to background task
    background_tasks.add_task(
        process_ingestion_background,
        job.id,
        str(tmp_path),
        safe_filename,
        file_hash,
    )

    return IngestResponse(
        job_id=job.id,
        document_id=None,
        filename=safe_filename,
        status="queued",
        page_count=0,
        fact_count=0,
        link_count=0,
        demo_mode=DEMO_MODE,
    )


@router.get('/ingest/{job_id}', response_model=IngestionJobOut)
def get_ingest_job(
    job_id: str,
    session: Session = Depends(get_session),
):
    """Poll ingestion status by job_id."""
    job = session.get(IngestionJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Ingestion job not found.")

    return IngestionJobOut(
        job_id=job.id,
        document_id=job.document_id,
        filename=job.filename,
        status=job.status,
        stage=job.stage,
        progress=job.progress,
        message=job.message,
        fact_count=job.fact_count,
        link_count=job.link_count,
        error_detail=job.error_detail,
        demo_mode=DEMO_MODE,
    )
