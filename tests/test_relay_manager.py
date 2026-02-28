
import pytest
import asyncio
import json
from unittest.mock import MagicMock, AsyncMock
from fastapi import WebSocket

from agentmesh.relay.manager import RelayManager
from agentmesh.core.registry import AgentRegistry
from agentmesh.core.security import SecurityManager
from agentmesh.core.agent_card import AgentCard

@pytest.mark.asyncio
async def test_relay_manager_flow():
    # Setup mocks
    registry = MagicMock(spec=AgentRegistry)
    sm = MagicMock(spec=SecurityManager)
    
    # Configure SecurityManager mock
    sm.verify_data_signature.return_value = True
    
    # Configure Registry mock
    agent = AgentCard(
        id="agent_123",
        name="Mock Agent",
        version="1.0.0",
        skills=[{"name": "test", "description": "test skill"}],
        endpoint="http://localhost",
        public_key="mock_pub"
    )
    registry.get_agent = AsyncMock(return_value=agent)
    
    manager = RelayManager(registry, sm)
    
    # Mock WebSocket
    mock_ws = MagicMock(spec=WebSocket)
    mock_ws.accept = AsyncMock()
    mock_ws.send_text = AsyncMock()
    mock_ws.close = AsyncMock()
    
    # Create a queue for incoming messages (to be read by handle_connection)
    incoming_queue = asyncio.Queue()
    
    async def mock_receive_text():
        # This simulates receiving a message from the websocket
        return await incoming_queue.get()
    
    mock_ws.receive_text = mock_receive_text
    
    # Start handle_connection in a background task
    connection_task = asyncio.create_task(manager.handle_connection(mock_ws, "agent_123"))
    
    # 1. Verify Handshake Challenge
    # Wait for challenge to be sent
    await asyncio.sleep(0.1)
    mock_ws.send_text.assert_called()
    call_args = mock_ws.send_text.call_args[0][0]
    challenge_msg = json.loads(call_args)
    assert challenge_msg["type"] == "challenge"
    assert "nonce" in challenge_msg
    
    # 2. Send Challenge Response
    response_msg = {
        "type": "challenge_response",
        "signature": "valid_signature"
    }
    await incoming_queue.put(json.dumps(response_msg))
    
    # Wait for connection to be established
    await asyncio.sleep(0.1)
    
    # Check if connection is registered
    print(f"Connections before forward: {manager.connections}")
    assert "agent_123" in manager.connections
    assert manager.connections["agent_123"] == mock_ws
    
    # 3. Test Request Forwarding (Client -> Relay -> Agent)
    request_payload = {"action": "test_action", "data": "foo"}
    
    # Start forward_request in background (it waits for response)
    # We need to run this concurrently
    print("Starting forward_request task")
    forward_task = asyncio.create_task(manager.forward_request("agent_123", request_payload))
    
    # Wait for request to be sent to WebSocket
    await asyncio.sleep(0.1)
    
    # Check if request was sent to WS
    print("Checking if request sent")
    # Get the last call to send_text
    last_call_args = mock_ws.send_text.call_args[0][0]
    request_msg = json.loads(last_call_args)
    
    assert request_msg["type"] == "request"
    assert request_msg["payload"] == request_payload
    assert "request_id" in request_msg
    request_id = request_msg["request_id"]
    
    # 4. Send Response from Agent (Agent -> Relay -> Client)
    agent_response = {
        "request_id": request_id,
        "status": "success",
        "result": "bar"
    }
    await incoming_queue.put(json.dumps(agent_response))
    
    # Wait for forward_request to complete and get result
    result = await forward_task
    
    assert result == agent_response
    
    # Cleanup
    connection_task.cancel()
    try:
        await connection_task
    except asyncio.CancelledError:
        pass
