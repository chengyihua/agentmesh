"""Relay Manager for handling WebSocket connections and routing."""

from __future__ import annotations

import asyncio
import json
import logging
import secrets
from typing import Dict, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect

from ..protocols.base import InvocationRequest, InvocationResult
from ..core.security import SecurityManager
from ..core.registry import AgentRegistry
from ..core.agent_card import HealthStatus

logger = logging.getLogger(__name__)

class RelayManager:
    """Manages WebSocket connections for relaying requests to agents."""

    def __init__(self, registry: AgentRegistry, security_manager: SecurityManager):
        self.registry = registry
        self.security_manager = security_manager
        self.connections: Dict[str, WebSocket] = {}
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self._lock = asyncio.Lock()

    def is_connected(self, agent_id: str) -> bool:
        """Check if an agent is connected to the relay."""
        return agent_id in self.connections

    async def invoke(self, agent_id: str, request: InvocationRequest) -> InvocationResult:
        """Invoke an agent via the relay connection."""
        if not self.is_connected(agent_id):
            raise ValueError(f"Agent {agent_id} not connected to Relay")
            
        start_time = asyncio.get_running_loop().time()
        
        # Prepare payload matching InvocationRequest fields
        payload = {
            "skill": request.skill,
            "payload": request.payload,
            "path": request.path,
            "method": request.method,
            "headers": request.headers,
        }
        
        try:
            # Send request and wait for response
            response_data = await self.forward_request(agent_id, payload, timeout=request.timeout_seconds)
            
            # Calculate latency
            latency = (asyncio.get_running_loop().time() - start_time) * 1000
            
            # Check for error in response
            if response_data.get("status") == "error":
                return InvocationResult(
                    protocol="relay",
                    target_url=f"relay://{agent_id}",
                    status_code=500,
                    ok=False,
                    latency_ms=latency,
                    response={"error": response_data.get("error", "Unknown error")},
                    response_headers={}
                )
            
            return InvocationResult(
                protocol="relay",
                target_url=f"relay://{agent_id}",
                status_code=200,
                ok=True,
                latency_ms=latency,
                response=response_data.get("result", response_data),
                response_headers={}
            )
            
        except TimeoutError:
             return InvocationResult(
                protocol="relay",
                target_url=f"relay://{agent_id}",
                status_code=504,
                ok=False,
                latency_ms=(asyncio.get_running_loop().time() - start_time) * 1000,
                response={"error": "Gateway Timeout"},
                response_headers={}
            )
        except Exception as e:
             return InvocationResult(
                protocol="relay",
                target_url=f"relay://{agent_id}",
                status_code=500,
                ok=False,
                latency_ms=(asyncio.get_running_loop().time() - start_time) * 1000,
                response={"error": str(e)},
                response_headers={}
            )

    async def handle_connection(self, websocket: WebSocket, agent_id: str):
        """
        Handle a WebSocket connection from an agent.
        Performs handshake and then enters message loop.
        """
        await websocket.accept()
        
        # 1. Verify agent exists
        agent = await self.registry.get_agent(agent_id)
        if not agent:
            await websocket.close(code=4004, reason="Agent not found")
            return

        if not agent.public_key:
            await websocket.close(code=4003, reason="Agent has no public key")
            return

        # 2. Challenge-Response Handshake
        nonce = secrets.token_hex(16)
        await websocket.send_text(json.dumps({"type": "challenge", "nonce": nonce}))
        
        try:
            msg = await websocket.receive_text()
            data = json.loads(msg)
            if data.get("type") != "challenge_response":
                await websocket.close(code=4000, reason="Invalid response type")
                return
            
            signature = data.get("signature")
            if not signature:
                await websocket.close(code=4001, reason="Missing signature")
                return

            # Verify signature of the nonce
            is_valid = self.security_manager.verify_data_signature(nonce, signature, agent.public_key)
            if not is_valid:
                await websocket.close(code=4002, reason="Invalid signature")
                return

        except Exception as e:
            logger.error(f"Handshake error for {agent_id}: {e}")
            await websocket.close(code=4000, reason="Handshake error")
            return

        # 3. Register connection
        async with self._lock:
            # If there's an existing connection, close it
            old_ws = self.connections.get(agent_id)
            if old_ws:
                try:
                    await old_ws.close(code=1000, reason="New connection replaced old one")
                except Exception:
                    pass
            self.connections[agent_id] = websocket
        
        logger.info(f"Agent {agent_id} connected via Relay")
        
        # Mark as Healthy
        try:
            agent = await self.registry.get_agent(agent_id)
            if agent:
                agent.set_health_status(HealthStatus.HEALTHY)
                await self.registry.storage.upsert_agent(agent)
        except Exception as e:
            logger.warning(f"Failed to update agent status on connect: {e}")
        
        try:
            while True:
                # Listen for messages (responses to requests)
                data = await websocket.receive_text()
                await self._handle_message(agent_id, data)
        except WebSocketDisconnect:
            logger.info(f"Agent {agent_id} disconnected")
        except Exception as e:
            logger.error(f"Connection error for {agent_id}: {e}")
        finally:
            async with self._lock:
                if self.connections.get(agent_id) == websocket:
                    del self.connections[agent_id]
                    
                    # Mark as Offline
                    try:
                        agent = await self.registry.get_agent(agent_id)
                        if agent:
                            agent.set_health_status(HealthStatus.OFFLINE)
                            await self.registry.storage.upsert_agent(agent)
                            logger.info(f"Agent {agent_id} marked as OFFLINE due to relay disconnect")
                    except Exception as e:
                        logger.error(f"Failed to mark agent offline: {e}")

    async def _handle_message(self, agent_id: str, data: str):
        """Handle incoming message from agent (usually a response)."""
        try:
            msg = json.loads(data)
            # Check if it's a response to a pending request
            request_id = msg.get("request_id")
            if request_id:
                future = self.pending_requests.pop(request_id, None)
                if future and not future.done():
                    future.set_result(msg)
            else:
                logger.warning(f"Received message without request_id from {agent_id}: {msg}")
        except Exception as e:
            logger.error(f"Error handling message from {agent_id}: {e}")

    async def forward_request(self, agent_id: str, payload: Dict[str, Any], timeout: float = 30.0) -> Dict[str, Any]:
        """Forward a request to the agent and wait for response."""
        websocket = self.connections.get(agent_id)
        if websocket is None:
            raise ValueError(f"Agent {agent_id} not connected to Relay")
        
        # Generate a unique request ID if not present
        if "request_id" not in payload:
            payload["request_id"] = secrets.token_hex(8)
        
        request_id = payload["request_id"]
        
        future = asyncio.get_running_loop().create_future()
        self.pending_requests[request_id] = future
        
        try:
            # Wrap payload in a standard envelope
            envelope = {
                "type": "request",
                "payload": payload,
                "request_id": request_id
            }
            await websocket.send_text(json.dumps(envelope))
            
            # Wait for response
            response = await asyncio.wait_for(future, timeout)
            return response
            
        except asyncio.TimeoutError:
            self.pending_requests.pop(request_id, None)
            raise TimeoutError("Relay request timed out")
        except Exception as e:
            self.pending_requests.pop(request_id, None)
            raise e
