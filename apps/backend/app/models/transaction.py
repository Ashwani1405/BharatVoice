"""
Sprint 1 - Transactions and Ledger Model
"""
import uuid
import sqlalchemy
from app.database import metadata

ledger = sqlalchemy.Table(
    "ledger",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.dialects.postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    sqlalchemy.Column("user_id", sqlalchemy.dialects.postgresql.UUID(as_uuid=True), sqlalchemy.ForeignKey("users.id", ondelete="CASCADE")),
    sqlalchemy.Column("amount", sqlalchemy.Integer, nullable=False), # in paise
    sqlalchemy.Column("type", sqlalchemy.String(20), nullable=False), # 'credit' or 'debit'
    sqlalchemy.Column("description", sqlalchemy.Text),
    sqlalchemy.Column("razorpay_payment_id", sqlalchemy.String(255)),
    sqlalchemy.Column("created_at", sqlalchemy.DateTime(timezone=True), server_default=sqlalchemy.func.now()),
)
