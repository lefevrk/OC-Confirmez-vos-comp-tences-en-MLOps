"""create prediction_events

Revision ID: f9a0166a98f4
Revises:
Create Date: 2026-08-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "f9a0166a98f4"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "prediction_events",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("prediction_id", sa.String(36), nullable=False),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("model_name", sa.String(64), nullable=False),
        sa.Column("model_alias", sa.String(32), nullable=False),
        sa.Column("model_version", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("error_code", sa.String(128), nullable=True),
        sa.Column("probability", sa.Float, nullable=True),
        sa.Column("decision", sa.Integer, nullable=True),
        sa.Column("inference_latency_ms", sa.Float, nullable=True),
        sa.Column("features", JSONB, nullable=False),
    )
    op.create_index("ix_prediction_events_occurred_at", "prediction_events", ["occurred_at"])
    op.create_index("ix_prediction_events_model_version", "prediction_events", ["model_version"])


def downgrade() -> None:
    op.drop_table("prediction_events")
