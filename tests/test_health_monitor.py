import pytest
import asyncio
from datetime import datetime, timezone
from agentmesh.core.health import HealthMonitor, HealthStatus
from agentmesh.core.agent_card import AgentCard
from agentmesh.storage.memory import MemoryStorage

@pytest.mark.asyncio
async def test_heartbeat_update():
    storage = MemoryStorage()
    monitor = HealthMonitor(storage)
    agent = AgentCard(id="test-1", name="Test", version="1.0.0", endpoint="http://localhost", skills=[{"name": "test", "description": "test"}])
    
    await monitor.record_heartbeat(agent, HealthStatus.HEALTHY)
    
    assert agent.health_status == HealthStatus.HEALTHY
    assert agent.last_heartbeat is not None
    
    stored = await storage.get_agent("test-1")
    assert stored.last_heartbeat == agent.last_heartbeat

@pytest.mark.asyncio
async def test_health_check_loop():
    storage = MemoryStorage()
    monitor = HealthMonitor(storage)
    monitor.health_check_interval = 0.1 # fast check
    monitor.max_unhealthy_time = 0.2
    
    agent = AgentCard(id="test-2", name="Test2", version="1.0.0", endpoint="http://localhost", skills=[{"name": "test", "description": "test"}])
    agent.last_health_check = datetime.now(timezone.utc)
    agents = {"test-2": agent}
    
    await monitor.start(agents)
    await asyncio.sleep(0.5) # wait for check
    
    assert agent.health_status == HealthStatus.OFFLINE
    await monitor.stop()
