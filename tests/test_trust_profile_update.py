
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from agentmesh.core.registry import AgentRegistry
from agentmesh.core.trust import TrustManager, TrustEvent
from agentmesh.core.agent_card import AgentCard, AgentCardUpdate

@pytest.mark.asyncio
async def test_trust_score_profile_update():
    # Setup Registry and TrustManager
    registry = AgentRegistry()
    registry.storage = AsyncMock()
    registry.storage.list_agents.return_value = []
    registry.storage.upsert_agent = AsyncMock()
    
    # Initialize TrustManager (it's created in Registry __init__ but we want to ensure it's started/mocked if needed)
    # Actually Registry creates it: self.trust_manager = TrustManager(self)
    
    # Create a dummy agent
    agent_id = "agent_123"
    agent = AgentCard(
        id=agent_id,
        name="Test Agent",
        description="A test agent",
        version="1.0.0",
        skills=[{"name": "test_skill", "description": "A test skill"}],
         endpoint="http://localhost:8000",
         trust_score=0.5
     )
    
    # Manually add agent to registry to bypass registration logic for this test
    registry.agents[agent_id] = agent
    
    # Get initial score
    initial_score = registry.trust_manager.scores.get(agent_id, 0.5)
    assert initial_score == 0.5
    
    # Perform Update
    update_data = AgentCardUpdate(description="Updated description")
    await registry.update_agent(agent_id, update_data)
    
    # Check if Trust Event was recorded
    # We can check the internal state of trust_manager
    
    # The trust manager updates scores in memory
    new_score = registry.trust_manager.scores.get(agent_id)
    
    # Expected: 0.5 + 0.05 = 0.55
    # Allow for floating point differences
    assert new_score is not None
    assert abs(new_score - 0.55) < 0.0001
    
    # Check event counts
    counts = registry.trust_manager.event_counts.get(agent_id, {})
    assert counts.get(TrustEvent.PROFILE_UPDATE) == 1

