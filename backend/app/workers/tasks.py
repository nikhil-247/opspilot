from sqlalchemy.exc import SQLAlchemyError

from app.db.session import SessionLocal
from app.schemas.events import EventCreate
from app.services.incident_service import ingest_event
from app.workers.celery_app import celery_app


@celery_app.task(
    bind=True,
    name="opspilot.process_event",
    autoretry_for=(SQLAlchemyError,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def process_event(self, organization_id: str, event_payload: dict) -> dict[str, object]:
    """Persist an event and update its incident from a Celery worker."""
    payload = EventCreate.model_validate(event_payload)
    with SessionLocal() as db:
        event, incident, created = ingest_event(db, payload, organization_id)
        return {
            "event_id": event.id,
            "incident_id": incident.id if incident else None,
            "incident_created": created,
        }
