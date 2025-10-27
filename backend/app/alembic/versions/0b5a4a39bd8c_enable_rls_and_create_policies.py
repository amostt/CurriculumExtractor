"""enable rls and create policies

Revision ID: 0b5a4a39bd8c
Revises: aaacfc2783ba
Create Date: 2025-10-27 13:39:30.925303

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '0b5a4a39bd8c'
down_revision = 'aaacfc2783ba'
branch_labels = None
depends_on = None


def upgrade():
    # Enable Row-Level Security on user table
    op.execute('ALTER TABLE "user" ENABLE ROW LEVEL SECURITY')

    # Enable Row-Level Security on extractions table
    op.execute('ALTER TABLE extractions ENABLE ROW LEVEL SECURITY')

    # Create RLS policies for user table
    op.execute("""
        CREATE POLICY "Users can view own profile"
        ON "user"
        FOR SELECT
        TO authenticated
        USING (id = auth.uid())
    """)

    op.execute("""
        CREATE POLICY "Users can update own profile"
        ON "user"
        FOR UPDATE
        TO authenticated
        USING (id = auth.uid())
        WITH CHECK (id = auth.uid())
    """)

    # Create RLS policies for extractions table
    op.execute("""
        CREATE POLICY "Users can view own extractions"
        ON extractions
        FOR SELECT
        TO authenticated
        USING (owner_id = auth.uid())
    """)

    op.execute("""
        CREATE POLICY "Users can create own extractions"
        ON extractions
        FOR INSERT
        TO authenticated
        WITH CHECK (owner_id = auth.uid())
    """)

    op.execute("""
        CREATE POLICY "Users can update own extractions"
        ON extractions
        FOR UPDATE
        TO authenticated
        USING (owner_id = auth.uid())
        WITH CHECK (owner_id = auth.uid())
    """)

    op.execute("""
        CREATE POLICY "Users can delete own extractions"
        ON extractions
        FOR DELETE
        TO authenticated
        USING (owner_id = auth.uid())
    """)


def downgrade():
    # Drop RLS policies for extractions table
    op.execute('DROP POLICY IF EXISTS "Users can delete own extractions" ON extractions')
    op.execute('DROP POLICY IF EXISTS "Users can update own extractions" ON extractions')
    op.execute('DROP POLICY IF EXISTS "Users can create own extractions" ON extractions')
    op.execute('DROP POLICY IF EXISTS "Users can view own extractions" ON extractions')

    # Drop RLS policies for user table
    op.execute('DROP POLICY IF EXISTS "Users can update own profile" ON "user"')
    op.execute('DROP POLICY IF EXISTS "Users can view own profile" ON "user"')

    # Disable Row-Level Security on extractions table
    op.execute('ALTER TABLE extractions DISABLE ROW LEVEL SECURITY')

    # Disable Row-Level Security on user table
    op.execute('ALTER TABLE "user" DISABLE ROW LEVEL SECURITY')
