"""Create initial OpsPilot event and incident tables."""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "incidents",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("fingerprint", sa.String(length=64), nullable=False, unique=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("service", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("priority", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("occurrence_count", sa.Integer(), nullable=False),
        sa.Column("first_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sla_due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_incidents_status_priority", "incidents", ["status", "priority"])
    op.create_index("ix_incidents_service_last_seen", "incidents", ["service", "last_seen"])

    op.create_table(
        "events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("service", sa.String(length=100), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("attributes", sa.JSON(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("incident_id", sa.String(length=36), sa.ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_events_service_received_at", "events", ["service", "received_at"])
    op.create_index("ix_events_incident_id", "events", ["incident_id"])

    op.create_table(
        "incident_activities",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("incident_id", sa.String(length=36), sa.ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("actor", sa.String(length=100), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_incident_activities_incident_created", "incident_activities", ["incident_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_incident_activities_incident_created", table_name="incident_activities")
    op.drop_table("incident_activities")
    op.drop_index("ix_events_incident_id", table_name="events")
    op.drop_index("ix_events_service_received_at", table_name="events")
    op.drop_table("events")
    op.drop_index("ix_incidents_service_last_seen", table_name="incidents")
    op.drop_index("ix_incidents_status_priority", table_name="incidents")
    op.drop_table("incidents")
