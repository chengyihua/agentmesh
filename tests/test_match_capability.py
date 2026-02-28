import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from agentmesh.core.registry import AgentRegistry
from agentmesh.core.agent_card import AgentCard
from agentmesh.core.trust import TrustManager

@pytest.mark.asyncio
async def test_match_capability_structure():
    # Setup Registry
    registry = AgentRegistry()
    registry.storage = AsyncMock()
    registry.storage.list_agents.return_value = []
    
    # Mock trust manager to avoid errors
    registry.trust_manager = MagicMock(spec=TrustManager)
    registry.trust_manager.get_score.return_value = 0.5
    
    # Create a dummy agent
    agent_id = "agent_match_test"
    agent = AgentCard(
        id=agent_id,
        name="Match Test Agent",
        description="A test agent for matching capabilities",
        version="1.0.0",
        skills=[{"name": "test_match", "description": "A test skill"}],
        endpoint="http://localhost:8000",
        trust_score=0.8
    )
    
    # Manually add agent to registry
    registry.agents[agent_id] = agent
    
    # Mock search_agents to return this agent
    registry.search_agents = AsyncMock(return_value=[
        {
            "id": agent_id,
            "name": agent.name,
            "description": agent.description,
            "score": 0.95,
            "matched_fields": ["description"],
            "vector_score": 0.9,
            "keyword_score": 1.0
        }
    ])
    
    # Call match_capability
    result = await registry.match_capability("test")
    
    # Verify structure matches protocol doc
    assert result is not None
    assert "agent" in result
    assert "score" in result
    assert "reason" in result
    
    agent_data = result["agent"]
    assert agent_data["id"] == agent_id
    assert agent_data["name"] == agent.name
    assert agent_data["endpoint"] == str(agent.endpoint)
    assert agent_data["protocol"] == str(agent.protocol.value)
    
    assert result["score"] == 0.95
    assert "Matches query 'test'" in result["reason"]

