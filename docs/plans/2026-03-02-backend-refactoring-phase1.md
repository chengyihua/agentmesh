# Backend Refactoring Phase 1: Core Services Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor the monolithic `AgentRegistry` into specialized services (`HealthMonitor`, `TrustEngine`, `DiscoveryService`) to improve maintainability and testability.

**Architecture:**
- `AgentRegistry` remains the entry point for Agent CRUD but delegates specific logic.
- `HealthMonitor` handles heartbeats and background health checks.
- `TrustEngine` encapsulates trust scoring logic (moving implementation details out of Registry).
- `DiscoveryService` manages search indexes (skills, tags, protocols) and vector search integration.

**Tech Stack:** Python, asyncio, Pydantic

---

### Task 1: Create HealthMonitor Service

**Files:**
- Create: `src/agentmesh/core/health.py`
- Modify: `src/agentmesh/core/registry.py`
- Test: `tests/test_health_monitor.py`

**Step 1: Define HealthMonitor Class**

Create `src/agentmesh/core/health.py`:
```python
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from .agent_card import AgentCard, HealthStatus
from .storage import StorageBackend

logger = logging.getLogger(__name__)

class HealthMonitor:
    def __init__(self, storage: StorageBackend):
        self.storage = storage
        self.health_check_interval = 30
        self.max_unhealthy_time = 300
        self._check_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self, agents: Dict[str, AgentCard]):
        self._running = True
        self._check_task = asyncio.create_task(self._loop(agents))
        logger.info("HealthMonitor started")

    async def stop(self):
        self._running = False
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass

    async def record_heartbeat(self, agent: AgentCard, status: HealthStatus, timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        now = timestamp or datetime.now(timezone.utc)
        agent.health_status = status
        agent.last_health_check = now
        agent.last_heartbeat = now
        agent.updated_at = now
        
        # Persist changes
        await self.storage.upsert_agent(agent)
        
        return {
            "agent_id": agent.id,
            "status": status.value,
            "timestamp": now.isoformat(),
            "next_check": (now + timedelta(seconds=self.health_check_interval)).isoformat()
        }

    async def check_agent(self, agent: AgentCard) -> HealthStatus:
        if agent.last_health_check:
            delta = datetime.now(timezone.utc) - agent.last_health_check.astimezone(timezone.utc)
            if delta.total_seconds() > self.max_unhealthy_time:
                agent.set_health_status(HealthStatus.UNHEALTHY) # Or OFFLINE based on logic
                await self.storage.upsert_agent(agent)
        return agent.health_status

    async def _loop(self, agents: Dict[str, AgentCard]):
        while self._running:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._perform_checks(agents)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")

    async def _perform_checks(self, agents: Dict[str, AgentCard]):
        now = datetime.now(timezone.utc)
        for agent in agents.values():
            if not agent.last_health_check:
                continue
            delta = now - agent.last_health_check.astimezone(timezone.utc)
            if delta.total_seconds() > self.max_unhealthy_time:
                if agent.health_status != HealthStatus.OFFLINE:
                    agent.set_health_status(HealthStatus.OFFLINE)
                    await self.storage.upsert_agent(agent)
                    logger.warning(f"Agent {agent.id} marked OFFLINE")
```

**Step 2: Create Test for HealthMonitor**

Create `tests/test_health_monitor.py`:
```python
import pytest
import asyncio
from datetime import datetime, timezone
from src.agentmesh.core.health import HealthMonitor, HealthStatus
from src.agentmesh.core.agent_card import AgentCard
from src.agentmesh.storage.memory import MemoryStorage

@pytest.mark.asyncio
async def test_heartbeat_update():
    storage = MemoryStorage()
    monitor = HealthMonitor(storage)
    agent = AgentCard(id="test-1", name="Test", endpoint="http://localhost")
    
    await monitor.record_heartbeat(agent, HealthStatus.HEALTHY)
    
    assert agent.health_status == HealthStatus.HEALTHY
    assert agent.last_heartbeat is not None
    
    stored = await storage.get_agent("test-1")
    assert stored.last_heartbeat == agent.last_heartbeat
```

**Step 3: Integrate HealthMonitor into Registry**

Modify `src/agentmesh/core/registry.py`:
- Initialize `self.health_monitor = HealthMonitor(self.storage)` in `__init__`.
- Delegate `heartbeat`, `check_agent_health`, `batch_health_check` to `self.health_monitor`.
- Start/Stop `health_monitor` in `start()`/`stop()`.
- Remove old health check loop code from Registry.

### Task 2: Create DiscoveryService

**Files:**
- Create: `src/agentmesh/core/discovery.py`
- Modify: `src/agentmesh/core/registry.py`
- Test: `tests/test_discovery_service.py`

**Step 1: Define DiscoveryService Class**

Create `src/agentmesh/core/discovery.py`:
```python
import logging
from typing import Dict, List, Optional, Set, Any
from .agent_card import AgentCard, HealthStatus
from .vector_index import VectorIndexManager

logger = logging.getLogger(__name__)

class DiscoveryService:
    def __init__(self, vector_index: Optional[VectorIndexManager] = None):
        self.vector_index = vector_index
        self.skill_index: Dict[str, Set[str]] = {}
        self.protocol_index: Dict[str, Set[str]] = {}
        self.tag_index: Dict[str, Set[str]] = {}
        self._search_cache: Dict[str, List[Any]] = {}

    def update_indexes(self, agent: AgentCard):
        # Implementation from Registry._update_indexes
        pass

    def remove_from_indexes(self, agent: AgentCard):
        # Implementation from Registry._remove_from_indexes
        pass

    async def search(self, agents: Dict[str, AgentCard], query: Optional[str], **filters) -> List[AgentCard]:
        # Implementation from Registry.discover_agents + search_agents
        # Logic to filter by indexes and then rank
        pass
```

**Step 2: Migrate Index Logic**
- Move `_update_indexes`, `_remove_from_indexes`, `_search_score` logic from `Registry` to `DiscoveryService`.

**Step 3: Integrate DiscoveryService into Registry**
- Initialize `self.discovery = DiscoveryService(self.vector_index)` in `__init__`.
- Delegate `register_agent` index updates to `discovery.update_indexes`.
- Delegate `discover_agents` and `search_agents` calls to `discovery.search`.

### Task 3: Cleanup and Verification

**Files:**
- Modify: `src/agentmesh/core/registry.py`

**Step 1: Remove Redundant Code**
- Remove `_health_check_loop`, `_perform_health_checks` from Registry.
- Remove index dictionaries (`self.skill_index`, etc.) from Registry.
- Remove search logic methods from Registry.

**Step 2: Verify All Tests Pass**
- Run `pytest tests/` to ensure no regression in functionality.
