import hashlib
import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Event, Incident, IncidentActivity
from app.schemas.events import EventCreate, Severity

PRIORITY_BY_SEVERITY = {
    Severity.WARNING: "P3",
    Severity.ERROR: "P2",
    Severity.CRITICAL: "P1",
}
SLA_BY_PRIORITY = {
    "P1": timedelta(minutes=15),
    "P2": timedelta(minutes=30),
    "P3": timedelta(hours=4),
}
PRIORITY_RANK = {"P3": 1, "P2": 2, "P1": 3}


def _as_utc(value: datetime) -> datetime:
    """Normalize database-returned and request timestamps for safe comparisons."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _fingerprint(payload: EventCreate) -> str:
    normalized_message = re.sub(r"\s+", " ", payload.message.strip().lower())
    raw = "|".join((payload.service.strip().lower(), payload.event_type.strip().lower(), normalized_message))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def ingest_event(db: Session, payload: EventCreate) -> tuple[Event, Incident | None, bool]:
    now = datetime.now(timezone.utc)
    occurred_at = payload.occurred_at or now
    priority = PRIORITY_BY_SEVERITY.get(payload.severity)
    incident: Incident | None = None
    incident_created = False

    if priority is not None:
        fingerprint = _fingerprint(payload)
        incident = db.scalar(select(Incident).where(Incident.fingerprint == fingerprint))

        if incident is None:
            candidate = Incident(
                fingerprint=fingerprint,
                title=f"{payload.service}: {payload.message[:160]}",
                description=payload.message,
                service=payload.service,
                severity=payload.severity.value,
                priority=priority,
                status="open",
                occurrence_count=1,
                first_seen=occurred_at,
                last_seen=occurred_at,
                sla_due_at=now + SLA_BY_PRIORITY[priority],
                created_at=now,
                updated_at=now,
            )
            # A savepoint lets a concurrent duplicate event lose the unique-key race
            # without aborting the outer event-ingestion transaction.
            try:
                with db.begin_nested():
                    db.add(candidate)
                    db.flush()
                incident = candidate
                incident_created = True
                db.add(
                    IncidentActivity(
                        incident_id=incident.id,
                        action="created",
                        actor="system",
                        message=f"Incident created from {payload.severity.value} event",
                        created_at=now,
                    )
                )
            except IntegrityError:
                incident = db.scalar(select(Incident).where(Incident.fingerprint == fingerprint))

        if incident is not None and not incident_created:
            incident.occurrence_count += 1
            incident.last_seen = max(_as_utc(incident.last_seen), _as_utc(occurred_at))
            incident.updated_at = now
            if PRIORITY_RANK[priority] > PRIORITY_RANK[incident.priority]:
                incident.priority = priority
                incident.severity = payload.severity.value
                incident.sla_due_at = min(_as_utc(incident.sla_due_at), now + SLA_BY_PRIORITY[priority])
                db.add(
                    IncidentActivity(
                        incident_id=incident.id,
                        action="escalated",
                        actor="system",
                        message=f"Priority escalated to {priority} after a {payload.severity.value} event",
                        created_at=now,
                    )
                )
            elif incident.status == "resolved":
                incident.status = "open"
                incident.resolved_at = None
                db.add(
                    IncidentActivity(
                        incident_id=incident.id,
                        action="reopened",
                        actor="system",
                        message="A new matching event reopened this incident",
                        created_at=now,
                    )
                )

    event = Event(
        source=payload.source,
        service=payload.service,
        event_type=payload.event_type,
        severity=payload.severity.value,
        message=payload.message,
        attributes=payload.attributes,
        occurred_at=occurred_at,
        received_at=now,
        incident_id=incident.id if incident else None,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    if incident is not None:
        db.refresh(incident)
    return event, incident, incident_created
