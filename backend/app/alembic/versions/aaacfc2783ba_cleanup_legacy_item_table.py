"""cleanup legacy item table

Revision ID: aaacfc2783ba
Revises: efc9ab8c3122
Create Date: 2025-10-27 13:28:51.536266

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = 'aaacfc2783ba'
down_revision = 'efc9ab8c3122'
branch_labels = None
depends_on = None


def upgrade():
    # Drop legacy item table (no longer used in the application)
    # Use IF EXISTS to handle case where table was never created (e.g., fresh CI environment)
    op.execute('DROP TABLE IF EXISTS item CASCADE')


def downgrade():
    # Recreate item table if needed to rollback
    op.create_table(
        'item',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('owner_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ondelete='CASCADE')
    )
