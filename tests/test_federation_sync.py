import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from agentmesh.core.federation import FederationManager
from agentmesh.core.registry import AgentRegistry
from agentmesh.core.agent_card import AgentCard

@pytest.mark.asyncio
async def test_sync_from_seeds():
    registry = AgentRegistry(require_signed_registration=False)
    federation = FederationManager(registry=registry, seeds=["http://seed-node:8000"])
    
    # Mock httpx response
    mock_agents = [
        AgentCard(
            id="remote-agent-1", 
            name="Remote Agent", 
            version="1.0.0",
            endpoint="http://remote:8000",
            skills=[{"name": "test", "description": "test"}]
        ).model_dump()
    ]
    
    # Create a mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "agents": mock_agents,
        "peers": ["http://other-peer:8000"],
        "timestamp": 1234567890.0
    }

    # Mock client instance
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    # Patch AsyncClient to return our mock_client
    with patch("httpx.AsyncClient", return_value=mock_client):
        await federation.sync_from_seeds()
        
        # Verify agent was added to registry
        agents = registry.agents
        assert len(agents) == 1
        assert agents["remote-agent-1"].id == "remote-agent-1"
        
        # Verify peers updated
        assert "http://other-peer:8000" in federation.peers
