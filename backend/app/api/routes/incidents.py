from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import UserContext, get_current_context, require_roles
from app.db.session import get_db
from app.models import Incident, IncidentActivity
from app.schemas.incidents import IncidentAction, IncidentActivityRead, IncidentList, IncidentRead
from app.services.analysis_service import analyze_incident

router = APIRouter(prefix="/api/v1/incidents", tags=["incidents"])
WRITERS = ("owner", "admin", "on_call")


@router.get("", response_model=IncidentList, summary="List incidents")
def list_incidents(
    incident_status: str | None = Query(default=None, alias="status"),
    service: str | None = None,
    priority: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    context: UserContext = Depends(get_current_context),
    db: Session = Depends(get_db),
) -> IncidentList:
    filters = [Incident.organization_id == context.organization_id]
    if incident_status:
        filters.append(Incident.status == incident_status)
    if service:
        filters.append(Incident.service == service)
    if priority:
        filters.append(Incident.priority == priority.upper())
    query = select(Incident).where(*filters)
    count_query = select(func.count()).select_from(Incident).where(*filters)
    incidents = list(
        db.scalars(query.order_by(Incident.last_seen.desc()).offset(offset).limit(limit)).all()
    )
    total = db.scalar(count_query) or 0
    return IncidentList(items=incidents, total=total, limit=limit, offset=offset)


@router.get("/{incident_id}", response_model=IncidentRead, summary="Get an incident")
def get_incident(
    incident_id: str,
    context: UserContext = Depends(get_current_context),
    db: Session = Depends(get_db),
) -> Incident:
    incident = db.scalar(
        select(Incident).where(
            Incident.id == incident_id,
            Incident.organization_id == context.organization_id,
        )
    )
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("/{incident_id}/acknowledge", response_model=IncidentRead, summary="Acknowledge an incident")
def acknowledge_incident(
    incident_id: str,
    payload: IncidentAction,
    context: UserContext = Depends(require_roles(*WRITERS)),
    db: Session = Depends(get_db),
) -> Incident:
    incident = _get_incident(db, incident_id, context.organization_id)
    if incident.status != "open":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Cannot acknowledge an incident with status '{incident.status}'")
    now = datetime.now(timezone.utc)
    incident.status = "acknowledged"
    incident.acknowledged_at = now
    incident.updated_at = now
    db.add(IncidentActivity(
        incident_id=incident.id, action="acknowledged", actor=context.email,
        message=payload.note or "Incident acknowledged", created_at=now,
    ))
    db.commit()
    db.refresh(incident)
    return incident


@router.post("/{incident_id}/resolve", response_model=IncidentRead, summary="Resolve an incident")
def resolve_incident(
    incident_id: str,
    payload: IncidentAction,
    context: UserContext = Depends(require_roles(*WRITERS)),
    db: Session = Depends(get_db),
) -> Incident:
    incident = _get_incident(db, incident_id, context.organization_id)
    if incident.status == "resolved":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Incident is already resolved")
    now = datetime.now(timezone.utc)
    incident.status = "resolved"
    incident.resolved_at = now
    incident.updated_at = now
    db.add(IncidentActivity(
        incident_id=incident.id, action="resolved", actor=context.email,
        message=payload.note or "Incident resolved", created_at=now,
    ))
    db.commit()
    db.refresh(incident)
    return incident


@router.get("/{incident_id}/activity", response_model=list[IncidentActivityRead], summary="Get incident audit history")
def incident_activity(
    incident_id: str,
    context: UserContext = Depends(get_current_context),
    db: Session = Depends(get_db),
) -> list[IncidentActivity]:
    _get_incident(db, incident_id, context.organization_id)
    query = (
        select(IncidentActivity)
        .where(IncidentActivity.incident_id == incident_id)
        .order_by(IncidentActivity.created_at.asc())
    )
    return list(db.scalars(query).all())


@router.get("/{incident_id}/analysis", summary="Generate evidence-based incident hypotheses")
def incident_analysis(
    incident_id: str,
    context: UserContext = Depends(get_current_context),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    incident = _get_incident(db, incident_id, context.organization_id)
    return analyze_incident(db, incident)


def _get_incident(db: Session, incident_id: str, organization_id: str) -> Incident:
    incident = db.scalar(
        select(Incident).where(
            Incident.id == incident_id,
            Incident.organization_id == organization_id,
        )
    )
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident
