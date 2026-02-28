# AgentMesh Decentralized Phase 2 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement Federation & Seed Synchronization (PR2) for decentralized AgentMesh, allowing agents to discover each other via seed nodes without a central registry.

**Architecture:** Introduce `FederationManager` to handle peer synchronization. Expose `/federation/pull` endpoint for other nodes to fetch registry data. Implement background task to periodically pull from configured seed nodes and merge updates into local `AgentRegistry` using CRDT-like rules (LWW on `updated_at`) and signature verification.

**Tech Stack:** Python 3.10+, FastAPI (or existing framework), httpx (for async requests), asyncio.

---

### Task 1: Federation Manager & Pull Endpoint

**Files:**
- Create: `src/agentmesh/core/federation.py`
- Modify: `src/agentmesh/api/routes.py`
- Test: `tests/test_federation.py`

**Step 1: Write the failing test**

Create `tests/test_federation.py` to verify `FederationManager` initialization and pull logic.

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from agentmesh.core.federation import FederationManager
from agentmesh.core.registry import AgentRegistry
from agentmesh.core.agent_card import AgentCard

@pytest.mark.asyncio
async def test_federation_pull_local_registry():
    # Setup registry with one agent
    registry = AgentRegistry()
    agent = AgentCard(
        id="test-agent-1",
        name="Test Agent",
        version="1.0.0",
        endpoint="http://localhost:8000",
        public_key="pk1",
        manifest_signature="sig1"
    )
    await registry.register_agent(agent)
    
    # Initialize FederationManager
    federation = FederationManager(registry=registry)
    
    # Test get_local_updates (what /pull endpoint calls)
    updates = await federation.get_local_updates(since_timestamp=0)
    
    assert len(updates["agents"]) == 1
    assert updates["agents"][0].id == "test-agent-1"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_federation.py -v`
Expected: FAIL (ModuleNotFoundError or ImportError)

**Step 3: Write minimal implementation**

Create `src/agentmesh/core/federation.py`:

```python
import time
from typing import List, Dict, Optional
from pydantic import BaseModel

from agentmesh.core.registry import AgentRegistry
from agentmesh.core.agent_card import AgentCard

class FederationUpdate(BaseModel):
    agents: List[AgentCard]
    peers: List[str] = []  # List of known peer endpoints
    timestamp: float

class FederationManager:
    def __init__(self, registry: AgentRegistry, seeds: List[str] = None):
        self.registry = registry
        self.seeds = seeds or []
        self.peers = set(self.seeds)

    async def get_local_updates(self, since_timestamp: float = 0) -> FederationUpdate:
        # For now, just return all agents. 
        # In real impl, we might filter by updated_at if registry supports it.
        # Assuming registry.list_agents() returns all.
        agents = await self.registry.list_agents()
        
        # Filter logic if registry doesn't support 'since' natively yet
        # (Assuming AgentCard has no updated_at yet, or we ignore for MVP)
        # We'll just return all for now as baseline.
        
        return FederationUpdate(
            agents=agents,
            peers=list(self.peers),
            timestamp=time.time()
        )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_federation.py -v`
Expected: PASS

**Step 5: Add Endpoint in Routes**

Modify `src/agentmesh/api/routes.py` (pseudo-code, adjust to actual file structure):

```python
# Add imports
from agentmesh.core.federation import FederationManager

# In initialization or dependency injection setup
# federation_manager = FederationManager(registry)

# Add route
@router.get("/federation/pull")
async def pull_updates(since: float = 0):
    return await federation_manager.get_local_updates(since)
```

**Step 6: Commit**

```bash
git add src/agentmesh/core/federation.py tests/test_federation.py src/agentmesh/api/routes.py
git commit -m "feat: add FederationManager and /federation/pull endpoint"
```

---

### Task 2: Sync from Seeds (Client Side)

**Files:**
- Modify: `src/agentmesh/core/federation.py`
- Modify: `src/agentmesh/core/registry.py` (if merge logic needed)
- Test: `tests/test_federation_sync.py`

**Step 1: Write the failing test**

Create `tests/test_federation_sync.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch
from agentmesh.core.federation import FederationManager
from agentmesh.core.registry import AgentRegistry
from agentmesh.core.agent_card import AgentCard

