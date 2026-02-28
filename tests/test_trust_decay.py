
import asyncio
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from agentmesh.core.trust import TrustManager, TrustEvent
from agentmesh.core.agent_card import AgentCard, HealthStatus
from agentmesh.core.registry import AgentRegistry

@pytest.fixture
def registry():
    return AgentRegistry()

@pytest.fixture
def trust_manager(registry):
    return TrustManager(registry)

@pytest.mark.asyncio
async def test_trust_decay_on_read(registry, trust_manager):
    # Setup agent
    agent = AgentCard(
        id="decay-agent",
        name="Decay Agent",
        version="1.0.0",
        description="Test agent for trust decay",
        endpoint="http://localhost:8000",
        skills=[{"name": "test", "description": "test"}]
    )
    
    # Register first (sets created_at/updated_at to now)
    await registry.register_agent(agent)
    
    # Manually set trust score and updated_at to the past
    # 125 seconds ago = 2 intervals (60s each)
    past_time = datetime.now(timezone.utc) - timedelta(seconds=125)
    
    # We need to update the agent in memory/storage
    # Access agent from registry to ensure we modify the same object instance
    stored_agent = await registry.get_agent(agent.id)
    stored_agent.trust_score = 0.9
    stored_agent.updated_at = past_time
    
    # Ensure trust manager doesn't have it in cache yet
    if agent.id in trust_manager.scores:
        del trust_manager.scores[agent.id]
        
    # Calculate expected decay
    # current = 0.9
    # target = 0.5
    # factor = 0.01
    # intervals = 2
    # formula: target + (current - target) * (1 - factor)^intervals
    # 0.5 + (0.4) * (0.99)^2 = 0.5 + 0.4 * 0.9801 = 0.5 + 0.39204 = 0.89204
    
    decayed_score = await trust_manager.get_score(agent.id)
    
    # Allow small timing differences (seconds_elapsed might be slightly more than 125)
    assert decayed_score < 0.9
    # It should be around 0.892
    assert 0.89 <= decayed_score <= 0.893
    
    # Verify it updated the memory
    assert trust_manager.scores[agent.id] == decayed_score

@pytest.mark.asyncio
async def test_decay_loop(registry, trust_manager):
    # Setup agent
    agent_id = "loop-agent"
    trust_manager.scores[agent_id] = 0.8
    
    # Reduce decay interval for test
    trust_manager.decay_interval = 0.1
    
    # Start manager
    await trust_manager.start()
    
    try:
        # Wait for a few cycles
        await asyncio.sleep(0.3)
        
        # Score should have decayed
        current_score = trust_manager.scores[agent_id]
        assert current_score < 0.8
        assert current_score > 0.5
        
    finally:
        await trust_manager.stop()
