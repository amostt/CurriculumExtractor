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
    # Check if auth schema exists (Supabase only)
    # RLS policies require Supabase auth.uid() function
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'auth')"
    ))
    has_auth_schema = result.scalar()

    if not has_auth_schema:
        # This should ONLY happen in legacy non-Supabase environments
        # CI should use Supabase local (see test-frontend.yml) to test RLS policies
        print("━" * 80)
        print("⚠️  WARNING: Skipping RLS policies - auth schema not found")
        print("⚠️  RLS policies are NOT being applied to this database!")
        print("")
        print("If you're seeing this in CI:")
        print("  - CI should use 'supabase start' for local Supabase instance")
        print("  - See .github/workflows/test-frontend.yml for proper setup")
        print("")
        print("If you're in local development:")
        print("  - Use 'supabase start' instead of plain PostgreSQL")
        print("  - Or accept that RLS won't be tested locally")
        print("━" * 80)
        return

    # Auth schema found - enable RLS and create policies
    print("✅ Supabase auth schema detected - enabling RLS policies")

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

    print("✅ RLS enabled on user and extractions tables")
    print("✅ Created 6 RLS policies (2 for user, 4 for extractions)")


def downgrade():
    # Check if auth schema exists (Supabase only, not in CI/testing)
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'auth')"
    ))
    has_auth_schema = result.scalar()

    if not has_auth_schema:
        # Skip RLS teardown in non-Supabase environments
        print("⚠️  Skipping RLS policy removal - auth schema not found (non-Supabase environment)")
        return

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
