# Development Workflow

Daily development workflow and best practices for CurriculumExtractor.

**Last Updated**: October 23, 2025  
**Environment Status**: ✅ All services operational

---

## Quick Start

```bash
# Start all services with hot-reload
docker compose watch

# Access:
# - Frontend:  http://localhost:5173
# - API:       http://localhost:8000
# - API Docs:  http://localhost:8000/docs
```

**Login**: `admin@curriculumextractor.com` / `kRZtEcmM3tRevtEh1CitNL6s_s5ciE7q`

---

## Development Cycle

### 1. Start Development Environment

```bash
cd /Users/amostan/Repositories/CurriculumExtractor

# Option A: With hot-reload (recommended)
docker compose watch

# Option B: Standard mode
docker compose up -d

# Verify all services are healthy
docker compose ps
```

**Expected Services**:
- ✅ Backend (FastAPI) - http://localhost:8000
- ✅ Frontend (React) - http://localhost:5173
- ✅ Redis - localhost:6379
- ✅ Celery Worker - 4 processes
- ✅ Database (Supabase) - Session Mode
- ✅ Proxy (Traefik) - localhost:80
- ✅ MailCatcher - http://localhost:1080

### 2. Make Changes

Edit code in your IDE - changes auto-reload:
- **Backend**: FastAPI with `--reload` flag
- **Frontend**: Vite HMR (instant updates)
- **Celery**: Restart worker after task changes

### 3. Test Your Changes

```bash
# Backend unit tests
docker compose exec backend bash scripts/test.sh

# Frontend E2E tests (requires backend running)
cd frontend && npx playwright test

# Test Celery tasks
curl -X POST http://localhost:8000/api/v1/tasks/health-check
```

### 4. Check Code Quality

```bash
# Automated (runs on git commit)
git commit -m "feat: your change"

# Manual pre-commit check
uv run pre-commit run --all-files

# Individual checks
cd backend && uv run ruff check . && uv run mypy .
cd frontend && npm run lint
```

### 5. Commit Changes

```bash
git add .
git commit -m "feat: add extraction model"
git push origin your-branch
```

---

## Service Management

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs backend -f
docker compose logs celery-worker -f
docker compose logs frontend -f

# Filter for errors
docker compose logs backend | grep ERROR
```

### Restart Services

```bash
# Restart specific service
docker compose restart backend
docker compose restart celery-worker

# Restart all
docker compose restart

# Rebuild after dependency changes
docker compose build backend
docker compose up -d
```

### Stop Development Environment

```bash
# Stop all services
docker compose down

# Stop and remove volumes (CAUTION: deletes Redis data)
docker compose down -v
```

---

## Hot Reload

### Backend (FastAPI)
- ✅ Auto-reload enabled via `--reload` flag
- Code changes trigger automatic restart
- Watch for restart in logs: `docker compose logs backend -f`

### Frontend (React/Vite)
- ✅ Hot Module Replacement (HMR) enabled
- Changes appear instantly in browser
- No page refresh needed for most changes

### Celery Worker
- ⚠️ Manual restart required after task changes
- Run: `docker compose restart celery-worker`
- Watch logs: `docker compose logs celery-worker -f`

---

## Running Without Docker (Advanced)

### Prerequisites
- Python 3.10 (use pyenv if you have 3.13)
- Node.js v20+ (via fnm/nvm)
- Access to Supabase and Redis

### Backend Only (Local)
```bash
# Terminal 1: Ensure Redis is running
docker compose up redis -d

# Terminal 2: Run backend locally
cd backend
source .venv/bin/activate
fastapi dev app/main.py
# Access: http://localhost:8000
```

### Frontend Only (Local)
```bash
cd frontend
npm run dev
# Access: http://localhost:5173
```

### Celery Worker (Local)
```bash
# Ensure Redis is running
docker compose up redis -d

