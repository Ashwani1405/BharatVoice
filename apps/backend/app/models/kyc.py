"""
Sprint 1 - KYC Models
"""
import uuid
import sqlalchemy
from app.database import metadata

kyc_records = sqlalchemy.Table(
    "kyc_records",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.dialects.postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    sqlalchemy.Column("user_id", sqlalchemy.dialects.postgresql.UUID(as_uuid=True), sqlalchemy.ForeignKey("users.id", ondelete="CASCADE")),
    sqlalchemy.Column("aadhaar_number_hash", sqlalchemy.String(255)),
    sqlalchemy.Column("pan_hash", sqlalchemy.String(255)),
    sqlalchemy.Column("face_match_score", sqlalchemy.Float),
    sqlalchemy.Column("ocr_data", sqlalchemy.dialects.postgresql.JSONB),
    sqlalchemy.Column("status", sqlalchemy.String(50), default="pending"),
    sqlalchemy.Column("verified_at", sqlalchemy.DateTime(timezone=True)),
    sqlalchemy.Column("created_at", sqlalchemy.DateTime(timezone=True), server_default=sqlalchemy.func.now()),
)
