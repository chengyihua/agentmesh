import pytest
import asyncio
from datetime import datetime, timezone
from agentmesh.core.discovery import DiscoveryService
from agentmesh.core.agent_card import AgentCard

@pytest.mark.asyncio
async def test_discovery_indexing():
    service = DiscoveryService()
    agent = AgentCard(
        id="test-1", 
        name="Test Agent", 
        version="1.0.0",
        endpoint="http://localhost", 
        skills=[{"name": "python", "description": "coding"}],
        tags=["dev", "ai"],
        protocol="http"
    )
    
    service.update_indexes("test-1", agent)
    
    assert "test-1" in service.skill_index["python"]
    assert "test-1" in service.tag_index["dev"]
    assert "test-1" in service.protocol_index["http"]
    
    service.remove_from_indexes("test-1", agent)
    
    assert "python" not in service.skill_index
    assert "dev" not in service.tag_index

@pytest.mark.asyncio
async def test_discovery_candidates():
    service = DiscoveryService()
    agent1 = AgentCard(id="a1", name="A1", version="1.0.0", endpoint="e1", skills=[{"name": "s1", "description": "d"}], tags=["t1"])
    agent2 = AgentCard(id="a2", name="A2", version="1.0.0", endpoint="e2", skills=[{"name": "s1", "description": "d"}], tags=["t2"])
    
    agents = {"a1": agent1, "a2": agent2}
    service.update_indexes("a1", agent1)
    service.update_indexes("a2", agent2)
    
    # Search by skill
    candidates = await service.get_candidates(agents, skill_name="s1")
    assert candidates == {"a1", "a2"}
    
    # Search by tag
    candidates = await service.get_candidates(agents, tags=["t1"])
    assert candidates == {"a1"}
    
    # Search by query (no filter)
    candidates = await service.get_candidates(agents, q="whatever")
    assert candidates == {"a1", "a2"}

@pytest.mark.asyncio
async def test_search_score():
    service = DiscoveryService()
    agent = AgentCard(id="a1", name="Python Agent", version="1.0.0", endpoint="e1", skills=[{"name": "coding", "description": "writes python code"}])
    
    score, fields = await service.search_score(agent, "python", trust_score=1.0)
    assert score > 0
    assert "name" in fields or "skills" in fields # "python" is in name and description of skill