cd backend
source .venv/bin/activate
celery -A app.worker worker --loglevel=info --concurrency=4
```

---

## Working with Celery Tasks

### Creating a New Task

1. **Create task file** (e.g., `backend/app/tasks/extraction.py`):
   ```python
   from app.worker import celery_app
   import logging
   
   logger = logging.getLogger(__name__)
   
   @celery_app.task(bind=True, name="app.tasks.extraction.process_pdf")
   def process_pdf_task(self, extraction_id: str):
       logger.info(f"Processing: {extraction_id}")
       # Your task logic here
       return {"status": "completed", "extraction_id": extraction_id}
   ```

2. **Import in `backend/app/tasks/__init__.py`**:
   ```python
   from app.tasks.extraction import *  # noqa
   ```

3. **Rebuild and restart**:
   ```bash
   docker compose restart celery-worker
   ```

4. **Test the task**:
   ```bash
   # Via API
   curl -X POST http://localhost:8000/api/v1/tasks/health-check
   
   # Check status
   curl http://localhost:8000/api/v1/tasks/status/{TASK_ID}
   ```

### Monitoring Celery

```bash
# View worker logs
docker compose logs celery-worker -f

# Check registered tasks
docker compose exec celery-worker celery -A app.worker inspect registered

# Get worker stats
docker compose exec celery-worker celery -A app.worker inspect stats

# See active tasks
docker compose exec celery-worker celery -A app.worker inspect active
```

### Debugging Celery Tasks

**Add detailed logging**:
```python
import logging
logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def my_task(self):
    logger.info(f"Task started: {self.request.id}")
    logger.debug(f"Task args: {self.request.args}")
    # ... your code
    logger.info(f"Task completed: {self.request.id}")
```

**Watch logs in real-time**:
```bash
docker compose logs celery-worker -f | grep "my_task"
```

---

## Working with Supabase

### Using Supabase MCP Server

**For database operations, use the Supabase MCP server** (Model Context Protocol):

```python
# Project ID for all MCP commands
PROJECT_ID = "wijzypbstiigssjuiuvh"

# List all tables
mcp_supabase_list_tables(
    project_id="wijzypbstiigssjuiuvh",
    schemas=["public"]
)

# Execute SQL query
mcp_supabase_execute_sql(
    project_id="wijzypbstiigssjuiuvh",
    query="SELECT * FROM users LIMIT 10;"
)

# Apply database migration
mcp_supabase_apply_migration(
    project_id="wijzypbstiigssjuiuvh",
    name="add_new_column",
    query="ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(50);"
)

# Check for security issues
mcp_supabase_get_advisors(
    project_id="wijzypbstiigssjuiuvh",
    type="security"
)
```

### Storage Operations

**Create buckets** (via Supabase Dashboard):
1. Go to: https://app.supabase.com/project/wijzypbstiigssjuiuvh/storage
2. Create bucket: `worksheets` (private)
3. Create bucket: `extractions` (private)

**Upload files** (in backend code):
```python
from supabase import create_client
from app.core.config import settings

supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

# Upload file
with open(file_path, 'rb') as f:
    result = supabase.storage.from_("worksheets").upload(
        file=f,
        path=f"uploads/{user_id}/{filename}",
        file_options={"content-type": "application/pdf"}
    )

# Generate signed URL (7-day expiry)
url = supabase.storage.from_("worksheets").create_signed_url(
    path=f"uploads/{user_id}/{filename}",
    expires_in=604800
)
```

---

## Testing Strategy

### Test-Driven Development (TDD)

- ✅ Write tests FIRST before implementing features
- ✅ Run tests frequently during development
- ✅ Ensure all tests pass before committing
- ✅ Aim for ≥80% code coverage

### Backend Testing

```bash
# Run all tests with coverage
docker compose exec backend bash scripts/test.sh

# Run specific test file
docker compose exec backend pytest tests/api/routes/test_users.py -v

# Run specific test
docker compose exec backend pytest tests/api/routes/test_users.py::test_create_user -v

# Run with output
docker compose exec backend pytest -s
```

### Frontend Testing

```bash
cd frontend

# Run all E2E tests
npx playwright test

# Run specific test
npx playwright test login.spec.ts

# Run in UI mode (interactive)
npx playwright test --ui

