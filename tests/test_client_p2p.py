import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from agentmesh.client import AgentMeshClient

@pytest.mark.asyncio
async def test_client_start_p2p():
    client = AgentMeshClient()
    
    # Mock P2PNode
    with patch("agentmesh.p2p.node.P2PNode") as MockNode:
        mock_node_instance = AsyncMock()
        # Set synchronous methods
        mock_node_instance.send_message = MagicMock()
        mock_node_instance.close = MagicMock()
        
        mock_node_instance.nat_type = "full_cone"
        mock_node_instance.public_endpoint = ("1.2.3.4", 9999)
        MockNode.return_value = mock_node_instance
        
        # Test with callback
        async def on_request(payload, addr):
            return {"result": "ok"}
            
        profile = await client.start_p2p(on_request=on_request)
        
        assert profile["nat_type"] == "full_cone"
        assert profile["public_endpoints"] == ["1.2.3.4:9999"]
        
        MockNode.assert_called_with(port=0, on_request=on_request)
        mock_node_instance.start.assert_awaited_once()
        
        await client.close()

@pytest.mark.asyncio
async def test_client_invoke_p2p_explicit():
    client = AgentMeshClient()
    
    with patch("agentmesh.p2p.node.P2PNode") as MockNode:
        mock_node_instance = AsyncMock()
        mock_node_instance.send_request = AsyncMock(return_value={"status": "ok"})
        mock_node_instance.close = MagicMock()
        MockNode.return_value = mock_node_instance
        
        await client.start_p2p()
        
        # Mock get_agent response
        client.get_agent = AsyncMock(return_value={
            "id": "target-agent",
            "network_profile": {
                "public_endpoints": ["5.6.7.8:8888"],
                "nat_type": "full_cone"
            }
        })
        
        result = await client.invoke_agent_p2p("target-agent", {"msg": "hello"})
        
        assert result["status"] == "ok"
        
        mock_node_instance.connect_to_peer.assert_awaited_with("5.6.7.8", 8888)
        mock_node_instance.send_request.assert_awaited_with(
            ("5.6.7.8", 8888), 
            {"msg": "hello"},
            timeout=10.0
        )
        
        await client.close()

@pytest.mark.asyncio
async def test_client_invoke_smart_routing():
    client = AgentMeshClient()
    
    with patch("agentmesh.p2p.node.P2PNode") as MockNode:
        mock_node_instance = AsyncMock()
        mock_node_instance.transport = MagicMock() # Simulate started transport
        mock_node_instance.send_request = AsyncMock(return_value={"p2p_result": "success"})
        mock_node_instance.close = MagicMock()
        MockNode.return_value = mock_node_instance
        
        await client.start_p2p()
        
        # Mock get_agent response for P2P check
        client.get_agent = AsyncMock(return_value={
            "agent": {
                "id": "target-agent",
                "network_profile": {
                    "public_endpoints": ["1.1.1.1:1111"],
                    "nat_type": "full_cone"
                }
            }
        })
        
        # Call generic invoke_agent
        result = await client.invoke_agent("target-agent", {"task": "test"})
        
        assert result["p2p_result"] == "success"
        
        # Verify it used P2P
        mock_node_instance.send_request.assert_awaited()
        args, kwargs = mock_node_instance.send_request.call_args
        assert args[0] == ("1.1.1.1", 1111)
        # Check payload wrapper
        p2p_payload = args[1]
        assert p2p_payload["target_agent_id"] == "target-agent"
        assert p2p_payload["payload"] == {"task": "test"}
        assert p2p_payload["skill"] is None
        
        await client.close()

@pytest.mark.asyncio
async def test_client_invoke_fallback():
    client = AgentMeshClient()
    
    with patch("agentmesh.p2p.node.P2PNode") as MockNode:
        mock_node_instance = AsyncMock()
        mock_node_instance.transport = MagicMock()
        # Simulate P2P failure
        mock_node_instance.send_request = AsyncMock(side_effect=TimeoutError("P2P timeout"))
        mock_node_instance.close = MagicMock()
        MockNode.return_value = mock_node_instance
        
        await client.start_p2p()
        
        # Mock get_agent for P2P check
        client.get_agent = AsyncMock(return_value={
            "agent": {
                "id": "target-agent",
                "network_profile": {
                    "public_endpoints": ["1.1.1.1:1111"],
                    "nat_type": "full_cone"
                }
            }
        })
        
        # Mock _request for HTTP fallback
        client._request = AsyncMock(return_value={"http_result": "success"})
        
        result = await client.invoke_agent("target-agent", {"task": "test"})
        
        assert result["http_result"] == "success"
        
        # Verify P2P was attempted
        mock_node_instance.send_request.assert_awaited()
        
        # Verify HTTP fallback was called
        client._request.assert_called()
        
        await client.close()
