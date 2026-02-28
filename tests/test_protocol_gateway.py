import asyncio
import sys
import unittest
from typing import Any, Dict, Optional

import httpx

sys.path.insert(0, "src")

from agentmesh.core.agent_card import AgentCard, Skill
from agentmesh.protocols import InvocationRequest, InvocationResult, ProtocolGateway, ProtocolNotImplementedError


class FakeRequester:
    def __init__(self):
        self.calls = []

    async def __call__(
        self,
        *,
        method: str,
        url: str,
        timeout: float,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Any] = None,
    ) -> httpx.Response:
        self.calls.append(
            {
                "method": method,
                "url": url,
                "timeout": timeout,
                "headers": headers or {},
                "params": params,
                "json_body": json_body,
            }
        )
        request = httpx.Request(method, url)
        payload = {"ok": True, "echo": {"params": params, "json_body": json_body}}
        return httpx.Response(
            status_code=200,
            json=payload,
            headers={"content-type": "application/json"},
            request=request,
        )


def _agent(agent_id: str, protocol: str, endpoint: str) -> AgentCard:
    return AgentCard(
        id=agent_id,
        name=f"{agent_id}-name",
        version="1.0.0",
        skills=[Skill(name="run", description="run")],
        endpoint=endpoint,
        protocol=protocol,
    )


class TestProtocolGateway(unittest.TestCase):
    def test_http_custom_a2a_mcp_dispatch(self):
        async def _run():
            fake = FakeRequester()
            gateway = ProtocolGateway(http_request=fake.__call__)

            http_result = await gateway.invoke(
                _agent("http-agent", "http", "https://example-http.test"),
                InvocationRequest(
                    agent_id="http-agent",
                    endpoint="https://example-http.test",
                    protocol="http",
                    payload={"message": "hello"},
                    path="/invoke",
                ),
            )
            self.assertTrue(http_result.ok)
            self.assertEqual(http_result.status_code, 200)
            self.assertEqual(fake.calls[0]["url"], "https://example-http.test/invoke")

            a2a_result = await gateway.invoke(
                _agent("a2a-agent", "a2a", "https://example-a2a.test"),
                InvocationRequest(
                    agent_id="a2a-agent",
                    endpoint="https://example-a2a.test",
                    protocol="a2a",
                    skill="summarize",
                    payload={"text": "abc"},
                ),
            )
            self.assertTrue(a2a_result.ok)
            self.assertEqual(fake.calls[1]["url"], "https://example-a2a.test/a2a/invoke")
            self.assertEqual(fake.calls[1]["json_body"]["skill"], "summarize")

            mcp_result = await gateway.invoke(
                _agent("mcp-agent", "mcp", "https://example-mcp.test"),
                InvocationRequest(
                    agent_id="mcp-agent",
                    endpoint="https://example-mcp.test",
                    protocol="mcp",
                    skill="get_weather",
                    payload={"city": "Tokyo"},
                ),
            )
            self.assertTrue(mcp_result.ok)
            self.assertEqual(fake.calls[2]["url"], "https://example-mcp.test/mcp/invoke")
            self.assertEqual(fake.calls[2]["json_body"]["method"], "tools/call")

        asyncio.run(_run())

    def test_websocket_and_grpc_dispatch(self):
        async def _fake_ws(request: InvocationRequest) -> InvocationResult:
            return InvocationResult(
                protocol="websocket",
                target_url="ws://example",
                status_code=200,
                ok=True,
                latency_ms=1.0,
                response={"ws": request.payload},
                response_headers={},
            )

        async def _fake_grpc(request: InvocationRequest) -> InvocationResult:
            return InvocationResult(
                protocol="grpc",
                target_url="grpc://example/service.Method",
                status_code=200,
                ok=True,
                latency_ms=2.0,
                response={"grpc": request.payload},
                response_headers={},
            )

        async def _run():
            gateway = ProtocolGateway(websocket_invoke=_fake_ws, grpc_invoke=_fake_grpc)

            ws_result = await gateway.invoke(
                _agent("ws-agent", "websocket", "ws://example-ws.test"),
                InvocationRequest(
                    agent_id="ws-agent",
                    endpoint="ws://example-ws.test",
                    protocol="websocket",
                    payload={"x": 1},
                ),
            )
            self.assertTrue(ws_result.ok)
            self.assertEqual(ws_result.protocol, "websocket")

            grpc_result = await gateway.invoke(
                _agent("grpc-agent", "grpc", "localhost:50051"),
                InvocationRequest(
                    agent_id="grpc-agent",
                    endpoint="localhost:50051",
                    protocol="grpc",
                    payload={"y": 2},
                    path="/pkg.Service/Method",
                ),
            )
            self.assertTrue(grpc_result.ok)
            self.assertEqual(grpc_result.protocol, "grpc")

        asyncio.run(_run())

    def test_unimplemented_protocol(self):
        async def _run():
            gateway = ProtocolGateway()
            gateway._handlers.pop("custom", None)
            with self.assertRaises(ProtocolNotImplementedError):
                await gateway.invoke(
                    _agent("custom-agent", "custom", "https://example.test"),
                    InvocationRequest(
                        agent_id="custom-agent",
                        endpoint="https://example.test",
                        protocol="custom",
                        payload={"x": 1},
                    ),
                )

        asyncio.run(_run())