# Debug mode
npx playwright test --debug
```

### Celery Task Testing

```bash
# Test via API (recommended)
curl -X POST http://localhost:8000/api/v1/tasks/health-check

# Test via Python
docker compose exec backend python3 -c "
from app.tasks.default import health_check_task
result = health_check_task.delay()
print(result.get(timeout=10))
"

# Test with pytest (set CELERY_TASK_ALWAYS_EAGER=True in tests)
docker compose exec backend pytest tests/tasks/ -v
```

## Code Quality Checks

Pre-commit hooks automatically run:
- Ruff (Python linting/formatting)
- Biome (TypeScript linting)
- YAML/TOML validation

Manual checks:
```bash
# Backend
cd backend
uv run ruff check .
uv run mypy .

# Frontend
cd frontend
npm run lint
```

---

## Debugging

### Backend Debugging

**View detailed logs**:
```bash
# Application logs
docker compose logs backend -f

# Database query logs (set echo=True in db.py)
docker compose exec backend python3 -c "
from app.core.db import engine
engine.echo = True
# Run your code
"

# Check environment variables
docker compose exec backend env | grep -E "SUPABASE|DATABASE|REDIS"
```

**Test database connection**:
```bash
# Via MCP
mcp_supabase_get_project(id="wijzypbstiigssjuiuvh")

# Via Python
docker compose exec backend python3 -c "
from app.core.db import engine
conn = engine.connect()
print('✅ Connected!')
conn.close()
"
```

**Interactive Python shell**:
```bash
docker compose exec backend python3
>>> from app.core.db import engine
>>> from app.models import User
>>> from sqlmodel import Session, select
>>> with Session(engine) as session:
...     users = session.exec(select(User)).all()
...     print(f"Users: {len(users)}")
```

### Frontend Debugging

**Browser DevTools**:
- React DevTools for component inspection
- TanStack Query DevTools (auto-enabled in dev)
- Network tab for API calls

**Check for errors**:
```bash
# Console logs in browser
# Or check Vite dev server output
docker compose logs frontend -f
```

**TypeScript type checking**:
```bash
cd frontend
npx tsc --noEmit
```

### Celery Debugging

**Check task status**:
```bash
# Via API
curl http://localhost:8000/api/v1/tasks/status/{TASK_ID}

# Via Python
docker compose exec celery-worker python3 -c "
from celery.result import AsyncResult
from app.worker import celery_app
result = AsyncResult('task-id', app=celery_app)
print(f'Status: {result.status}')
print(f'Result: {result.result if result.successful() else result.info}')
"
```

**Test task directly**:
```bash
docker compose exec celery-worker python3 -c "
from app.tasks.default import health_check_task
result = health_check_task.delay()
print(f'Task queued: {result.id}')
# Wait and get result
print(f'Result: {result.get(timeout=10)}')
"
```

---

## Database Inspection (MCP)

### Quick Database Queries

```python
# Check table structure
mcp_supabase_execute_sql(
    project_id="wijzypbstiigssjuiuvh",
    query="""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'users'
    ORDER BY ordinal_position;
    """
)

# Count records
mcp_supabase_execute_sql(
    project_id="wijzypbstiigssjuiuvh",
    query="SELECT COUNT(*) FROM users;"
)

# View recent migrations
mcp_supabase_list_migrations(project_id="wijzypbstiigssjuiuvh")

# Check database logs (last 24 hours)
mcp_supabase_get_logs(
    project_id="wijzypbstiigssjuiuvh",
    service="postgres"
)
```

### Security Audits

```python
# Check for missing RLS policies
mcp_supabase_get_advisors(
    project_id="wijzypbstiigssjuiuvh",
    type="security"
)

