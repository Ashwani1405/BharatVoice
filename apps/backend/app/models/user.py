"""
Sprint 1 - User Model
"""
import uuid
import sqlalchemy
from app.database import metadata

users = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.dialects.postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    sqlalchemy.Column("name", sqlalchemy.String(255)),
    sqlalchemy.Column("phone", sqlalchemy.String(20), unique=True, nullable=False),
    sqlalchemy.Column("email", sqlalchemy.String(255), unique=True),
    sqlalchemy.Column("kyc_status", sqlalchemy.String(50), default="unverified"),
    sqlalchemy.Column("risk_score", sqlalchemy.Float, default=0.0),
    sqlalchemy.Column("razorpay_account_id", sqlalchemy.String(255)),
    sqlalchemy.Column("upi_id", sqlalchemy.String(255)),
    sqlalchemy.Column("created_at", sqlalchemy.DateTime(timezone=True), server_default=sqlalchemy.func.now()),
)
