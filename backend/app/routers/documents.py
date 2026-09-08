from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from typing import List
from app.db import get_session
from app.models.fact import Document
from app.models.schemas import DocumentOut

router = APIRouter(prefix='/api', tags=['documents'])


@router.get('/documents', response_model=List[DocumentOut])
def list_documents(session: Session = Depends(get_session)):
    return session.exec(select(Document).order_by(Document.upload_timestamp.desc())).all()
