
import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from agentmesh.client import AgentMeshClient
from agentmesh.p2p.node import P2PNode

@pytest.mark.asyncio
async def test_p2p_full_flow_simulation():
    """
    Simulate full P2P flow between Agent A and Agent B without actual HTTP server.
    Flow:
    1. A wants to call B.
    2. A checks B's profile (mocked).
    3. A sends handshake HTTP request (mocked).
    4. B receives handshake (simulated), starts punching to A.
    5. A starts punching to B.
    6. Connection established.
    7. A sends request via UDP.
    8. B processes request and responds.
    9. A receives response.
    """
    
    # --- Setup Nodes ---
    # Use real P2P nodes on localhost with random ports
    node_a = P2PNode(port=0)
    await node_a.start()
    port_a = node_a.transport.get_extra_info('sockname')[1]
    
    node_b = P2PNode(port=0)
    await node_b.start()
    port_b = node_b.transport.get_extra_info('sockname')[1]
    
    # Setup B's request handler
    async def handle_b_request(data, addr):
        # B receives request from A
        # Note: P2PNode passes (payload, addr)
        return {"status": "success", "echo": data.get("payload")}
    
    node_b.on_request = handle_b_request
    
    # --- Setup Clients ---
    client_a = AgentMeshClient(agent_id="agent-a")
    client_a.p2p_node = node_a # Inject real node
    
    # Mock client_a.get_agent("agent-b")
    mock_agent_b_profile = {
        "id": "agent-b",
        "network_profile": {
            "nat_type": "symmetric", # Doesn't matter for this test as we use localhost
            "public_endpoints": [f"127.0.0.1:{port_b}"],
            "p2p_protocols": ["udp-json"]
        }
    }
    client_a.get_agent = AsyncMock(return_value={"agent": mock_agent_b_profile})
    
    # Mock client_a.invoke_agent (the recursive call for handshake)
    # We need to allow the first call (skill="task") but intercept the second (skill="sys.p2p.handshake")
    # Actually invoke_agent is what we are testing, so we should mock _request instead?
    # Or better, we let invoke_agent run, and mock _request for the handshake.
    
    original_invoke = client_a.invoke_agent
    
    async def mock_request(method, path, **kwargs):
        # This mocks the HTTP calls.
        # If it's the handshake call:
        json_body = kwargs.get("json_body", {})
        skill = json_body.get("skill")
        
        if skill == "sys.p2p.handshake":
            # Simulate B receiving handshake
            # B connects to A
            # A's endpoint is in the payload
            payload = json_body.get("payload", {})
            a_endpoint = payload.get("public_endpoint")
            # In real world, this would come from request IP, but here we use payload
            # But wait, node_a.public_endpoint might be None if STUN failed or mocked
            # Let's force set public endpoints for test
            node_a.public_endpoint = ("127.0.0.1", port_a)
            
            # B punches to A
            asyncio.create_task(node_b.connect_to_peer("127.0.0.1", port_a))
            return {"status": "success"}
            
        return {"status": "mock_http_fallback"}

    client_a._request = AsyncMock(side_effect=mock_request)
    
    # Also need to mock STUN discovery or ensure public_endpoint is set
    node_a.public_endpoint = ("127.0.0.1", port_a)
    
    # --- Execute Flow ---
    try:
        # Client A invokes B
        # This should trigger P2P logic
        response = await client_a.invoke_agent(
            "agent-b",
            payload={"msg": "hello p2p"},
            skill="test.skill",
            timeout_seconds=5.0
        )
        
        # --- Verification ---
        # 1. Check if response came from P2P (B's handler returns "echo")
        assert response.get("status") == "success"
        assert response.get("echo") == {"msg": "hello p2p"}
        
        # 2. Verify handshake was called
        # client_a._request should have been called with skill="sys.p2p.handshake"
        calls = client_a._request.call_args_list
        handshake_called = False
        for call in calls:
            args, kwargs = call
            if kwargs.get("json_body", {}).get("skill") == "sys.p2p.handshake":
                handshake_called = True
                break
        assert handshake_called, "Handshake HTTP request was not sent"
        
    finally:
        node_a.close()
        node_b.close()
        await client_a.close()

