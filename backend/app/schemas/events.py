from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.incidents import IncidentRead


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class EventCreate(BaseModel):
    source: str = Field(min_length=1, max_length=100)
    service: str = Field(min_length=1, max_length=100)
    event_type: str = Field(min_length=1, max_length=100)
    severity: Severity
    message: str = Field(min_length=1, max_length=5000)
    occurred_at: datetime | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source: str
    service: str
    event_type: str
    severity: Severity
    message: str
    attributes: dict[str, Any]
    occurred_at: datetime
    received_at: datetime
    incident_id: str | None


class EventIngestResponse(BaseModel):
    event: EventRead
    incident: IncidentRead | None = None
    incident_created: bool = False


class EventQueuedResponse(BaseModel):
    task_id: str
    status: str = "queued"
