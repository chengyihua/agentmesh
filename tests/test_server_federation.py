import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from agentmesh.api.server import AgentMeshServer

@pytest.mark.asyncio
async def test_server_starts_federation_sync():
    # Patch FederationManager class to return our mock
    with patch("agentmesh.api.server.FederationManager") as MockFederationClass:
        mock_instance = MockFederationClass.return_value
        mock_instance.start_background_sync = AsyncMock()
        
        seeds = ["http://seed:8000"]
        server = AgentMeshServer(seeds=seeds)
        
        # Verify federation manager was initialized with seeds
        assert MockFederationClass.call_count == 1
        _, kwargs = MockFederationClass.call_args
        assert kwargs["seeds"] == seeds
        assert server.federation == mock_instance
        
        # Test lifespan context manager
        app = server.app
        
        # Use TestClient as context manager to trigger lifespan
        with TestClient(app) as client:
            # Check if start_background_sync was called
            mock_instance.start_background_sync.assert_called_once()
            
            # Verify app state has federation
            assert client.app.state.federation == mock_instance

