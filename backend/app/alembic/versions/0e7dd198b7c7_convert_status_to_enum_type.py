"""convert_status_to_enum_type

Convert ingestions.status column from VARCHAR to PostgreSQL ENUM type.

This migration:
1. Creates extractionstatus ENUM type with all status values
2. Converts existing VARCHAR status column to use the ENUM type
3. Maintains data integrity by mapping existing values to ENUM

Revision ID: 0e7dd198b7c7
Revises: 2ccac127c59f
Create Date: 2025-10-30 13:25:21.537208

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '0e7dd198b7c7'
down_revision = '2ccac127c59f'
branch_labels = None
depends_on = None


def upgrade():
    """Convert status column to PostgreSQL ENUM type."""
    # Create extractionstatus ENUM type
    op.execute("""
        CREATE TYPE extractionstatus AS ENUM (
            'UPLOADED',
            'OCR_IN_PROGRESS',
            'OCR_COMPLETE',
            'OCR_FAILED',
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

    # Update existing 'OCR_PROCESSING' values to 'OCR_IN_PROGRESS' if any exist
    op.execute("""
        UPDATE ingestions
        SET status = 'OCR_IN_PROGRESS'
        WHERE status = 'OCR_PROCESSING'
    """)

    # Convert status column to use ENUM type
    op.execute("""
        ALTER TABLE ingestions
        ALTER COLUMN status TYPE extractionstatus
        USING status::text::extractionstatus
    """)


def downgrade():
    """Convert status column back to VARCHAR."""
    # Convert status column back to VARCHAR
    op.execute("""
        ALTER TABLE ingestions
        ALTER COLUMN status TYPE VARCHAR
        USING status::text
    """)

    # Drop the ENUM type
    op.execute("DROP TYPE extractionstatus")
