"""Initial schema: tenants, slots, variations, mab_state, events

Revision ID: 001
Revises: None
Create Date: 2026-02-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- tenants ---
    op.create_table(
        "tenants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("public_key", sa.String(64), unique=True, nullable=False),
        sa.Column("secret_key", sa.String(64), unique=True, nullable=False),
        sa.Column("allowed_origins", ARRAY(sa.Text), nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_tenants_public_key", "tenants", ["public_key"])

    # --- slots ---
    op.create_table(
        "slots",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("slot_key", sa.String(64), nullable=False),
        sa.Column("selector", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # --- variations ---
    op.create_table(
        "variations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("slot_id", UUID(as_uuid=True), sa.ForeignKey("slots.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("vibe_segment", sa.String(64), nullable=False),
        sa.Column("content_json", JSONB, nullable=False),
        sa.Column("is_control", sa.Boolean, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # --- mab_state ---
    op.create_table(
        "mab_state",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "variation_id",
            UUID(as_uuid=True),
            sa.ForeignKey("variations.id"),
            unique=True,
            nullable=False,
        ),
        sa.Column("alpha", sa.Float, server_default="1.0", nullable=False),
        sa.Column("beta", sa.Float, server_default="1.0", nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # --- events ---
    op.create_table(
        "events",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("session_id", sa.String(64), nullable=False),
        sa.Column(
            "variation_id", UUID(as_uuid=True), sa.ForeignKey("variations.id"), nullable=True
        ),
        sa.Column("slot_id", sa.String(64), nullable=True),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("event_name", sa.String(128), nullable=True),
        sa.Column("referrer", sa.Text, nullable=True),
        sa.Column("utm_source", sa.String(128), nullable=True),
        sa.Column("vibe_segment", sa.String(64), nullable=True),
        sa.Column("metadata_json", JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_events_tenant_created", "events", ["tenant_id", "created_at"])
    op.create_index("ix_events_variation_type", "events", ["variation_id", "event_type"])
    op.create_index("ix_events_session", "events", ["session_id"])


def downgrade() -> None:
    op.drop_table("events")
    op.drop_table("mab_state")
    op.drop_table("variations")
    op.drop_table("slots")
    op.drop_table("tenants")
