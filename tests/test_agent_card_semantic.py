import pytest
from agentmesh.core.agent_card import AgentCard

def test_agent_card_vector_fields():
    card = AgentCard(
        id="test-1",
        name="Test",
        version="1.0",
        endpoint="http://localhost",
        skills=[{"name": "test", "description": "test"}],
        vector_desc="A test agent for vector search",
        capabilities=["search", "vector"]
    )
    assert card.vector_desc == "A test agent for vector search"
    assert "search" in card.capabilities
