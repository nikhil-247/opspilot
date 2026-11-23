from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Event
from app.schemas.events import EventCreate, EventIngestResponse, EventRead
from app.schemas.incidents import IncidentRead
from app.services.incident_service import ingest_event

router = APIRouter(prefix="/api/v1/events", tags=["events"])


@router.post("", response_model=EventIngestResponse, status_code=201, summary="Ingest an application event")
def create_event(payload: EventCreate, db: Session = Depends(get_db)) -> EventIngestResponse:
    event, incident, created = ingest_event(db, payload)
    return EventIngestResponse(
        event=EventRead.model_validate(event),
        incident=IncidentRead.model_validate(incident) if incident else None,
        incident_created=created,
    )


@router.get("", response_model=list[EventRead], summary="List recent events")
def list_events(
    service: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[Event]:
    query = select(Event).order_by(Event.received_at.desc()).limit(limit)
    if service:
        query = query.where(Event.service == service)
    return list(db.scalars(query).all())
