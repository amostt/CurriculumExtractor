"""create extractions table

Revision ID: efc9ab8c3122
Revises: 1a31ce608336
Create Date: 2025-10-27 13:27:28.795473

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = 'efc9ab8c3122'
down_revision = '1a31ce608336'
branch_labels = None
depends_on = None


def upgrade():
    # Create extraction_status enum type
    op.execute("""
        CREATE TYPE extraction_status AS ENUM (
            'UPLOADED',
            'OCR_PROCESSING',
            'OCR_COMPLETE',
            'SEGMENTATION_PROCESSING',
            'SEGMENTATION_COMPLETE',
            'TAGGING_PROCESSING',
            'DRAFT',
            'IN_REVIEW',
            'APPROVED',
            'REJECTED',
            'FAILED'
        )
    """)

    # Create extractions table
    op.create_table(
        'extractions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('owner_id', sa.UUID(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('page_count', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('status', sa.Enum(
            'UPLOADED', 'OCR_PROCESSING', 'OCR_COMPLETE',
            'SEGMENTATION_PROCESSING', 'SEGMENTATION_COMPLETE',
            'TAGGING_PROCESSING', 'DRAFT', 'IN_REVIEW',
            'APPROVED', 'REJECTED', 'FAILED',
            name='extraction_status'
        ), nullable=False, server_default='UPLOADED'),
        sa.Column('presigned_url', sa.String(length=2048), nullable=False),
        sa.Column('storage_path', sa.String(length=512), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ondelete='CASCADE'),
        sa.CheckConstraint('file_size > 0', name='file_size_positive')
    )

    # Create indexes
    op.create_index('ix_extractions_owner_id', 'extractions', ['owner_id'])
    op.create_index('ix_extractions_status', 'extractions', ['status'])
    op.create_index('ix_extractions_uploaded_at', 'extractions', ['uploaded_at'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_extractions_uploaded_at', 'extractions')
    op.drop_index('ix_extractions_status', 'extractions')
    op.drop_index('ix_extractions_owner_id', 'extractions')

    # Drop table
    op.drop_table('extractions')

    # Drop enum type
    op.execute('DROP TYPE extraction_status')
