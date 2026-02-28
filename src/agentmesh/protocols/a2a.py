"""A2A protocol bridge."""

from __future__ import annotations

from typing import Any, Dict

from .base import BaseProtocolHandler, InvocationRequest, InvocationResult, ProtocolInvocationError, resolve_target_url


class A2AProtocolHandler(BaseProtocolHandler):
    """Simple HTTP bridge for A2A-style invoke payloads."""

    async def invoke(self, request: InvocationRequest) -> InvocationResult:
        method = (request.method or "POST").upper()
        if method != "POST":
            raise ProtocolInvocationError("A2A protocol only supports POST invocation", status_code=400)

        url = resolve_target_url(request.endpoint, request.path or "/a2a/invoke")
        body: Dict[str, Any] = {
            "protocol": "a2a",
            "agent_id": request.agent_id,
            "skill": request.skill,
            "payload": request.payload or {},
        }

        headers = dict(request.headers or {})
        headers.setdefault("Content-Type", "application/json")

        return await self._perform_request(
            protocol="a2a",
            method="POST",
            url=url,
            timeout=request.timeout_seconds,
            headers=headers,
            json_body=body,
        )
