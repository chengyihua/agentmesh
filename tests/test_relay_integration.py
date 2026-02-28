
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from fastapi import WebSocket

from agentmesh.core.registry import AgentRegistry
from agentmesh.core.agent_card import AgentCard, ProtocolType
from agentmesh.protocols.gateway import ProtocolGateway
from agentmesh.protocols.relay import RelayProtocolHandler
from agentmesh.relay.manager import RelayManager
from agentmesh.core.security import SecurityManager

@pytest.mark.asyncio
async def test_relay_integration_invoke_flow():
    # 1. Setup Registry and RelayManager
    security_manager = MagicMock(spec=SecurityManager)
    # verify_data_signature must return True for handshake
    security_manager.verify_data_signature.return_value = True
    
    registry = AgentRegistry(security_manager=security_manager)
    relay_manager = RelayManager(registry, security_manager)
    
    # Wire RelayProtocolHandler into Gateway
    # We create a gateway and manually add the handler, similar to server.py
    gateway = ProtocolGateway()
    relay_handler = RelayProtocolHandler(relay_invoke=relay_manager.invoke)
    gateway._handlers["relay"] = relay_handler
    
    # Assign gateway to registry
    registry.protocol_gateway = gateway
    registry.relay_manager = relay_manager
    
    # 2. Register an Agent with protocol='relay'
    agent_id = "agent_relay_001"
    agent_card = AgentCard(
        id=agent_id,
        name="Relay Agent",
        version="1.0.0",
        skills=[{"name": "echo", "description": "Echoes payload"}],
        endpoint=f"relay://{agent_id}",
        protocol=ProtocolType.RELAY,
        public_key="mock_pub_key"
    )
    
    # Register directly into registry storage/memory
    registry.agents[agent_id] = agent_card
    
    # Mock registry.get_agent to return our agent (since registry.agents is used by get_agent usually, but let's be safe)
    # Actually registry.get_agent uses self.storage.get_agent or self.agents if MemoryStorage is implicit.
    # But let's just use the real registry methods since we are testing integration.
    # However, registry.get_agent is async.
    # Let's mock get_agent on registry if needed, but registry uses memory storage by default.
    # So we can just set it.
    
    # 3. Connect a mock WebSocket for this agent
    mock_ws = MagicMock(spec=WebSocket)
    mock_ws.accept = AsyncMock()
    mock_ws.send_text = AsyncMock()
    mock_ws.close = AsyncMock()
    
    # Use a queue to control receive_text behavior dynamically
    response_queue = asyncio.Queue()
    
    async def dynamic_receive_text():
        return await response_queue.get()
    
    mock_ws.receive_text = dynamic_receive_text
    
    # Simulate Handshake
    # The RelayManager.handle_connection waits for a handshake response.
    
    # We'll run handle_connection in a background task
    connection_task = asyncio.create_task(relay_manager.handle_connection(mock_ws, agent_id))
    
    # Wait for challenge
    await asyncio.sleep(0.01)
    mock_ws.send_text.assert_called() # Should have sent challenge
    
    # Send challenge response
    response_msg = '{"type": "challenge_response", "signature": "sig"}'
    await response_queue.put(response_msg)
    
    # Wait for connection to be established
    await asyncio.sleep(0.01)
    assert relay_manager.is_connected(agent_id)
    
    # 4. Invoke the agent via Registry
    invoke_payload = {"msg": "hello"}
    
    # We need to handle the agent side logic:
    # When RelayManager sends a request, we need to capture it and put a response in the queue.
    
    async def auto_respond_loop():
        while True:
            await asyncio.sleep(0.01)
            # Check if send_text was called with a request
            if mock_ws.send_text.call_count >= 2: # 1 challenge + 1 request
                # Get the last call args
                args = mock_ws.send_text.call_args[0][0]
                import json
                try:
                    msg = json.loads(args)
                    if msg.get("type") == "request":
                        req_id = msg.get("request_id")
                        # Send response
                        resp = {
                            "request_id": req_id,
                            "status": "success",
                            "result": {"echo": "hello"}
                        }
                        await response_queue.put(json.dumps(resp))
                        break
                except:
                    pass
    
    responder = asyncio.create_task(auto_respond_loop())
    
    # Perform Invocation
    result = await registry.invoke_agent(
        agent_id=agent_id,
        skill="echo",
        payload=invoke_payload
    )
    
    # Verify result
    assert result["ok"] is True
    assert result["response"]["echo"] == "hello"
    assert result["protocol"] == "relay"
    
    # Cleanup
    responder.cancel()
    connection_task.cancel()
    try:
        await connection_task
    except asyncio.CancelledError:
        pass
