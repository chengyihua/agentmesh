
import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from agentmesh.client import AgentMeshClient
from agentmesh.core.agent_card import AgentCard, NetworkProfile
import httpx

@pytest.mark.asyncio
async def test_agent_join_flow_full():
    """
    Test the full 6-step agent join flow using AgentMeshClient.
    1. Initialization
    2. Network Detect (P2P Start)
    3. Relay Connect
    4. Registry Registration (with retry/update)
    5. Health Monitoring (Heartbeat)
    """
    
    # Mock configuration
    agent_id = "test-agent-join"
    # Valid base64 encoded 32-byte key
    private_key = "MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIzNDU2Nzg5MDE="
    base_url = "http://localhost:8000"
    relay_url = "ws://relay.example.com"
    
    # Mock P2P Node behavior
    with patch("agentmesh.p2p.node.P2PNode") as MockP2PNode:
        mock_p2p = AsyncMock()
        # Fix: close() is synchronous in P2PNode, so mock it as such to avoid "coroutine not awaited" warning
        mock_p2p.close = MagicMock()
        MockP2PNode.return_value = mock_p2p
        mock_p2p.start.return_value = None
        mock_p2p.nat_type = "full_cone"
        mock_p2p.public_endpoint = ("1.2.3.4", 12345)
        mock_p2p.local_endpoints = ["192.168.1.10:12345"]
        
        # Mock Relay Client behavior
        with patch("agentmesh.relay.client.RelayClient") as MockRelayClient:
            mock_relay = AsyncMock()
            MockRelayClient.return_value = mock_relay
            mock_relay.connect.return_value = None
            
            # Mock HTTP Client behavior
            with patch("httpx.AsyncClient") as MockHttpClient:
                mock_http = AsyncMock()
                MockHttpClient.return_value = mock_http
                
                # Mock responses
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"status": "success"}
                mock_response.raise_for_status = MagicMock()
                mock_http.request.return_value = mock_response
                
                async with AgentMeshClient(
                    base_url=base_url,
                    agent_id=agent_id,
                    private_key=private_key
                ) as client:
                    
                    # --- Step 2: Network Detect ---
                    p2p_profile = await client.start_p2p(port=12345, update_registry=False)
                    
                    assert p2p_profile["nat_type"] == "full_cone"
                    assert "1.2.3.4:12345" in p2p_profile["public_endpoints"]
                    assert "192.168.1.10:12345" in p2p_profile["local_endpoints"]
                    
                    # --- Step 3: Connect Relay ---
                    # First, ensure relay client works
                    success = await client.connect_relay(relay_url, update_registry=False)
                    assert success is True
                    p2p_profile["relay_endpoint"] = relay_url
                    
                    # --- Step 4: Register with Retry ---
                    # Simulate "Agent already exists" first to test update fallback
                    mock_http.request.side_effect = [
                        httpx.HTTPStatusError(
                            "400 Bad Request", 
                            request=MagicMock(), 
                            response=MagicMock(status_code=400, text="Agent already exists")
                        ),
                        MagicMock(status_code=200, json=lambda: {"status": "updated"})
                    ]
                    
                    agent_card_data = {
                        "id": agent_id,
                        "name": "Test Agent",
                        "skills": [{"name": "test-skill", "type": "service", "description": "Test"}],
                        "endpoint": "http://localhost:8000",
                        "network_profile": p2p_profile
                    }
                    
                    # This should catch the 400 and call update_agent
                    result = await client.register_or_update_agent_with_retry(agent_card_data)
                    
                    assert result == {"status": "updated"}
                    
                    # Verify calls
                    # 1. register_agent (failed)
                    # 2. update_agent (success)
                    assert mock_http.request.call_count == 2
                    calls = mock_http.request.call_args_list
                    assert calls[0][0][0] == "POST" # Register
                    assert calls[1][0][0] == "PUT"  # Update
                    
                    # --- Step 5: Health Monitoring ---
                    # Simulate heartbeat
                    # Reset mock for heartbeat
                    mock_http.request.side_effect = None
                    mock_http.request.return_value.status_code = 200
                    mock_http.request.return_value.json.return_value = {"status": "healthy"}
                    
                    # Send manual heartbeat
                    # Assuming send_heartbeat(agent_id) exists
                    await client.send_heartbeat(agent_id)
                    
                    assert mock_http.request.call_count == 3
                    calls = mock_http.request.call_args_list
                    # Check that the 3rd call was a POST to /heartbeat
                    assert calls[2][0][0] == "POST"
                    assert f"/api/v1/agents/{agent_id}/heartbeat" in calls[2][0][1]

@pytest.mark.asyncio
async def test_retry_logic_failure():
    """Test retry logic when registration fails repeatedly."""
    with patch("httpx.AsyncClient") as MockHttpClient:
        mock_http = AsyncMock()
        MockHttpClient.return_value = mock_http
        
        # Always fail
        mock_http.request.side_effect = Exception("Network Error")
        
        async with AgentMeshClient(agent_id="test") as client:
            with pytest.raises(Exception, match="Network Error"):
                # Use small delay to speed up test
                await client.register_or_update_agent_with_retry(
                    {"id": "test"}, 
                    max_retries=2, 
                    base_delay=0.01
                )
