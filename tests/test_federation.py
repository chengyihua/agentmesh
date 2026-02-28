import pytest
from unittest.mock import AsyncMock, MagicMock
from agentmesh.core.federation import FederationManager
from agentmesh.core.registry import AgentRegistry
from agentmesh.core.agent_card import AgentCard

@pytest.mark.asyncio
async def test_federation_pull_local_registry():
    # Setup registry with one agent
    registry = AgentRegistry(require_signed_registration=False)
    agent = AgentCard(
        id="test-agent-1",
        name="Test Agent",
        version="1.0.0",
        endpoint="http://localhost:8000",
        skills=[{"name": "test", "description": "test"}]
    )
    await registry.register_agent(agent)
    
    # Initialize FederationManager
    federation = FederationManager(registry=registry)
    
    # Test get_local_updates (what /pull endpoint calls)
    updates = await federation.get_local_updates(since_timestamp=0)
    
    assert len(updates.agents) == 1
    assert updates.agents[0].id == "test-agent-1"
