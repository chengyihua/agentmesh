# Production Hardening Phase 3 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enhance production readiness by implementing database migrations (Alembic) and end-to-end (E2E) integration tests.

**Architecture:**
- **Migrations**: Use Alembic for version control of database schema (PostgreSQL).
- **E2E Tests**: Use `pytest` with a real/mocked environment to test the full flow: Register -> Connect -> Invoke.

**Tech Stack:** Python, Alembic, SQLAlchemy, Pytest, Docker

---

### Task 1: Setup Alembic for Migrations

**Files:**
- Create: `alembic.ini`
- Create: `migrations/env.py`
- Create: `migrations/script.py.mako`
- Modify: `src/agentmesh/storage/postgres.py`

**Step 1: Initialize Alembic Config**

Create `alembic.ini`:
```ini
[alembic]
script_location = migrations
sqlalchemy.url = postgresql+asyncpg://postgres:postgres@localhost:5432/agentmesh

[post_write_hooks]
# hooks...
```

Create `migrations/env.py` (Async template):
```python
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from src.agentmesh.storage.models import Base  # Import your SQLAlchemy models

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
```

**Step 2: Generate Initial Migration**

Run command: `alembic revision --autogenerate -m "Initial migration"`

### Task 2: Create End-to-End Test Suite

**Files:**
- Create: `tests/e2e/test_full_flow.py`
- Create: `tests/e2e/conftest.py`

**Step 1: Setup E2E Fixtures**

Create `tests/e2e/conftest.py`:
```python
import pytest
import asyncio
import uvicorn
from fastapi.testclient import TestClient
from src.agentmesh.main import app
from src.agentmesh.client import AgentMeshClient

@pytest.fixture(scope="session")
def api_client():
    with TestClient(app) as client:
        yield client

@pytest.fixture(scope="session")
def mesh_client():
    # Configure client to point to TestClient or local server
    client = AgentMeshClient(base_url="http://testserver")
    # Mock/Adapter for TestClient might be needed if not running real server
    return client
```

**Step 2: Write Full Flow Test**

Create `tests/e2e/test_full_flow.py`:
```python
import pytest
from src.agentmesh.core.agent_card import AgentCard

@pytest.mark.asyncio
async def test_register_connect_invoke(api_client):
    # 1. Register Agent A
    agent_a = {
        "id": "agent-a",
        "name": "Agent A",
        "endpoint": "http://localhost:8001",
        "skills": [{"name": "echo", "description": "echoes input"}]
    }
    resp = api_client.post("/agents", json=agent_a)
    assert resp.status_code == 201

    # 2. Register Agent B
    agent_b = {
        "id": "agent-b",
        "name": "Agent B",
        "endpoint": "http://localhost:8002",
        "skills": [{"name": "ask", "description": "asks questions"}]
    }
    resp = api_client.post("/agents", json=agent_b)
    assert resp.status_code == 201

    # 3. Discovery
    resp = api_client.get("/agents?skill=echo")
    data = resp.json()
    assert len(data["data"]["agents"]) >= 1
    assert data["data"]["agents"][0]["id"] == "agent-a"

    # 4. Health Check (Simulated)
    # Trigger heartbeat
    resp = api_client.post("/agents/agent-a/heartbeat", json={"status": "healthy"})
    assert resp.status_code == 200

    # 5. Check Leaderboard
    resp = api_client.get("/agents/leaderboard")
    assert resp.status_code == 200
```

### Task 3: Docker Optimization (Optional but Recommended)

**Files:**
- Modify: `Dockerfile`
- Modify: `docker-compose.yml`

**Step 1: Optimize Dockerfile**
- Use multi-stage build to reduce size.
- Ensure `pip install` uses `--no-cache-dir`.

```dockerfile
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY src/ src/
COPY scripts/ scripts/
CMD ["python", "-m", "src.agentmesh.main"]
```
