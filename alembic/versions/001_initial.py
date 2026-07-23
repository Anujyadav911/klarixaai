"""initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-07-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

priority_enum = ENUM("critical", "high", "normal", "low", name="priority_enum", create_type=False)
delivery_status_enum = ENUM("pending", "queued", "processing", "sent", "delivered", "failed", name="delivery_status_enum", create_type=False)
channel_enum = ENUM("email", "sms", "push", name="channel_enum", create_type=False)


def upgrade() -> None:
    priority_enum.create(op.get_bind(), checkfirst=True)
    delivery_status_enum.create(op.get_bind(), checkfirst=True)
    channel_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "templates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(128), unique=True, nullable=False),
        sa.Column("subject", sa.String(512), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "user_preferences",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.String(128), unique=True, nullable=False, index=True),
        sa.Column("email_enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("sms_enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("push_enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "notifications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.String(128), nullable=False, index=True),
        sa.Column("idempotency_key", sa.String(256), unique=True, nullable=True, index=True),
        sa.Column("priority", priority_enum, nullable=False),
        sa.Column("template_id", UUID(as_uuid=True), sa.ForeignKey("templates.id"), nullable=True),
        sa.Column("payload", JSONB, nullable=False),
        sa.Column("status", delivery_status_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_notifications_user_id_created_at", "notifications", ["user_id", "created_at"])

    op.create_table(
        "notification_deliveries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("notification_id", UUID(as_uuid=True), sa.ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("channel", channel_enum, nullable=False),
        sa.Column("status", delivery_status_enum, nullable=False),
        sa.Column("retry_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("provider_response", JSONB, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("notification_deliveries")
    op.drop_table("notifications")
    op.drop_table("user_preferences")
    op.drop_table("templates")
    channel_enum.drop(op.get_bind(), checkfirst=True)
    delivery_status_enum.drop(op.get_bind(), checkfirst=True)
    priority_enum.drop(op.get_bind(), checkfirst=True)
