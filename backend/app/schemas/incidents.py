from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class IncidentStatus(StrEnum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class IncidentPriority(StrEnum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class IncidentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str
    service: str
    severity: str
    priority: IncidentPriority
    status: IncidentStatus
    occurrence_count: int
    first_seen: datetime
    last_seen: datetime
    sla_due_at: datetime
    acknowledged_at: datetime | None
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime


class IncidentList(BaseModel):
    items: list[IncidentRead]
    total: int
    limit: int
    offset: int


class IncidentAction(BaseModel):
    actor: str = Field(default="on-call-engineer", min_length=1, max_length=100)
    note: str | None = Field(default=None, max_length=2000)


class IncidentActivityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    incident_id: str
    action: str
    actor: str
    message: str
    created_at: datetime
