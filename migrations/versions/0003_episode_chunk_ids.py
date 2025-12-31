"""add chunk_ids to episodes

Revision ID: 0003_episode_chunk_ids
Revises: 0002_episode_transcript_fields
Create Date: 2025-12-29 19:55:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0003_episode_chunk_ids"
down_revision: Union[str, None] = "0002_episode_transcript_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("episodes")}
    if "chunk_ids" in columns:
        return
    op.add_column("episodes", sa.Column("chunk_ids", sa.ARRAY(sa.String())))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("episodes")}
    if "chunk_ids" not in columns:
        return
    op.drop_column("episodes", "chunk_ids")