# Check for performance issues
mcp_supabase_get_advisors(
    project_id="wijzypbstiigssjuiuvh",
    type="performance"
)
```

---

## Database Changes

### Method 1: Alembic (Recommended for Team Development)

**Complete workflow**:

1. **Update models** in `backend/app/models.py`:
   ```python
   class Extraction(SQLModel, table=True):
       id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
       filename: str = Field(max_length=255)
       status: str = Field(default="DRAFT", max_length=50)
       created_at: datetime = Field(default_factory=datetime.utcnow)
       user_id: uuid.UUID = Field(foreign_key="user.id")
   ```

2. **Generate migration**:
   ```bash
   docker compose exec backend alembic revision --autogenerate -m "Add Extraction model"
   ```

3. **Review migration** in `backend/app/alembic/versions/`:
   - Check the generated SQL
   - Add any custom logic needed
   - Verify foreign keys and constraints

4. **Apply migration**:
   ```bash
   docker compose exec backend alembic upgrade head
   ```

5. **Verify in Supabase**:
   ```python
   # Use MCP to verify
   mcp_supabase_list_tables(
       project_id="wijzypbstiigssjuiuvh",
       schemas=["public"]
   )
   
   # Check for security issues
   mcp_supabase_get_advisors(
       project_id="wijzypbstiigssjuiuvh",
       type="security"
   )
   ```

6. **Commit migration files**:
   ```bash
   git add backend/app/alembic/versions/
   git commit -m "feat: add extraction model"
   ```

### Method 2: Supabase MCP (Quick Prototyping/Hotfixes)

**For rapid iterations**:

```python
# 1. Apply change via MCP
mcp_supabase_apply_migration(
    project_id="wijzypbstiigssjuiuvh",
    name="add_extraction_table",
    query="""
    CREATE TABLE IF NOT EXISTS extractions (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        filename VARCHAR(255) NOT NULL,
        status VARCHAR(50) DEFAULT 'DRAFT',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
)

# 2. Sync Alembic to match
docker compose exec backend alembic stamp head

# 3. Generate migration for version control
docker compose exec backend alembic revision --autogenerate -m "Sync extraction table"
```

### Migration Best Practices

- ✅ Always review auto-generated migrations
- ✅ Test migrations on local/staging before production
- ✅ Use MCP to verify tables after migration
- ✅ Check for missing RLS policies with MCP advisors
- ✅ Commit migration files to git
- ❌ Don't edit applied migrations (create new ones)

### Keeping Alembic Synchronized with Database

**The Problem**: Database changes made outside Alembic (via MCP, Supabase Dashboard, or direct SQL) create a mismatch between database state and migration history.

**The Solution**: Always create migrations for external changes and use `alembic stamp` to mark them as applied.

#### Complete Synchronization Workflow

**Step 1: Identify the Mismatch**

Common error: `Can't locate revision identified by 'XXXXXX'`

```bash
# Check current Alembic version
docker compose exec backend alembic current

# Check database version
mcp_supabase_execute_sql(
    project_id="wijzypbstiigssjuiuvh",
    query="SELECT version_num FROM alembic_version;"
)

# List local migration files
ls backend/app/alembic/versions/
```

**Step 2: Inspect Database State**

```python
# List all tables
mcp_supabase_list_tables(
    project_id="wijzypbstiigssjuiuvh",
    schemas=["public"]
)

# Check table structure
mcp_supabase_execute_sql(
    project_id="wijzypbstiigssjuiuvh",
    query="""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'extractions'
    ORDER BY ordinal_position;
    """
)

# Check RLS policies
mcp_supabase_execute_sql(
    project_id="wijzypbstiigssjuiuvh",
    query="""
    SELECT schemaname, tablename, policyname, cmd, qual
    FROM pg_policies
    WHERE schemaname = 'public'
    ORDER BY tablename, policyname;
    """
)
```

**Step 3: Reset to Valid Version**

If database has unknown version, reset to latest known version:

```python
# Find latest valid migration from your codebase
# Example: 1a31ce608336

# Update database to this version
mcp_supabase_execute_sql(
    project_id="wijzypbstiigssjuiuvh",
    query="UPDATE alembic_version SET version_num = '1a31ce608336';"
)

# Verify
docker compose exec backend alembic current
# Should now show: 1a31ce608336 (head)
```

**Step 4: Create Catchup Migrations**

For each table/change that exists in database but not in migrations:

```bash
# Create migration matching current database state
docker compose exec backend alembic revision -m "create extractions table"
```

Edit the migration file to match EXACTLY what's in the database:

```python
# backend/app/alembic/versions/XXXXX_create_extractions_table.py
def upgrade():
    # Copy exact schema from database inspection
    op.create_table(
        'extractions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('owner_id', sa.UUID(), nullable=False),
        # ... all other columns
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ondelete='CASCADE')
    )

    # Include indexes
    op.create_index('ix_extractions_owner_id', 'extractions', ['owner_id'])

def downgrade():
    # Reverse operations
    op.drop_index('ix_extractions_owner_id', 'extractions')
    op.drop_table('extractions')
```

**Step 5: Mark Migration as Applied**

Since the table/changes already exist in database:

```bash
# Get the new revision ID from the migration file (revision = 'XXXXX')
docker compose exec backend alembic stamp XXXXX

# Verify it's in the chain
docker compose exec backend alembic history
docker compose exec backend alembic current
```

**Step 6: Apply Any New Migrations**

If you have new migrations after the catchup:

```bash
docker compose exec backend alembic upgrade head
```

**Step 7: Verify Everything**

```bash
# Check Alembic is at head
docker compose exec backend alembic current

# Verify database tables
mcp_supabase_list_tables(project_id="wijzypbstiigssjuiuvh", schemas=["public"])

# Check for security issues (missing RLS policies)
mcp_supabase_get_advisors(project_id="wijzypbstiigssjuiuvh", type="security")

# Rebuild backend with new migrations
docker compose build backend
docker compose up -d backend celery-worker

# Test the services start cleanly
docker compose logs backend --tail=20
```

**Step 8: Commit Migration Files**

```bash
git add backend/app/alembic/versions/
git commit -m "chore(db): sync Alembic migrations with database state"
git push
```

#### Common Scenarios

**Scenario 1: Added table via MCP or Supabase Dashboard**

1. Table exists in database, not in Alembic
2. Create migration with `CREATE TABLE` statement matching database
3. Use `alembic stamp` to mark as applied
4. Commit migration file

**Scenario 2: Enabled RLS directly in database**

1. RLS and policies exist, no migration tracking them
2. Create migration with `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` and `CREATE POLICY` statements
3. Use `alembic stamp` to mark as applied
4. Commit migration file

**Scenario 3: Database version doesn't exist in codebase**

1. Database has version `460746be37d1`, codebase doesn't have this file
2. Reset database to latest known version: `UPDATE alembic_version SET version_num = 'latest_known'`
3. Create catchup migrations for any missing tables/changes
4. Use `alembic stamp` for each catchup migration
5. Continue with normal workflow

**Scenario 4: Multiple developers made conflicting migrations**

1. Pull latest code with new migrations
2. Check for parallel branches in `alembic history`
3. If needed, create merge migration: `alembic merge -m "merge migration branches"`
4. Apply with `alembic upgrade head`

#### Troubleshooting

**Error: `Can't locate revision identified by 'XXXXX'`**
- Database has migration version that doesn't exist in codebase
- Solution: Reset to known version (Step 3 above), create catchup migrations

**Error: `Target database is not up to date`**
- Database schema differs from migration expectations
- Solution: Use MCP to inspect database, create migrations matching actual state

**Error: Table already exists**
- Migration tries to create table that already exists
- Solution: Don't run `alembic upgrade`, use `alembic stamp` instead

**Warning: Missing RLS policies**
- After running migrations, `mcp_supabase_get_advisors` shows security issues
- Solution: Create migration to add RLS policies, apply with `alembic stamp`

**Multiple heads in migration history**
- Conflicting migrations from different branches
- Solution: `alembic merge heads -m "merge branches"`, then `alembic upgrade head`

#### Prevention Best Practices

1. **Always use Alembic for schema changes** when possible
2. **If using MCP/Dashboard**, immediately create migration and stamp it
3. **Check migration status** before starting work: `alembic current`
4. **Verify security** after schema changes: `mcp_supabase_get_advisors(type="security")`
5. **Rebuild Docker** after adding migrations: `docker compose build backend`
6. **Test locally** before pushing migrations to remote
7. **Document complex migrations** in commit messages
8. **Use Context7** to research Alembic best practices when uncertain

---

## Adding API Endpoints

### Complete Workflow

1. **Create route file** (e.g., `backend/app/api/routes/extractions.py`):
   ```python
   from fastapi import APIRouter, HTTPException
   from app.api.deps import CurrentUser, SessionDep
   from app.models import Extraction, ExtractionCreate, ExtractionPublic
   
   router = APIRouter(prefix="/extractions", tags=["extractions"])
   
   @router.get("/", response_model=list[ExtractionPublic])
   def list_extractions(session: SessionDep, current_user: CurrentUser):
       statement = select(Extraction).where(Extraction.user_id == current_user.id)
       extractions = session.exec(statement).all()
       return extractions
   
   @router.post("/", response_model=ExtractionPublic)
   def create_extraction(
       session: SessionDep,
       current_user: CurrentUser,
       extraction_in: ExtractionCreate
   ):
       extraction = Extraction.model_validate(
           extraction_in,
           update={"user_id": current_user.id}
       )
       session.add(extraction)
       session.commit()
       session.refresh(extraction)
       return extraction
   ```

2. **Register route** in `backend/app/api/main.py`:
   ```python
   from app.api.routes import extractions, login, users, utils, tasks
   
   api_router.include_router(extractions.router)
   ```

3. **Generate TypeScript client**:
   ```bash
   ./scripts/generate-client.sh
   ```

4. **Test in API docs**: http://localhost:8000/docs

5. **Use in frontend**:
   ```typescript
   import { ExtractionsService } from '@/client'
   
   const { data } = useQuery({
     queryKey: ['extractions'],
     queryFn: () => ExtractionsService.listExtractions()
   })
   ```

---

## Frontend Development

### File-Based Routing (TanStack Router)

**Create new route**:
```bash
# Create: frontend/src/routes/_layout/extractions.tsx
# URL becomes: http://localhost:5173/extractions
```

**Route template**:
```typescript
import { createFileRoute } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { ExtractionsService } from '@/client'

export const Route = createFileRoute('/_layout/extractions')({
  component: ExtractionsPage,
})

function ExtractionsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['extractions'],
    queryFn: () => ExtractionsService.listExtractions(),
  })

  if (isLoading) return <div>Loading...</div>
  
  return (
    <div>
      <h1>Extractions</h1>
      {/* Your UI */}
    </div>
  )
}
```

**After creating routes**:
- TanStack Router auto-generates `routeTree.gen.ts`
- No manual route registration needed

### Generating OpenAPI Client

**After any backend API changes**:

```bash
# From project root
./scripts/generate-client.sh

# Or manually
cd frontend
npm run generate-client
```

This updates:
- `frontend/src/client/schemas.gen.ts`
- `frontend/src/client/sdk.gen.ts`
- `frontend/src/client/types.gen.ts`

**Always commit generated client files!**

---

## Common Development Tasks

### Add a New Model

```bash
# 1. Define in backend/app/models.py
# 2. Generate migration
docker compose exec backend alembic revision --autogenerate -m "Add model"
# 3. Review and apply
docker compose exec backend alembic upgrade head
# 4. Verify via MCP
mcp_supabase_list_tables(project_id="wijzypbstiigssjuiuvh", schemas=["public"])
```

### Add Frontend Dependencies

```bash
cd frontend
npm install package-name@version

# Frontend auto-reloads, no rebuild needed
# Update imports in your code
```

### Add Backend Dependencies

```bash
# 1. Edit backend/pyproject.toml
# 2. Rebuild
docker compose build backend
# 3. Restart
docker compose up -d backend celery-worker
```

### Update OpenAPI Client

```bash
# After any backend API changes
./scripts/generate-client.sh

# Commit generated files
git add frontend/src/client/
git commit -m "chore: update API client"
```

---

## Environment & Credentials

### Current Project

- **Supabase Project**: wijzypbstiigssjuiuvh
- **Region**: ap-south-1 (Mumbai, India)
- **Database**: PostgreSQL 17.6.1
- **Connection**: Session Mode (port 5432)
- **Dashboard**: https://app.supabase.com/project/wijzypbstiigssjuiuvh

### Development Credentials

- **Admin Email**: admin@curriculumextractor.com
- **Admin Password**: kRZtEcmM3tRevtEh1CitNL6s_s5ciE7q
- **Database Password**: Curriculumextractor1234!

### Service URLs

| Service | URL | Notes |
|---------|-----|-------|
| Frontend | http://localhost:5173 | React app |
| Backend API | http://localhost:8000 | FastAPI |
| API Docs | http://localhost:8000/docs | Swagger UI |
| MailCatcher | http://localhost:1080 | Email testing |
| Traefik Dashboard | http://localhost:8090 | Proxy stats |
| Supabase Dashboard | https://app.supabase.com/project/wijzypbstiigssjuiuvh | DB management |

---

## Useful Commands Reference

### Docker Compose

```bash
# Start with hot-reload
docker compose watch

# Start normally
docker compose up -d

# Stop all
docker compose down

# View all logs
docker compose logs -f

# Specific service logs
docker compose logs backend -f

# Restart service
docker compose restart backend

# Rebuild after dependency changes
docker compose build backend
docker compose up -d

# Check service status
docker compose ps

# Execute command in service
docker compose exec backend bash
```

### Celery

```bash
# View worker logs
docker compose logs celery-worker -f

# Restart worker
docker compose restart celery-worker

# Check registered tasks
docker compose exec celery-worker celery -A app.worker inspect registered

# Get worker stats
docker compose exec celery-worker celery -A app.worker inspect stats

# Purge all tasks
docker compose exec celery-worker celery -A app.worker purge
```

### Database (Alembic)

```bash
# Generate migration
docker compose exec backend alembic revision --autogenerate -m "Description"

# Apply migrations
docker compose exec backend alembic upgrade head

# Rollback one version
docker compose exec backend alembic downgrade -1

# Show current version
docker compose exec backend alembic current

# Show migration history
docker compose exec backend alembic history
```

### Database (Supabase MCP)

```python
# List tables
mcp_supabase_list_tables(project_id="wijzypbstiigssjuiuvh", schemas=["public"])

# Execute query
mcp_supabase_execute_sql(project_id="wijzypbstiigssjuiuvh", query="SELECT COUNT(*) FROM users;")

# Apply migration
mcp_supabase_apply_migration(project_id="wijzypbstiigssjuiuvh", name="migration_name", query="SQL")

# Check advisories
mcp_supabase_get_advisors(project_id="wijzypbstiigssjuiuvh", type="security")
```

---

## Troubleshooting

### Backend Won't Start

```bash
# Check logs
docker compose logs backend --tail=50

# Common issues:
# - Database connection failed → Check .env DATABASE_URL
# - Import error → Rebuild: docker compose build backend
# - Port in use → Check: lsof -i :8000
```

### Celery Worker Not Processing

```bash
# Check if worker is running
docker compose ps celery-worker

# Check logs
docker compose logs celery-worker --tail=50

# Verify Redis connection
docker compose exec redis redis-cli -a 5WEQ47_uuNd-289-_ZnN79GmNY8LFWzy PING

# Check registered tasks
docker compose exec celery-worker celery -A app.worker inspect registered
```

### Frontend Not Loading

```bash
# Check logs
docker compose logs frontend --tail=50

# Rebuild if needed
docker compose build frontend
docker compose up -d frontend

# Check if backend is accessible
curl http://localhost:8000/api/v1/utils/health-check/
```

### Database Connection Issues

```bash
# Test via MCP
mcp_supabase_get_project(id="wijzypbstiigssjuiuvh")

# Check database logs
mcp_supabase_get_logs(project_id="wijzypbstiigssjuiuvh", service="postgres")

# Test connection from backend
docker compose exec backend python3 -c "from app.core.db import engine; engine.connect(); print('✅ Connected')"
```

---

## Performance Tips

### Backend Optimization

- Use `Session` context managers (auto-closes connections)
- Implement pagination for list endpoints
- Use `select()` with filters before fetching
- Add database indexes for frequent queries
- Monitor connection pool usage

### Celery Optimization

- Set appropriate `time_limit` for tasks
- Use `task_reject_on_worker_lost=True` for critical tasks
- Implement retry logic with exponential backoff
- Monitor task queue depth
- Use separate queues for different task types

### Frontend Optimization

- Use TanStack Query for server state (automatic caching)
- Implement virtualization for long lists
- Lazy load routes with TanStack Router
- Optimize images before upload
- Use React.memo for expensive components

---

## Git Workflow

### Branch Strategy

```bash
# Create feature branch
git checkout -b feature/extraction-model

# Make changes, commit frequently
git add .
git commit -m "feat: add extraction model"

# Push to remote
git push origin feature/extraction-model

# Create pull request on GitHub
```

### PR Labeling

**All pull requests must have at least one type label** to pass CI checks. The `check-labels` workflow validates this requirement.

**Available labels** (based on conventional commit types):
- `feature` - New feature implementation (feat commits)
- `bug` - Bug fixes (fix commits)
- `docs` - Documentation changes (docs commits)
- `refactor` - Code refactoring (refactor commits)
- `enhancement` - Performance improvements (perf commits)
- `internal` - Internal/maintenance changes (chore, ci, build, style commits)
- `breaking` - Breaking changes (feat!, fix! commits)
- `security` - Security-related changes
- `upgrade` - Dependency upgrades

**Labeling methods**:
1. **Manual**: Add label via GitHub UI when creating PR
2. **Via Claude**: Use the `pr-labeling` skill when creating PRs with Claude Code
3. **Via CLI**: `gh pr edit <number> --add-label <label-name>`

**Example**:
```bash
# Create PR with gh CLI
gh pr create --title "feat: add extraction model" --body "Description"

# Add label
gh pr edit <number> --add-label feature
```

### Commit Message Format

Follow conventional commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `test:` - Tests
- `refactor:` - Code refactoring
- `chore:` - Maintenance

**Examples**:
```bash
git commit -m "feat: add PDF extraction Celery task"
git commit -m "fix: resolve database connection timeout"
git commit -m "docs: update CLAUDE.md with MCP commands"
git commit -m "test: add extraction model tests"
```

---

## Quick Links

**Documentation**:
- [Setup Guide](./setup.md) - Initial installation
- [Supabase Setup](./supabase-setup-guide.md) - Database configuration
- [Architecture Overview](../architecture/overview.md) - System design
- [PRD Overview](../prd/overview.md) - Product requirements

**Status Documents**:
- [DEVELOPMENT_READY.md](../../DEVELOPMENT_READY.md) - Current environment status
- [CELERY_SETUP_COMPLETE.md](../../CELERY_SETUP_COMPLETE.md) - Celery configuration
- [ENVIRONMENT_RUNNING.md](../../ENVIRONMENT_RUNNING.md) - Services overview
- [CLAUDE.md](../../CLAUDE.md) - AI development guide

**External**:
- [Supabase Dashboard](https://app.supabase.com/project/wijzypbstiigssjuiuvh)
- [FastAPI Docs](https://fastapi.tiangolo.com)
- [TanStack Query Docs](https://tanstack.com/query)
- [Celery Docs](https://docs.celeryproject.org)

---

## Next Steps

Now that your environment is running, start building features:

1. ✅ ~~Environment setup~~ COMPLETE
2. ✅ ~~Infrastructure (Celery + Redis)~~ COMPLETE
3. **Create core models** (Extraction, Question, Ingestion)
4. Set up Supabase Storage buckets
5. Add PDF processing libraries
6. Implement extraction pipeline
7. Build review UI

See [PRD Overview](../prd/overview.md) for complete feature requirements!

---

**Happy developing! 🚀**
