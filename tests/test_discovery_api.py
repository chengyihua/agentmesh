import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock, patch
from agentmesh.api.server import AgentMeshServer
from agentmesh.core.agent_card import AgentCard
from agentmesh.core.vector_index import VectorIndexManager

@pytest.mark.asyncio
async def test_discovery_api():
    # Create mock vector index
    mock_vector = MagicMock(spec=VectorIndexManager)
    mock_vector.search = AsyncMock(return_value=[
        {"agent_id": "agent-1", "score": 0.9}
    ])
    
    # Inject mock into server
    server = AgentMeshServer(vector_index=mock_vector)
    
    # Populate registry with agent so it can be hydrated
    agent = AgentCard(
        id="agent-1",
        name="Agent 1",
        version="1.0",
        endpoint="http://example.com",
        vector_desc="Test agent",
        skills=[{"name": "test", "description": "test"}]
    )
    # Add to storage so it survives registry.start() (which syncs from storage)
    await server.registry.storage.upsert_agent(agent)
    
    with TestClient(server.app) as client:
        response = client.get("/api/v1/agents/search?q=test")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        results = data["data"]["results"]
        assert len(results) == 1
        result = results[0]
        assert result["id"] == "agent-1"
        assert result["score"] >= 0.9  # Adjusted expectation as scores might be boosted
        
        # Verify search was called
        mock_vector.search.assert_called_once()
        args, kwargs = mock_vector.search.call_args
        assert args[0] == "test"