@pytest.mark.asyncio
async def test_sync_from_seeds():
    registry = AgentRegistry()
    federation = FederationManager(registry=registry, seeds=["http://seed-node:8000"])
    
    # Mock httpx response
    mock_agents = [
        AgentCard(
            id="remote-agent-1", 
            name="Remote Agent", 
            endpoint="http://remote:8000",
            public_key="pk2",
            manifest_signature="sig2"
        ).model_dump()
    ]
    
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "agents": mock_agents,
            "peers": ["http://other-peer:8000"],
            "timestamp": 1234567890.0
        }
        
        await federation.sync_from_seeds()
        
        # Verify agent was added to registry
        agents = await registry.list_agents()
        assert len(agents) == 1
        assert agents[0].id == "remote-agent-1"
        
        # Verify peers updated
        assert "http://other-peer:8000" in federation.peers
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_federation_sync.py -v`
Expected: FAIL (AttributeError: 'FederationManager' object has no attribute 'sync_from_seeds')

**Step 3: Write implementation**

Update `src/agentmesh/core/federation.py`:

```python
import httpx
import logging

logger = logging.getLogger(__name__)

class FederationManager:
    # ... existing __init__ ...
    
    async def sync_from_seeds(self):
        async with httpx.AsyncClient() as client:
            for seed in self.seeds:
                try:
                    # Append protocol if missing
                    if not seed.startswith("http"):
                        url = f"http://{seed}/federation/pull"
                    else:
                        url = f"{seed}/federation/pull"
                        
                    resp = await client.get(url, timeout=5.0)
                    if resp.status_code == 200:
                        data = resp.json()
                        await self._process_sync_data(data)
                except Exception as e:
                    logger.warning(f"Failed to sync from seed {seed}: {e}")

    async def _process_sync_data(self, data: Dict):
        # 1. Update peers
        remote_peers = data.get("peers", [])
        for p in remote_peers:
            self.peers.add(p)
            
        # 2. Merge agents
        agents_data = data.get("agents", [])
        for agent_dict in agents_data:
            try:
                # Parse as AgentCard
                card = AgentCard(**agent_dict)
                
                # Verify signature if required (registry handles this inside register_agent?)
                # We should probably use a special merge method or just register_agent
                # Note: register_agent typically overrides. 
                # For CRDT, we check timestamp, but AgentCard currently lacks updated_at in model.
                # MVP: Just overwrite.
                
                await self.registry.register_agent(card)
            except Exception as e:
                logger.warning(f"Failed to merge agent from sync: {e}")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_federation_sync.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/agentmesh/core/federation.py
git commit -m "feat: implement sync_from_seeds logic"
```

---

### Task 3: Background Sync Task Integration

**Files:**
- Modify: `src/agentmesh/main.py` (or where app is created)
- Test: `tests/test_app_lifecycle.py`

**Step 1: Write the failing test**

Create `tests/test_app_lifecycle.py` to verify startup event triggers sync loop (mocked).

```python
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from agentmesh.main import app  # Adjust import

def test_startup_sync_trigger():
    with patch("agentmesh.core.federation.FederationManager.sync_from_seeds") as mock_sync:
        with TestClient(app) as client:
            # Trigger startup
            pass
        # This is hard to test with TestClient for background tasks
        # Alternative: Verify background task is added to FastAPI app.state or similar
```

*Self-correction:* Testing background tasks in integration tests is tricky. Let's focus on unit testing the `start_background_sync` method we'll add to `FederationManager` and ensuring `main.py` calls it.

Revised Test `tests/test_background_sync.py`:

```python
import pytest
import asyncio
from agentmesh.core.federation import FederationManager
from agentmesh.core.registry import AgentRegistry

@pytest.mark.asyncio
async def test_background_loop():
    registry = AgentRegistry()
    federation = FederationManager(registry)
    
    # Mock sync_from_seeds to track calls
    federation.sync_from_seeds = AsyncMock()
    
    # Start loop task
    task = asyncio.create_task(federation.start_background_sync(interval=0.1))
    
    await asyncio.sleep(0.25)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
        
    assert federation.sync_from_seeds.call_count >= 2
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_background_sync.py -v`
Expected: FAIL (AttributeError)

**Step 3: Write implementation**

Update `src/agentmesh/core/federation.py`:

```python
class FederationManager:
    # ... existing ...
    
    async def start_background_sync(self, interval: float = 60.0):
        while True:
            try:
                await self.sync_from_seeds()
            except Exception as e:
                logger.error(f"Error in background sync: {e}")
            await asyncio.sleep(interval)
```

Update `src/agentmesh/main.py` to initialize and start it:

```python
# In startup event
@app.on_event("startup")
async def startup_event():
    # ... existing ...
    seeds = os.getenv("SEEDS", "").split(",")
    app.state.federation = FederationManager(app.state.registry, seeds=[s for s in seeds if s])
    asyncio.create_task(app.state.federation.start_background_sync())
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_background_sync.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/agentmesh/core/federation.py src/agentmesh/main.py
git commit -m "feat: add background sync task"
```
