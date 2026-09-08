from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select
from typing import List, Optional
from app.db import get_session
from app.models.fact import Fact
from app.models.schemas import FactOut

router = APIRouter(prefix='/api', tags=['facts'])


@router.get('/facts', response_model=List[FactOut])
def list_facts(
    document_id: Optional[str] = None,
    entity: Optional[str] = None,
    metric: Optional[str] = None,
    data_type: Optional[str] = None,
    limit: int = Query(default=200, le=1000),
    session: Session = Depends(get_session),
):
    stmt = select(Fact)
    if document_id:
        stmt = stmt.where(Fact.document_id == document_id)
    if entity:
        stmt = stmt.where(Fact.entity.ilike(f'%{entity}%'))
    if metric:
        stmt = stmt.where(Fact.metric_name.ilike(f'%{metric}%'))
    if data_type:
        stmt = stmt.where(Fact.data_type == data_type)
    return session.exec(stmt.limit(limit)).all()
