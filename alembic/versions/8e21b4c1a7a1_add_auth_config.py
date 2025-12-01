"""add auth config

Revision ID: 8e21b4c1a7a1
Revises: 3d0a2a346b3c
Create Date: 2025-11-03 00:00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = "8e21b4c1a7a1"
down_revision: Union[str, Sequence[str], None] = "3d0a2a346b3c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "authconfigmodel",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("api_key", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_authconfigmodel_source"), "authconfigmodel", ["source"], unique=False
    )
    op.create_index(
        op.f("ix_authconfigmodel_api_key"), "authconfigmodel", ["api_key"], unique=True
    )
    op.create_index(
        op.f("ix_authconfigmodel_is_active"),
        "authconfigmodel",
        ["is_active"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_authconfigmodel_is_active"), table_name="authconfigmodel")
    op.drop_index(op.f("ix_authconfigmodel_api_key"), table_name="authconfigmodel")
    op.drop_index(op.f("ix_authconfigmodel_source"), table_name="authconfigmodel")
    op.drop_table("authconfigmodel")
