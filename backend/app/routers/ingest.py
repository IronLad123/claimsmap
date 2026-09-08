import hashlib
import os
import tempfile
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlmodel import Session, select
from app.db import get_session
from app.models.fact import Document, Fact, CrossDocumentLink
from app.models.schemas import IngestResponse
from app.ingestion.parser import extract_document, get_page_count
from app.extraction.extractor import process_chunks
from app.reconciliation.engine import run_reconciliation
from app.config import DEMO_MODE

router = APIRouter(prefix='/api', tags=['ingest'])


@router.post('/ingest', response_model=IngestResponse)
async def ingest_pdf(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail='Only PDF files are accepted.')

    contents = await file.read()
    file_hash = hashlib.sha256(contents).hexdigest()[:24]

    existing = session.exec(
        select(Document).where(Document.file_hash == file_hash)
    ).first()
    if existing:
        fact_count = session.exec(
            select(Fact).where(Fact.document_id == existing.id)
        ).all()
        all_links = session.exec(select(CrossDocumentLink)).all()
        doc_fact_ids = {f.id for f in fact_count}
        link_count = sum(
            1 for lnk in all_links
            if lnk.source_fact_id in doc_fact_ids or lnk.target_fact_id in doc_fact_ids
        )
        return IngestResponse(
            document_id=existing.id, filename=existing.filename,
            page_count=existing.page_count, fact_count=len(fact_count),
            link_count=link_count, demo_mode=DEMO_MODE,
        )

    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        tmp.write(contents)
        tmp_path = Path(tmp.name)

    try:
        page_count = get_page_count(tmp_path)
        doc = Document(filename=file.filename, page_count=page_count, file_hash=file_hash)
        session.add(doc)
        session.commit()
        session.refresh(doc)

        if not DEMO_MODE:
            chunks = extract_document(tmp_path, doc.id)
            new_facts = process_chunks(chunks, doc.id, session)
            all_facts = list(session.exec(select(Fact)).all())
            new_links = run_reconciliation(all_facts, session)
        else:
            new_facts, new_links = [], []

        facts_for_doc = session.exec(
            select(Fact).where(Fact.document_id == doc.id)
        ).all()
        return IngestResponse(
            document_id=doc.id, filename=doc.filename, page_count=page_count,
            fact_count=len(facts_for_doc), link_count=len(new_links),
            demo_mode=DEMO_MODE,
        )
    finally:
        os.unlink(tmp_path)
