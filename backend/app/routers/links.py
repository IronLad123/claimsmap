from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select
from typing import List, Optional
from app.db import get_session
from app.models.fact import CrossDocumentLink
from app.models.schemas import LinkOut

router = APIRouter(prefix='/api', tags=['links'])


@router.get('/links', response_model=List[LinkOut])
def list_links(
    relation_type: Optional[str] = None,
    limit: int = Query(default=200, le=1000),
    session: Session = Depends(get_session),
):
    stmt = select(CrossDocumentLink)
    if relation_type:
        stmt = stmt.where(CrossDocumentLink.relation_type == relation_type)
    return session.exec(stmt.limit(limit)).all()
