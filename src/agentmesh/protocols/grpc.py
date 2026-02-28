"""gRPC protocol bridge."""

from __future__ import annotations

import base64
import json
import time
from typing import Any, Awaitable, Callable, Dict, Iterable, Optional, Tuple
from urllib.parse import urlparse

from .base import InvocationRequest, InvocationResult, ProtocolInvocationError, ProtocolTransportError

GrpcInvokeFn = Callable[[InvocationRequest], Awaitable[InvocationResult]]


def _resolve_grpc_target(endpoint: str) -> str:
    if "://" not in endpoint:
        return endpoint.lstrip("/")

    parsed = urlparse(endpoint)
    if parsed.scheme in {"grpc", "http", "https", "ws", "wss"}:
        if parsed.netloc:
            return parsed.netloc
        if parsed.path:
            return parsed.path.lstrip("/")
    if parsed.scheme:
        return parsed.path.lstrip("/")
    return endpoint.lstrip("/")


def _build_grpc_request_bytes(payload: Dict[str, Any]) -> bytes:
    if "body_base64" in payload:
        return base64.b64decode(str(payload["body_base64"]))
    if "body_text" in payload:
        return str(payload["body_text"]).encode("utf-8")
    if "body_bytes" in payload and isinstance(payload["body_bytes"], list):
        return bytes(payload["body_bytes"])
    return json.dumps(payload).encode("utf-8")


def _parse_grpc_response_bytes(raw: bytes) -> Any:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return {"body_base64": base64.b64encode(raw).decode("utf-8")}

    try:
        return json.loads(text)
    except ValueError:
        return text


def _headers_to_metadata(headers: Dict[str, str]) -> Iterable[Tuple[str, str]]:
    return [(key.lower(), value) for key, value in headers.items()]


class GrpcProtocolHandler:
    """gRPC invoke bridge based on unary-unary generic call."""

    def __init__(self, grpc_invoke: Optional[GrpcInvokeFn] = None):
        self._grpc_invoke = grpc_invoke

    async def invoke(self, request: InvocationRequest) -> InvocationResult:
        if self._grpc_invoke is not None:
            return await self._grpc_invoke(request)
        return await self._invoke_real(request)

    async def _invoke_real(self, request: InvocationRequest) -> InvocationResult:
        try:
            import grpc
        except ImportError as exc:
            raise ProtocolTransportError("grpcio package is required for grpc protocol invocation") from exc

        rpc_method = request.path or ""
        if not rpc_method.startswith("/"):
            raise ProtocolInvocationError(
                "gRPC invocation requires path like '/package.Service/Method'",
                status_code=400,
            )

        target = _resolve_grpc_target(request.endpoint)
        request_bytes = _build_grpc_request_bytes(request.payload or {})
        metadata = tuple(_headers_to_metadata(request.headers or {}))

        started_at = time.monotonic()
        channel = grpc.aio.insecure_channel(target)
        try:
            unary_call = channel.unary_unary(
                rpc_method,
                request_serializer=lambda item: item,
                response_deserializer=lambda item: item,
            )
            response_bytes = await unary_call(request_bytes, timeout=request.timeout_seconds, metadata=metadata)
        except Exception as exc:
            raise ProtocolTransportError(
                f"gRPC protocol invocation failed: {exc}",
                details={"protocol": "grpc", "target": target, "path": rpc_method},
            ) from exc
        finally:
            await channel.close()

        latency_ms = round((time.monotonic() - started_at) * 1000, 3)
        parsed_response = _parse_grpc_response_bytes(response_bytes)
        return InvocationResult(
            protocol="grpc",
            target_url=f"grpc://{target}{rpc_method}",
            status_code=200,
            ok=True,
            latency_ms=latency_ms,
            response=parsed_response,
            response_headers={},
        )
