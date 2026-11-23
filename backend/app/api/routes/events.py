from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import UserContext, get_current_context, require_roles
from app.db.session import get_db
from app.models import Event
from app.schemas.events import EventCreate, EventIngestResponse, EventQueuedResponse, EventRead
from app.schemas.incidents import IncidentRead
from app.services.incident_service import ingest_event
from app.workers.tasks import process_event

router = APIRouter(prefix="/api/v1/events", tags=["events"])
WRITERS = ("owner", "admin", "on_call")


@router.post("", response_model=EventIngestResponse, status_code=201, summary="Ingest an event immediately")
def create_event(
    payload: EventCreate,
    context: UserContext = Depends(require_roles(*WRITERS)),
    db: Session = Depends(get_db),
) -> EventIngestResponse:
    event, incident, created = ingest_event(db, payload, context.organization_id)
    return EventIngestResponse(
        event=EventRead.model_validate(event),
        incident=IncidentRead.model_validate(incident) if incident else None,
        incident_created=created,
    )


@router.post("/async", response_model=EventQueuedResponse, status_code=202, summary="Queue an event for background processing")
def queue_event(
    payload: EventCreate,
    context: UserContext = Depends(require_roles(*WRITERS)),
) -> EventQueuedResponse:
    try:
        task = process_event.delay(context.organization_id, payload.model_dump(mode="json"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Event queue is unavailable; retry this request.",
        ) from exc
    return EventQueuedResponse(task_id=task.id, status="queued")


@router.get("", response_model=list[EventRead], summary="List recent events")
def list_events(
    service: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    context: UserContext = Depends(get_current_context),
    db: Session = Depends(get_db),
) -> list[Event]:
    query = (
        select(Event)
        .where(Event.organization_id == context.organization_id)
        .order_by(Event.received_at.desc())
        .limit(limit)
    )
    if service:
        query = query.where(Event.service == service)
    return list(db.scalars(query).all())
