"""SQLAlchemy schema for this service's own PostgreSQL tables."""

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, Float, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for this service's own tables."""


class PredictionEventRecord(Base):
    """ORM mapping for one row of `prediction_events`.

    Named distinctly from the domain's ``PredictionEvent`` — this is the
    storage shape, not the business object; the adapter translates between
    the two.
    """

    __tablename__ = "prediction_events"
    __table_args__ = (
        Index("ix_prediction_events_occurred_at", "occurred_at"),
        Index("ix_prediction_events_model_version", "model_version"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    prediction_id: Mapped[str] = mapped_column(String(36))
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    model_name: Mapped[str] = mapped_column(String(64))
    model_alias: Mapped[str] = mapped_column(String(32))
    model_version: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16))
    error_code: Mapped[str | None] = mapped_column(String(128))
    probability: Mapped[float | None] = mapped_column(Float)
    decision: Mapped[int | None] = mapped_column(Integer)
    inference_latency_ms: Mapped[float | None] = mapped_column(Float)
    features: Mapped[dict[str, Any]] = mapped_column(JSONB)


metadata = Base.metadata
