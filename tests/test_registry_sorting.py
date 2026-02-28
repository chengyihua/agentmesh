import pytest
import asyncio
from datetime import datetime, timedelta
from agentmesh.core.registry import AgentRegistry
from agentmesh.core.agent_card import AgentCard, HealthStatus

@pytest.mark.asyncio
async def test_list_agents_sorting():
    registry = AgentRegistry()
    
    # Create 3 agents with different trust scores
    skill = {"name": "test", "description": "test"}
    agent1 = AgentCard(id="agent1", name="A1", version="1.0", endpoint="http://a1", trust_score=0.1, skills=[skill])
    agent2 = AgentCard(id="agent2", name="A2", version="1.0", endpoint="http://a2", trust_score=0.9, skills=[skill])
    agent3 = AgentCard(id="agent3", name="A3", version="1.0", endpoint="http://a3", trust_score=0.5, skills=[skill])
    
    # Manually inject agents
    registry.agents = {
        "agent1": agent1,
        "agent2": agent2,
        "agent3": agent3,
    }
    
    # Mock calculate_trust_score
    async def mock_calculate_trust(agent_id):
        if agent_id == "agent1": return 0.1
        if agent_id == "agent2": return 0.9
        if agent_id == "agent3": return 0.5
        return 0.0
        
    registry.calculate_trust_score = mock_calculate_trust
    
    # Test sort by trust_score desc (default)
    # Note: list_agents might not accept sort_by yet, so this should fail
    agents = await registry.list_agents(sort_by="trust_score", order="desc")
    assert agents[0].id == "agent2"
    assert agents[1].id == "agent3"
    assert agents[2].id == "agent1"
    
    # Test sort by trust_score asc
    agents = await registry.list_agents(sort_by="trust_score", order="asc")
    assert agents[0].id == "agent1"
    assert agents[1].id == "agent3"
    assert agents[2].id == "agent2"
