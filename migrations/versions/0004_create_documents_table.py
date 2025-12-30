"""Create documents table

Revision ID: 0004
Revises: 0003
Create Date: 2025-12-30 20:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0004'
down_revision: Union[str, None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create documents table
    op.create_table('documents',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('file_hash', sa.String(length=64), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('has_errors', sa.Boolean(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('extracted_text', sa.Text(), nullable=True),
        sa.Column('table_count', sa.Integer(), nullable=False),
        sa.Column('image_count', sa.Integer(), nullable=False),
        sa.Column('page_count', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('author', sa.String(length=255), nullable=True),
        sa.Column('subject', sa.String(length=500), nullable=True),
        sa.Column('creator', sa.String(length=255), nullable=True),
        sa.Column('producer', sa.String(length=255), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('chunk_ids', sa.LargeBinary(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('file_hash')
    )
    
    # Create indexes
    op.create_index(op.f('ix_documents_file_hash'), 'documents', ['file_hash'], unique=True)
    op.create_index(op.f('ix_documents_status'), 'documents', ['status'])
    op.create_index(op.f('ix_documents_created_at'), 'documents', ['created_at'])
    op.create_index(op.f('ix_documents_processed_at'), 'documents', ['processed_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_documents_processed_at'), table_name='documents')
    op.drop_index(op.f('ix_documents_created_at'), table_name='documents')
    op.drop_index(op.f('ix_documents_status'), table_name='documents')
    op.drop_index(op.f('ix_documents_file_hash'), table_name='documents')
    
    # Drop table
    op.drop_table('documents')
