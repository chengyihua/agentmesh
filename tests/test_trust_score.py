
import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from agentmesh.core.trust import TrustManager, TrustEvent
from agentmesh.core.registry import AgentRegistry
from agentmesh.core.agent_card import AgentCard, HealthStatus

@pytest.fixture
def mock_registry():
    registry = AsyncMock(spec=AgentRegistry)
    registry.agents = {}
    # Default get_agent to return None (simulating agent not found in storage/registry)
    registry.get_agent.return_value = None
    return registry

@pytest.fixture
async def trust_manager(mock_registry):
    manager = TrustManager(mock_registry)
    await manager.start()
    yield manager
    await manager.stop()

@pytest.mark.asyncio
async def test_initial_score(trust_manager):
    score = await trust_manager.get_score("new_agent")
    assert score == 0.5

@pytest.mark.asyncio
async def test_score_updates(trust_manager):
    agent_id = "test_agent"
    
    # Initial score
    assert await trust_manager.get_score(agent_id) == 0.5
    
    # Success event (+0.05)
    await trust_manager.record_event(agent_id, TrustEvent.SUCCESS)
    score = await trust_manager.get_score(agent_id)
    assert score == 0.55
    
    # Failure event (-0.10)
    await trust_manager.record_event(agent_id, TrustEvent.FAILURE)
    score = await trust_manager.get_score(agent_id)
    assert abs(score - 0.45) < 0.0001
    
    # Bad Signature (-0.20)
    await trust_manager.record_event(agent_id, TrustEvent.BAD_SIGNATURE)
    score = await trust_manager.get_score(agent_id)
    assert abs(score - 0.25) < 0.0001
    
    # Rate Limit (-0.02)
    await trust_manager.record_event(agent_id, TrustEvent.RATE_LIMIT)
    score = await trust_manager.get_score(agent_id)
    assert abs(score - 0.23) < 0.0001
    
    # Heartbeat (+0.00001)
    await trust_manager.record_event(agent_id, TrustEvent.HEARTBEAT)
    score = await trust_manager.get_score(agent_id)
    assert abs(score - 0.23001) < 0.0001

@pytest.mark.asyncio
async def test_score_clamping(trust_manager):
    agent_id = "test_agent"
    
    # Max score clamping
    for _ in range(100):
        await trust_manager.record_event(agent_id, TrustEvent.SUCCESS)
    
    score = await trust_manager.get_score(agent_id)
    assert score <= 1.0
    
    # Min score clamping
    for _ in range(50):
        await trust_manager.record_event(agent_id, TrustEvent.BAD_SIGNATURE)
        
    score = await trust_manager.get_score(agent_id)
    assert score >= 0.0

@pytest.mark.asyncio
async def test_score_decay_on_read(trust_manager, mock_registry):
    agent_id = "inactive_agent"
    
    # Create an agent with an old updated_at (2 minutes ago)
    # decay_interval is 60s, so it should decay twice
    old_time = datetime.now(timezone.utc) - timedelta(seconds=130)
    agent = AgentCard(
        id=agent_id,
        name="Inactive",
        version="1.0",
        endpoint="http://x",
        skills=[{"name": "s", "description": "d"}],
        trust_score=0.8,
        updated_at=old_time
    )
    
    mock_registry.get_agent.return_value = agent
    
    # First read should trigger decay
    score = await trust_manager.get_score(agent_id)
    
    # Expected: 0.8 decays towards 0.5 twice
    # decay_factor = 0.01
    # decayed = 0.5 + (0.8 - 0.5) * ((1 - 0.01) ** 2)
    # decayed = 0.5 + 0.3 * (0.99 ** 2)
    # decayed = 0.5 + 0.3 * 0.9801 = 0.79403
    
    assert score < 0.8
    assert abs(score - 0.79403) < 0.001
    
    # Check that it's now in active memory
    assert agent_id in trust_manager.scores

@pytest.mark.asyncio
async def test_integration_registry():
    # Test TrustManager integrated within Registry
    registry = AgentRegistry(storage=AsyncMock())
    # Mock storage methods to avoid actual DB calls or errors
    registry.storage.connect = AsyncMock()
    registry.storage.upsert_agent = AsyncMock()
    registry.storage.list_agents = AsyncMock(return_value=[])
    registry.storage.get_agent = AsyncMock(return_value=None)
    
    await registry.start()
    
    try:
        agent_id = "agent_1"
        agent = AgentCard(
            id=agent_id,
            name="Test Agent",
            version="1.0.0",
            endpoint="http://localhost:8000",
            skills=[{"name": "test", "type": "tool", "description": "test skill"}]
        )
        # Register manually or just inject
    finally:
        await registry.stop()
