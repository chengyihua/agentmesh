"""HTTP/CUSTOM protocol bridge."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .base import BaseProtocolHandler, InvocationRequest, InvocationResult, resolve_target_url


class HttpCustomProtocolHandler(BaseProtocolHandler):
    """Direct HTTP bridge used for `http` and `custom` protocols."""

    async def invoke(self, request: InvocationRequest) -> InvocationResult:
        method = (request.method or "POST").upper()
        headers: Dict[str, str] = dict(request.headers or {})
        if request.skill:
            headers.setdefault("X-AgentMesh-Skill", request.skill)

        url = resolve_target_url(request.endpoint, request.path)
        payload: Dict[str, Any] = dict(request.payload or {})

        params: Optional[Dict[str, Any]] = None
        json_body: Optional[Dict[str, Any]] = None
        if method in {"GET", "DELETE"}:
            params = payload
            if request.skill:
                params = dict(params or {})
                params.setdefault("skill", request.skill)
        else:
            json_body = payload

        return await self._perform_request(
            protocol=request.protocol,
            method=method,
            url=url,
            timeout=request.timeout_seconds,
            headers=headers or None,
            params=params,
            json_body=json_body,
        )
