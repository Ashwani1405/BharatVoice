"""
Sprint 1 - Fraud Data Models
"""
import uuid
import sqlalchemy
from app.database import metadata

fraud_signals = sqlalchemy.Table(
    "fraud_signals",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.dialects.postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    sqlalchemy.Column("user_id", sqlalchemy.dialects.postgresql.UUID(as_uuid=True), sqlalchemy.ForeignKey("users.id", ondelete="CASCADE")),
    sqlalchemy.Column("signal_type", sqlalchemy.String(100), nullable=False),
    sqlalchemy.Column("signal_value", sqlalchemy.dialects.postgresql.JSONB),
    sqlalchemy.Column("created_at", sqlalchemy.DateTime(timezone=True), server_default=sqlalchemy.func.now()),
)

audit_log = sqlalchemy.Table(
    "audit_log",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.dialects.postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    sqlalchemy.Column("user_id", sqlalchemy.dialects.postgresql.UUID(as_uuid=True), sqlalchemy.ForeignKey("users.id", ondelete="SET NULL")),
    sqlalchemy.Column("action", sqlalchemy.String(255), nullable=False),
    sqlalchemy.Column("metadata", sqlalchemy.dialects.postgresql.JSONB),
    sqlalchemy.Column("created_at", sqlalchemy.DateTime(timezone=True), server_default=sqlalchemy.func.now()),
)
