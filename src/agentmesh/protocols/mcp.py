"""MCP protocol bridge."""

from __future__ import annotations

import uuid
from typing import Any, Dict

from .base import BaseProtocolHandler, InvocationRequest, InvocationResult, ProtocolInvocationError, resolve_target_url


class MCPProtocolHandler(BaseProtocolHandler):
    """HTTP MCP gateway bridge using JSON-RPC style payload."""

    async def invoke(self, request: InvocationRequest) -> InvocationResult:
        method = (request.method or "POST").upper()
        if method != "POST":
            raise ProtocolInvocationError("MCP protocol only supports POST invocation", status_code=400)

        url = resolve_target_url(request.endpoint, request.path or "/mcp/invoke")
        rpc_id = str(uuid.uuid4())

        if request.skill:
            rpc_method = "tools/call"
            params: Dict[str, Any] = {
                "name": request.skill,
                "arguments": request.payload or {},
                "agent_id": request.agent_id,
            }
        else:
            rpc_method = "agentmesh/invoke"
            params = {
                "agent_id": request.agent_id,
                "payload": request.payload or {},
            }

        body: Dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "method": rpc_method,
            "params": params,
        }

        headers = dict(request.headers or {})
        headers.setdefault("Content-Type", "application/json")

        return await self._perform_request(
            protocol="mcp",
            method="POST",
            url=url,
            timeout=request.timeout_seconds,
            headers=headers,
            json_body=body,
        )
