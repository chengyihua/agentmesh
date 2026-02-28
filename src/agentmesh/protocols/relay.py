"""Relay protocol handler implementation."""

from typing import Optional

from .base import (
    InvocationRequest,
    InvocationResult,
    RelayInvokeFn,
    ProtocolNotImplementedError,
)


class RelayProtocolHandler:
    """Handles invocations via the Relay Network."""

    def __init__(self, relay_invoke: Optional[RelayInvokeFn] = None):
        self.relay_invoke_fn = relay_invoke

    async def invoke(self, request: InvocationRequest) -> InvocationResult:
        if not self.relay_invoke_fn:
            raise ProtocolNotImplementedError("Relay invocation function not configured")
        
        return await self.relay_invoke_fn(request.agent_id, request)
