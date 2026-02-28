"""Protocol invocation primitives for AgentMesh."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, Optional

import httpx

HttpRequestFn = Callable[..., Awaitable[httpx.Response]]
RelayInvokeFn = Callable[[str, "InvocationRequest"], Awaitable["InvocationResult"]]


async def default_http_request(
    *,
    method: str,
    url: str,
    timeout: float,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json_body: Optional[Any] = None,
) -> httpx.Response:
    """Default async HTTP requester used by protocol handlers."""
    async with httpx.AsyncClient(timeout=timeout) as client:
        return await client.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json_body,
        )


def resolve_target_url(endpoint: str, path: Optional[str]) -> str:
    """Resolve target URL from endpoint + optional path."""
    if not path:
        return endpoint
    normalized = path.strip()
    if normalized.startswith("http://") or normalized.startswith("https://"):
        return normalized
    return f"{endpoint.rstrip('/')}/{normalized.lstrip('/')}"


def parse_response_data(response: httpx.Response) -> Any:
    """Parse response body as JSON when possible, fallback to text."""
    content_type = response.headers.get("content-type", "").lower()
    if "application/json" in content_type:
        try:
            return response.json()
        except ValueError:
            return response.text
    try:
        return response.json()
    except ValueError:
        return response.text


@dataclass
class InvocationRequest:
    """Internal invoke request dispatched to protocol handlers."""

    agent_id: str
    endpoint: str
    protocol: str
    skill: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    path: Optional[str] = None
    method: str = "POST"
    timeout_seconds: float = 30.0
    headers: Dict[str, str] = field(default_factory=dict)


@dataclass
class InvocationResult:
    """Internal invoke response returned from protocol handlers."""

    protocol: str
    target_url: str
    status_code: int
    ok: bool
    latency_ms: float
    response: Any
    response_headers: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "protocol": self.protocol,
            "target_url": self.target_url,
            "status_code": self.status_code,
            "ok": self.ok,
            "latency_ms": self.latency_ms,
            "response": self.response,
            "response_headers": self.response_headers,
        }


class ProtocolInvocationError(Exception):
    """Base protocol invocation error."""

    def __init__(self, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details or {}


class ProtocolNotImplementedError(ProtocolInvocationError):
    """Raised when protocol exists but invocation bridge is not implemented."""

    def __init__(self, message: str):
        super().__init__(message, status_code=501)


class ProtocolTransportError(ProtocolInvocationError):
    """Raised when remote call fails at transport layer."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=502, details=details)


class BaseProtocolHandler:
    """Base protocol handler interface."""

    def __init__(self, http_request: Optional[HttpRequestFn] = None):
        self._http_request = http_request or default_http_request

    async def invoke(self, request: InvocationRequest) -> InvocationResult:
        raise NotImplementedError

    async def _perform_request(
        self,
        *,
        protocol: str,
        method: str,
        url: str,
        timeout: float,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Any] = None,
    ) -> InvocationResult:
        started_at = time.monotonic()
        try:
            response = await self._http_request(
                method=method,
                url=url,
                timeout=timeout,
                headers=headers,
                params=params,
                json_body=json_body,
            )
        except httpx.HTTPError as exc:
            raise ProtocolTransportError(
                f"Protocol invocation transport error: {exc}",
                details={"protocol": protocol, "url": url},
            ) from exc

        latency_ms = round((time.monotonic() - started_at) * 1000, 3)
        return InvocationResult(
            protocol=protocol,
            target_url=url,
            status_code=response.status_code,
            ok=200 <= response.status_code < 300,
            latency_ms=latency_ms,
            response=parse_response_data(response),
            response_headers=dict(response.headers),
        )
