
import asyncio
import json
import logging
from typing import Any, Callable, Dict, Optional, Awaitable

import websockets
from websockets.client import connect
from websockets.exceptions import ConnectionClosed

from ..core.security import SecurityManager

logger = logging.getLogger(__name__)

class RelayClient:
    """
    Client for connecting to the AgentMesh Relay Network.
    Allows an agent to receive requests via a WebSocket connection.
    """

    def __init__(
        self,
        relay_url: str,
        agent_id: str,
        private_key: str,
        request_handler: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]],
        security_manager: Optional[SecurityManager] = None,
    ):
        self.relay_url = relay_url.rstrip("/")
        self.agent_id = agent_id
        self.private_key = private_key
        self.request_handler = request_handler
        self.security_manager = security_manager or SecurityManager()
        self.running = False
        self.websocket = None

    async def connect(self):
        """Connect to the relay server and start listening for requests."""
        url = f"{self.relay_url}/relay/v1/ws/{self.agent_id}"
        logger.info(f"Connecting to relay: {url}")
        
        try:
            async with connect(url) as websocket:
                self.websocket = websocket
                self.running = True
                
                # 1. Handle Handshake
                try:
                    msg = await websocket.recv()
                    data = json.loads(msg)
                    
                    if data.get("type") != "challenge":
                        logger.error(f"Unexpected handshake message: {msg}")
                        return

                    nonce = data.get("nonce")
                    if not nonce:
                        logger.error("Missing nonce in challenge")
                        return
                    
                    # Sign the nonce
                    signature = self.security_manager.sign_data(nonce, self.private_key)
                    
                    # Send response
                    response = {
                        "type": "challenge_response",
                        "signature": signature
                    }
                    await websocket.send(json.dumps(response))
                    logger.info("Handshake completed successfully")
                    
                except Exception as e:
                    logger.error(f"Handshake failed: {e}")
                    return

                # 2. Listen for requests
                logger.info("Listening for relay requests...")
                while self.running:
                    try:
                        message = await websocket.recv()
                        await self._handle_message(message)
                    except ConnectionClosed:
                        logger.warning("Relay connection closed")
                        break
                    except Exception as e:
                        logger.error(f"Error receiving message: {e}")
                        break
                        
        except Exception as e:
            logger.error(f"Failed to connect to relay: {e}")
            raise

    async def _handle_message(self, message: str):
        """Process incoming relay message."""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type == "request":
                await self._process_request(data)
            else:
                logger.warning(f"Unknown message type: {msg_type}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def _process_request(self, data: Dict[str, Any]):
        """Execute the request handler and send response."""
        request_id = data.get("request_id")
        payload = data.get("payload", {})
        
        if not request_id:
            logger.error("Request missing request_id")
            return
            
        try:
            # Call user handler
            result = await self.request_handler(payload)
            
            # Send success response
            response = {
                "request_id": request_id,
                "status": "success",
                "result": result
            }
        except Exception as e:
            logger.error(f"Error processing request {request_id}: {e}")
            # Send error response
            response = {
                "request_id": request_id,
                "status": "error",
                "error": str(e)
            }
            
        if self.websocket:
            await self.websocket.send(json.dumps(response))

    def stop(self):
        """Stop the relay client."""
        self.running = False
        # WebSocket close is handled by context manager in connect()
