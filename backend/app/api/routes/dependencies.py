from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import UserContext, get_current_context, require_roles
from app.db.session import get_db
from app.models import ServiceDependency

router = APIRouter(prefix="/api/v1/services", tags=["service topology"])


class DependencyCreate(BaseModel):
    source_service: str = Field(min_length=1, max_length=100)
    target_service: str = Field(min_length=1, max_length=100)
    relationship_type: str = Field(default="depends_on", max_length=50)


class DependencyRead(DependencyCreate):
    id: str
    created_at: datetime


@router.get("/dependencies", response_model=list[DependencyRead])
def list_dependencies(
    context: UserContext = Depends(get_current_context),
    db: Session = Depends(get_db),
) -> list[ServiceDependency]:
    query = (
        select(ServiceDependency)
        .where(ServiceDependency.organization_id == context.organization_id)
        .order_by(ServiceDependency.source_service, ServiceDependency.target_service)
    )
    return list(db.scalars(query).all())


@router.post("/dependencies", response_model=DependencyRead, status_code=201)
def create_dependency(
    payload: DependencyCreate,
    context: UserContext = Depends(require_roles("owner", "admin", "on_call")),
    db: Session = Depends(get_db),
) -> ServiceDependency:
    if payload.source_service == payload.target_service:
        raise HTTPException(status_code=422, detail="A service cannot depend on itself")
    item = ServiceDependency(
        organization_id=context.organization_id,
        source_service=payload.source_service.strip(),
        target_service=payload.target_service.strip(),
        relationship_type=payload.relationship_type,
        created_at=datetime.now(timezone.utc),
    )
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="This service dependency already exists") from None
    db.refresh(item)
    return item
