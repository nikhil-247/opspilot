"""Add organizations, memberships and tenant-scoped event data."""
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa

revision = "0002_enterprise_access"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

DEVELOPMENT_ORGANIZATION_ID = "00000000-0000-4000-8000-000000000001"


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"], unique=True)

    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False, unique=True),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.String(length=500), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "memberships",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="viewer"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "organization_id", name="uq_membership_user_organization"),
    )
    op.create_index("ix_memberships_organization_role", "memberships", ["organization_id", "role"])

    now = datetime.now(timezone.utc)
    organizations = sa.table(
        "organizations",
        sa.column("id", sa.String()),
        sa.column("name", sa.String()),
        sa.column("slug", sa.String()),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )
    op.bulk_insert(organizations, [{
        "id": DEVELOPMENT_ORGANIZATION_ID,
        "name": "Legacy Development Workspace",
        "slug": "legacy-development",
        "created_at": now,
    }])

    is_sqlite = op.get_bind().dialect.name == "sqlite"
    for table_name in ("incidents", "events"):
        if is_sqlite:
            # SQLite cannot add a foreign-key constraint with ALTER TABLE ADD COLUMN.
            # The production PostgreSQL migration below creates the FK and NOT NULL constraint.
            op.add_column(
                table_name,
                sa.Column("organization_id", sa.String(length=36), nullable=True),
            )
        else:
            op.add_column(
                table_name,
                sa.Column(
                    "organization_id",
                    sa.String(length=36),
                    sa.ForeignKey("organizations.id", ondelete="CASCADE"),
                    nullable=True,
                ),
            )
        op.execute(
            sa.text(
                f"UPDATE {table_name} SET organization_id = :org_id "
                "WHERE organization_id IS NULL"
            ).bindparams(org_id=DEVELOPMENT_ORGANIZATION_ID)
        )
        if not is_sqlite:
            op.alter_column(
                table_name,
                "organization_id",
                existing_type=sa.String(length=36),
                nullable=False,
            )

    op.create_index(
        "ix_events_organization_received_at", "events", ["organization_id", "received_at"]
    )
    op.create_index(
        "ix_incidents_organization_status", "incidents", ["organization_id", "status"]
    )

    op.create_table(
        "service_dependencies",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_service", sa.String(length=100), nullable=False),
        sa.Column("target_service", sa.String(length=100), nullable=False),
        sa.Column("relationship_type", sa.String(length=50), nullable=False, server_default="depends_on"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "organization_id", "source_service", "target_service",
            name="uq_service_dependency_org_pair",
        ),
    )
    op.create_index(
        "ix_service_dependencies_organization", "service_dependencies", ["organization_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_service_dependencies_organization", table_name="service_dependencies")
    op.drop_table("service_dependencies")
    op.drop_index("ix_incidents_organization_status", table_name="incidents")
    op.drop_index("ix_events_organization_received_at", table_name="events")
    for table_name in ("events", "incidents"):
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.drop_column("organization_id")
    op.drop_index("ix_memberships_organization_role", table_name="memberships")
    op.drop_table("memberships")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.drop_index("ix_organizations_slug", table_name="organizations")
    op.drop_table("organizations")
