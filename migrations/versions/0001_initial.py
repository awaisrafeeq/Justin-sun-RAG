"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2025-12-25 20:47:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import uuid


# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "rss_feeds",
        sa.Column("id", sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column("feed_url", sa.String(length=512), nullable=False, unique=True),
        sa.Column("feed_title", sa.String(length=512)),
        sa.Column("feed_description", sa.Text()),
        sa.Column("last_fetched_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("total_episodes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )

    op.create_table(
        "documents",
        sa.Column("id", sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column("filename", sa.String(length=512), nullable=False),
        sa.Column("file_hash", sa.String(length=128), nullable=False, unique=True),
        sa.Column("doc_type", sa.String(length=64), nullable=False),
        sa.Column("extracted_name", sa.String(length=256)),
        sa.Column("extracted_metadata", sa.JSON()),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("chunk_ids", sa.ARRAY(sa.String())),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )

    op.create_table(
        "episodes",
        sa.Column("id", sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column("feed_id", sa.UUID(), sa.ForeignKey("rss_feeds.id", ondelete="CASCADE"), nullable=False),
        sa.Column("guid", sa.String(length=512), nullable=False),
        sa.Column("title", sa.String(length=512)),
        sa.Column("audio_url", sa.String(length=1024)),
        sa.Column("published_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("chunk_ids", sa.ARRAY(sa.String())),
        sa.Column("processed_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("has_errors", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.UniqueConstraint("feed_id", "guid", name="uq_feed_guid"),
    )


def downgrade() -> None:
    op.drop_table("episodes")
    op.drop_table("documents")
    op.drop_table("rss_feeds")
