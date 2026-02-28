import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from agentmesh.core.federation import FederationManager
from agentmesh.core.registry import AgentRegistry

@pytest.mark.asyncio
async def test_sync_from_discovered_peers():
    registry = AgentRegistry()
    # Initial seed
    federation = FederationManager(registry=registry, seeds=["seed1:8000"])
    
    # Add a discovered peer manually to simulate previous sync
    federation.peers.add("peer2:8000")
    
    # Mock httpx client
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"agents": [], "peers": []}
    mock_client.get.return_value = mock_resp
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        await federation.sync_from_seeds()
        
        # Verify calls were made to BOTH seed1 and peer2
        # Note: Order is not guaranteed in set iteration, but both should be called
        calls = [c[0][0] for c in mock_client.get.call_args_list]
        assert any("seed1:8000" in url for url in calls)
        assert any("peer2:8000" in url for url in calls)
        assert len(calls) == 2

@pytest.mark.asyncio
async def test_sync_filters_invalid_peers():
    # Optional: Test that we handle empty peers or connection errors gracefully
    registry = AgentRegistry()
    federation = FederationManager(registry=registry, seeds=["seed1:8000"])
    
    # Mock client to raise error for one peer
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    
    def side_effect(url, **kwargs):
        if "seed1" in url:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"agents": [], "peers": ["new-peer:8000"]}
            return mock_resp
        raise Exception("Connection failed")
        
    mock_client.get.side_effect = side_effect
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        await federation.sync_from_seeds()
        
        # Should catch exception and continue
        # And should have processed seed1 response
        assert "new-peer:8000" in federation.peers
