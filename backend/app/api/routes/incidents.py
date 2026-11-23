from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Incident, IncidentActivity
from app.schemas.incidents import (
    IncidentAction,
    IncidentActivityRead,
    IncidentList,
    IncidentRead,
)

router = APIRouter(prefix="/api/v1/incidents", tags=["incidents"])


@router.get("", response_model=IncidentList, summary="List incidents")
def list_incidents(
    incident_status: str | None = Query(default=None, alias="status"),
    service: str | None = None,
    priority: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> IncidentList:
    query = select(Incident)
    count_query = select(func.count()).select_from(Incident)
    filters = []
    if incident_status:
        filters.append(Incident.status == incident_status)
    if service:
        filters.append(Incident.service == service)
    if priority:
        filters.append(Incident.priority == priority.upper())
    if filters:
        query = query.where(*filters)
        count_query = count_query.where(*filters)
    incidents = list(
        db.scalars(query.order_by(Incident.last_seen.desc()).offset(offset).limit(limit)).all()
    )
    total = db.scalar(count_query) or 0
    return IncidentList(items=incidents, total=total, limit=limit, offset=offset)


@router.get("/{incident_id}", response_model=IncidentRead, summary="Get an incident")
def get_incident(incident_id: str, db: Session = Depends(get_db)) -> Incident:
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("/{incident_id}/acknowledge", response_model=IncidentRead, summary="Acknowledge an incident")
def acknowledge_incident(
    incident_id: str,
    payload: IncidentAction,
    db: Session = Depends(get_db),
) -> Incident:
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    if incident.status != "open":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot acknowledge an incident with status '{incident.status}'",
        )
    now = datetime.now(timezone.utc)
    incident.status = "acknowledged"
    incident.acknowledged_at = now
    incident.updated_at = now
    db.add(
        IncidentActivity(
            incident_id=incident.id,
            action="acknowledged",
            actor=payload.actor,
            message=payload.note or "Incident acknowledged",
            created_at=now,
        )
    )
    db.commit()
    db.refresh(incident)
    return incident


@router.post("/{incident_id}/resolve", response_model=IncidentRead, summary="Resolve an incident")
def resolve_incident(
    incident_id: str,
    payload: IncidentAction,
    db: Session = Depends(get_db),
) -> Incident:
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    if incident.status == "resolved":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Incident is already resolved",
        )
    now = datetime.now(timezone.utc)
    incident.status = "resolved"
    incident.resolved_at = now
    incident.updated_at = now
    db.add(
        IncidentActivity(
            incident_id=incident.id,
            action="resolved",
            actor=payload.actor,
            message=payload.note or "Incident resolved",
            created_at=now,
        )
    )
    db.commit()
    db.refresh(incident)
    return incident


@router.get("/{incident_id}/activity", response_model=list[IncidentActivityRead], summary="Get incident audit history")
def incident_activity(incident_id: str, db: Session = Depends(get_db)) -> list[IncidentActivity]:
    if db.get(Incident, incident_id) is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    query = (
        select(IncidentActivity)
        .where(IncidentActivity.incident_id == incident_id)
        .order_by(IncidentActivity.created_at.asc())
    )
    return list(db.scalars(query).all())
