"""add_ai_provider_default_model

Revision ID: 120a843d4a48
Revises: 807b210b9de7
Create Date: 2026-09-03 19:26:17.260306

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '120a843d4a48'
down_revision: Union[str, None] = '807b210b9de7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns — SQLite supports ADD COLUMN only
    op.add_column('ai_providers', sa.Column('default_model', sa.String(length=200), nullable=True))

    # Add summary_data column to social_profile_summaries if it doesn't exist
    try:
        op.add_column('social_profile_summaries', sa.Column('summary_data', sa.JSON(), nullable=True))
    except Exception:
        pass  # Column may already exist

    # SQLite does not support ALTER COLUMN / type changes — skip all alter_column ops
    # The workflow_executions, workflow_nodes, and workflows schema changes are
    # SQLite-incompatible and will be applied during a PostgreSQL migration.


def downgrade() -> None:
    op.drop_column('ai_providers', 'default_model')
    try:
        op.drop_column('social_profile_summaries', 'summary_data')
    except Exception:
        pass
