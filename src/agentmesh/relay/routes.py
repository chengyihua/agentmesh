"""Relay API routes."""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, WebSocket, HTTPException, Request, status
from ..core.registry import AgentRegistry
from ..core.security import SecurityManager
from ..core.errors import ErrorCode, raise_error
from .manager import RelayManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["relay"])

def get_registry(request: Request) -> AgentRegistry:
    return request.app.state.registry

def get_security_manager(request: Request) -> SecurityManager:
    return request.app.state.security_manager

def get_relay_manager(request: Request) -> RelayManager:
    return request.app.state.relay_manager

def get_relay_manager_ws(websocket: WebSocket) -> RelayManager:
    return websocket.app.state.relay_manager

@router.websocket("/ws/{agent_id}")
async def relay_websocket_endpoint(
    websocket: WebSocket,
    agent_id: str,
    relay_manager: RelayManager = Depends(get_relay_manager_ws)
):
    """WebSocket endpoint for agents to connect to the relay."""
    await relay_manager.handle_connection(websocket, agent_id)

@router.post("/invoke/{agent_id}")
async def invoke_agent_via_relay(
    agent_id: str,
    payload: Dict[str, Any],
    relay_manager: RelayManager = Depends(get_relay_manager)
) -> Dict[str, Any]:
    """Invoke an agent via the relay connection."""
    try:
        response = await relay_manager.forward_request(agent_id, payload)
        return response
    except ValueError as e:
        raise_error(status_code=status.HTTP_404_NOT_FOUND, code=ErrorCode.NOT_FOUND, message=str(e))
    except TimeoutError:
        raise_error(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            code=ErrorCode.RELAY_CONNECTION_FAILED,
            message="Request timed out"
        )
    except Exception as e:
        logger.error(f"Relay invocation error: {e}")
        raise_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code=ErrorCode.INTERNAL_ERROR,
            message="Relay error",
            details={"error": str(e)}
        )
