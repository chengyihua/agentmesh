import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from agentmesh.api.server import AgentMeshServer

@pytest.mark.asyncio
async def test_server_p2p_handling():
    # Mock dependencies
    mock_registry = AsyncMock()
    mock_registry.start = AsyncMock()
    mock_registry.stop = AsyncMock()
    mock_registry.trust_manager = MagicMock() # Needed for rate limiter init
    
    # We need to patch P2PNode to avoid actual binding during init if we don't mock it
    # But AgentMeshServer inits P2PNode in __init__.
    # So we can patch P2PNode class.
    
    with patch("agentmesh.api.server.P2PNode") as MockP2PNode:
        mock_node_instance = MagicMock()
        MockP2PNode.return_value = mock_node_instance
        
        # Initialize server with mock registry
        # Note: We need to mock other deps if they do heavy lifting in init
        with patch("agentmesh.api.server.RedisStorage"), \
             patch("agentmesh.api.server.PostgresStorage"):
            
            mock_registry.invoke_agent = AsyncMock(return_value={"result": "success"})
            
            server = AgentMeshServer(registry=mock_registry, production=False, storage="memory")
            
            # Check if P2P node is initialized with handler
            assert server.p2p_node is not None
            # Verify on_request was passed. 
            # Since we mocked P2PNode, we check the call args of the class
            call_args = MockP2PNode.call_args
            assert call_args.kwargs['on_request'] == server._handle_p2p_request
            
            # Simulate incoming P2P request
            payload = {
                "target_agent_id": "test-agent",
                "skill": "test-skill",
                "payload": {"foo": "bar"},
                "method": "POST"
            }
            addr = ("1.2.3.4", 5678)
            
            response = await server._handle_p2p_request(payload, addr)
            
            # Verify response
            assert response["status"] == "success"
            assert response["result"] == {"result": "success"}
            
            # Verify registry invocation
            mock_registry.invoke_agent.assert_awaited_with(
                "test-agent",
                skill="test-skill",
                payload={"foo": "bar"},
                path=None,
                method="POST",
                headers=None,
                timeout_seconds=30.0
            )

@pytest.mark.asyncio
async def test_server_p2p_handling_missing_agent_id():
    with patch("agentmesh.api.server.P2PNode"):
        server = AgentMeshServer(production=False, storage="memory")
        
        payload = {
            "skill": "test-skill"
        }
        addr = ("1.2.3.4", 5678)
        
        response = await server._handle_p2p_request(payload, addr)
        
        assert "error" in response
        assert "Missing target_agent_id" in response["error"]

@pytest.mark.asyncio
async def test_server_p2p_handling_error():
    mock_registry = AsyncMock()
    mock_registry.trust_manager = MagicMock()
    
    with patch("agentmesh.api.server.P2PNode"):
        mock_registry.invoke_agent = AsyncMock(side_effect=ValueError("Agent not found"))
        
        server = AgentMeshServer(registry=mock_registry, production=False, storage="memory")
        
        payload = {
            "target_agent_id": "unknown-agent",
            "payload": {}
        }
        addr = ("1.2.3.4", 5678)
        
        response = await server._handle_p2p_request(payload, addr)
        
        assert "error" in response
        assert "Agent not found" in response["error"]
