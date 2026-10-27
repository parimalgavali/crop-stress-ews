"""Fields and precomputed predictions.

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import JSONB

revision = "0001"
down_revision = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.create_table(
        "fields",
        sa.Column("field_id", sa.String, primary_key=True),
        sa.Column("year", sa.Integer, primary_key=True),
        sa.Column("district", sa.String, nullable=False),
        sa.Column("area_ha", sa.Float, nullable=False),
        sa.Column("geom", Geometry("GEOMETRY", srid=4326, spatial_index=True), nullable=False),
    )
    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("field_id", sa.String, nullable=False),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("horizon_days", sa.Integer, nullable=False),
        sa.Column("risk", sa.Float, nullable=False),
        sa.Column("level", sa.String(5), nullable=False),
        sa.Column("reasons", JSONB, nullable=False),
        sa.ForeignKeyConstraint(["field_id", "year"], ["fields.field_id", "fields.year"]),
        sa.CheckConstraint("level IN ('green', 'amber', 'red')", name="ck_predictions_level"),
        sa.CheckConstraint("risk >= 0 AND risk <= 1", name="ck_predictions_risk"),
    )
    op.create_index("ix_predictions_field_date", "predictions", ["field_id", "year", "date"])


def downgrade() -> None:
    op.drop_table("predictions")
    op.drop_table("fields")
