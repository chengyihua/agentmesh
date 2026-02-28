
import pytest
import asyncio
import json
from unittest.mock import MagicMock, AsyncMock, patch

from agentmesh.relay.client import RelayClient
from agentmesh.core.security import SecurityManager

@pytest.mark.asyncio
async def test_relay_client_handshake_and_request():
    # Setup mocks
    mock_websocket = AsyncMock()
    mock_websocket.recv = AsyncMock()
    mock_websocket.send = AsyncMock()
    mock_websocket.close = AsyncMock()
    
    # Mock SecurityManager
    sm = MagicMock(spec=SecurityManager)
    sm.sign_data.return_value = "mock_signature"
    
    # Mock request handler
    handler = AsyncMock(return_value={"result": "success"})
    
    # Create client
    client = RelayClient(
        relay_url="ws://localhost:8000",
        agent_id="agent_123",
        private_key="mock_priv_key",
        request_handler=handler,
        security_manager=sm
    )
    
    # Mock connect context manager
    mock_connect = MagicMock()
    mock_connect.__aenter__.return_value = mock_websocket
    mock_connect.__aexit__.return_value = None
    
    with patch("agentmesh.relay.client.connect", return_value=mock_connect):
        # Configure recv to return sequence of messages
        # 1. Challenge
        # 2. Request
        # 3. Raise ConnectionClosed to stop loop
        
        challenge_msg = json.dumps({"type": "challenge", "nonce": "test_nonce"})
        request_msg = json.dumps({
            "type": "request", 
            "request_id": "req_1",
            "payload": {"foo": "bar"}
        })
        
        # We need to control the loop.
        # recv() is called once for handshake, then in loop.
        
        # Side effect for recv()
        async def recv_side_effect():
            if mock_websocket.recv.call_count == 1:
                return challenge_msg
            elif mock_websocket.recv.call_count == 2:
                return request_msg
            else:
                # Stop the client loop
                client.running = False
                # Raise exception to break await if needed, but running=False should stop loop
                # However, loop checks running at start.
                # If we are inside recv(), we need to return something or raise.
                from websockets.exceptions import ConnectionClosed
                raise ConnectionClosed(None, None)

        mock_websocket.recv.side_effect = recv_side_effect
        
        # Run connect()
        # It will run until ConnectionClosed
        try:
            await client.connect()
        except Exception:
            pass
            
        # Verify Handshake
        # First send should be challenge response
        args, _ = mock_websocket.send.call_args_list[0]
        response = json.loads(args[0])
        assert response["type"] == "challenge_response"
        assert response["signature"] == "mock_signature"
        
        # Verify Request Handling
        # Handler called?
        handler.assert_called_once()
        assert handler.call_args[0][0] == {"foo": "bar"}
        
        # Second send should be request response
        args, _ = mock_websocket.send.call_args_list[1]
        response = json.loads(args[0])
        assert response["request_id"] == "req_1"
        assert response["status"] == "success"
        assert response["result"]["result"] == "success"
