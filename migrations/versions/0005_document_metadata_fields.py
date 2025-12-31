"""document metadata fields

Revision ID: 0005_document_metadata_fields
Revises: 0004
Create Date: 2025-12-31 19:01:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0005_document_metadata_fields"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("documents"):
        return

    existing_cols = {col["name"] for col in inspector.get_columns("documents")}

    if "doc_type" not in existing_cols:
        op.add_column("documents", sa.Column("doc_type", sa.String(length=64), nullable=True))
        op.create_index(op.f("ix_documents_doc_type"), "documents", ["doc_type"])

    if "extracted_name" not in existing_cols:
        op.add_column(
            "documents",
            sa.Column("extracted_name", sa.String(length=256), nullable=True),
        )

    if "extracted_metadata" not in existing_cols:
        op.add_column("documents", sa.Column("extracted_metadata", sa.JSON(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("documents"):
        return

    existing_cols = {col["name"] for col in inspector.get_columns("documents")}

    if "extracted_metadata" in existing_cols:
        op.drop_column("documents", "extracted_metadata")

    if "extracted_name" in existing_cols:
        op.drop_column("documents", "extracted_name")

    if "doc_type" in existing_cols:
        op.drop_index(op.f("ix_documents_doc_type"), table_name="documents")
        op.drop_column("documents", "doc_type")
