"""episode transcript fields

Revision ID: 0002_episode_transcript_fields
Revises: 0001_initial
Create Date: 2025-12-29 18:10:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0002_episode_transcript_fields"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("episodes", sa.Column("transcript_text", sa.Text()))
    op.add_column("episodes", sa.Column("transcript_segments", sa.JSON()))


def downgrade() -> None:
    op.drop_column("episodes", "transcript_segments")
    op.drop_column("episodes", "transcript_text")
