"""WebSocket protocol bridge."""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any, Awaitable, Callable, Dict, Optional
from urllib.parse import urlparse, urlunparse

from .base import InvocationRequest, InvocationResult, ProtocolTransportError, resolve_target_url

WebsocketInvokeFn = Callable[[InvocationRequest], Awaitable[InvocationResult]]


def _to_websocket_url(url: str) -> str:
    if "://" not in url:
        return f"ws://{url.lstrip('/')}"

    parsed = urlparse(url)
    if parsed.scheme in {"ws", "wss"}:
        return url
    if parsed.scheme == "http":
        return urlunparse(parsed._replace(scheme="ws"))
    if parsed.scheme == "https":
        return urlunparse(parsed._replace(scheme="wss"))
    if parsed.scheme:
        return url
    return f"ws://{url.lstrip('/')}"


class WebsocketProtocolHandler:
    """WebSocket invoke bridge (send one message, await one response)."""

    def __init__(self, websocket_invoke: Optional[WebsocketInvokeFn] = None):
        self._websocket_invoke = websocket_invoke

    async def invoke(self, request: InvocationRequest) -> InvocationResult:
        if self._websocket_invoke is not None:
            return await self._websocket_invoke(request)
        return await self._invoke_real(request)

    async def _invoke_real(self, request: InvocationRequest) -> InvocationResult:
        try:
            import websockets
        except ImportError as exc:
            raise ProtocolTransportError("websockets package is required for websocket protocol invocation") from exc

        target_url = _to_websocket_url(resolve_target_url(request.endpoint, request.path))
        timeout = request.timeout_seconds
        started_at = time.monotonic()

        payload: Dict[str, Any] = {
            "agent_id": request.agent_id,
            "skill": request.skill,
            "payload": request.payload or {},
        }
        outbound = json.dumps(payload)

        connect_kwargs: Dict[str, Any] = {"open_timeout": timeout, "close_timeout": timeout}
        if request.headers:
            connect_kwargs["additional_headers"] = dict(request.headers)

        try:
            connection = websockets.connect(target_url, **connect_kwargs)
        except TypeError:
            if "additional_headers" in connect_kwargs:
                connect_kwargs["extra_headers"] = connect_kwargs.pop("additional_headers")
            connection = websockets.connect(target_url, **connect_kwargs)

        try:
            async with connection as ws:
                await ws.send(outbound)
                inbound = await asyncio.wait_for(ws.recv(), timeout=timeout)
        except Exception as exc:
            raise ProtocolTransportError(
                f"WebSocket protocol invocation failed: {exc}",
                details={"protocol": "websocket", "url": target_url},
            ) from exc

        latency_ms = round((time.monotonic() - started_at) * 1000, 3)
        parsed_response: Any
        try:
            parsed_response = json.loads(inbound) if isinstance(inbound, str) else inbound
        except (TypeError, ValueError):
            parsed_response = inbound

        return InvocationResult(
            protocol="websocket",
            target_url=target_url,
            status_code=200,
            ok=True,
            latency_ms=latency_ms,
            response=parsed_response,
            response_headers={},
        )
