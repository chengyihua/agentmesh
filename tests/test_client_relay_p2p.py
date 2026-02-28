
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from agentmesh.client import AgentMeshClient

@pytest.mark.asyncio
async def test_connect_relay_success():
    # Mock RelayClient
    with patch("agentmesh.relay.client.RelayClient") as MockRelayClient:
        mock_relay_instance = AsyncMock()
        MockRelayClient.return_value = mock_relay_instance
        # Mock connect to return a future that is not done? Or just awaitable.
        mock_relay_instance.connect = AsyncMock()
        
        client = AgentMeshClient(agent_id="agent-1", private_key="key")
        client.update_agent = AsyncMock()
        
        success = await client.connect_relay("ws://relay:8000", update_registry=True)
        
        assert success is True
        assert client.relay_client is mock_relay_instance
        # Check if connect was called
        mock_relay_instance.connect.assert_called()
        # Check if registry update was called
        client.update_agent.assert_called_with("agent-1", {
            "network_profile": {"relay_endpoint": "ws://relay:8000"}
        })

@pytest.mark.asyncio
async def test_handle_relay_request_handshake():
    client = AgentMeshClient(agent_id="agent-1", private_key="key")
    client.p2p_node = MagicMock()
    client.p2p_node.connect_to_peer = AsyncMock() # Use AsyncMock for coroutine
    
    # Simulate handshake payload
    payload = {
        "skill": "sys.p2p.handshake",
        "payload": {
            "endpoint": "1.2.3.4:5678",
            "peer_id": "peer-1"
        }
    }
    
    response = await client._handle_relay_request(payload)
    
    assert response["status"] == "success"
    assert "punching started" in response["message"]
    
    # Check if connect_to_peer was called
    # Since it's run in background task, we might need to wait or check if task was created.
    # But in the code: asyncio.create_task(self.p2p_node.connect_to_peer(ip, port))
    # Mocking asyncio.create_task is hard.
    # Instead, we can inspect if the coroutine was created?
    # Or just mock p2p_node.connect_to_peer to be a coroutine.
    
    # Actually, asyncio.create_task schedules it.
    # We can't easily assert it ran unless we run the loop.
    # But we can assert connect_to_peer was called (to create the coroutine).
    client.p2p_node.connect_to_peer.assert_called_with("1.2.3.4", 5678)

@pytest.mark.asyncio
async def test_handle_relay_request_other():
    client = AgentMeshClient(agent_id="agent-1", private_key="key")
    
    # User handler
    async def user_handler(payload):
        return {"status": "handled", "data": payload["data"]}
        
    client._user_relay_handler = user_handler
    
    payload = {
        "skill": "other",
        "data": "test"
    }
    
    response = await client._handle_relay_request(payload)
    
    assert response["status"] == "handled"
    assert response["data"] == "test"
