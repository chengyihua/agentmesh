import sys
import unittest
from typing import Any, Dict, Optional

import httpx
from fastapi.testclient import TestClient

sys.path.insert(0, "src")

from agentmesh.api.server import create_server
from agentmesh.protocols import InvocationRequest, InvocationResult, ProtocolGateway


class FakeRequester:
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
        request = httpx.Request(method, url)
        return httpx.Response(
            status_code=200,
            json={"remote_ok": True, "url": url, "method": method, "echo": json_body or params},
            headers={"content-type": "application/json"},
            request=request,
        )


class TestInvokeAPI(unittest.TestCase):
    def setUp(self) -> None:
        async def fake_ws(request: InvocationRequest) -> InvocationResult:
            return InvocationResult(
                protocol="websocket",
                target_url="ws://example-ws.test",
                status_code=200,
                ok=True,
                latency_ms=1.0,
                response={"remote_ok": True, "echo": request.payload},
                response_headers={},
            )

        async def fake_grpc(request: InvocationRequest) -> InvocationResult:
            return InvocationResult(
                protocol="grpc",
                target_url="grpc://example-grpc.test/pkg.Service/Method",
                status_code=200,
                ok=True,
                latency_ms=2.0,
                response={"remote_ok": True, "echo": request.payload},
                response_headers={},
            )

        server = create_server(debug=False)
        server.registry.protocol_gateway = ProtocolGateway(
            http_request=FakeRequester().__call__,
            websocket_invoke=fake_ws,
            grpc_invoke=fake_grpc,
        )
        self.client = TestClient(server.app)

    def _register(self, agent_id: str, protocol: str, endpoint: str = "https://example-agent.test"):
        payload = {
            "id": agent_id,
            "name": f"{agent_id}-name",
            "version": "1.0.0",
            "skills": [{"name": "run", "description": "run"}],
            "endpoint": endpoint,
            "protocol": protocol,
            "health_status": "healthy",
        }
        response = self.client.post("/api/v1/agents/register", json=payload)
        self.assertEqual(response.status_code, 201)

    def test_invoke_http_mcp_websocket_grpc(self):
        self._register("http-agent-001", "http")
        self._register("mcp-agent-001", "mcp")
        self._register("ws-agent-001", "websocket", endpoint="ws://example-ws.test")
        self._register("grpc-agent-001", "grpc")

        http_resp = self.client.post(
            "/api/v1/agents/http-agent-001/invoke",
            json={"payload": {"ping": "pong"}, "path": "/work", "method": "POST"},
        )
        self.assertEqual(http_resp.status_code, 200)
        self.assertTrue(http_resp.json()["success"])
        self.assertEqual(http_resp.json()["data"]["result"]["response"]["remote_ok"], True)

        mcp_resp = self.client.post(
            "/api/v1/agents/mcp-agent-001/invoke",
            json={"skill": "tool.call", "payload": {"input": 1}},
        )
        self.assertEqual(mcp_resp.status_code, 200)
        self.assertEqual(mcp_resp.json()["data"]["result"]["protocol"], "mcp")

        ws_resp = self.client.post(
            "/api/v1/agents/ws-agent-001/invoke",
            json={"payload": {"input": 2}},
        )
        self.assertEqual(ws_resp.status_code, 200)
        self.assertEqual(ws_resp.json()["data"]["result"]["protocol"], "websocket")

        grpc_resp = self.client.post(
            "/api/v1/agents/grpc-agent-001/invoke",
            json={"payload": {"input": 1}, "path": "/pkg.Service/Method"},
        )
        self.assertEqual(grpc_resp.status_code, 200)
        self.assertEqual(grpc_resp.json()["data"]["result"]["protocol"], "grpc")

        stats_resp = self.client.get("/api/v1/agents/http-agent-001/stats")
        self.assertEqual(stats_resp.status_code, 200)
        data = stats_resp.json()["data"]
        self.assertGreaterEqual(data["invocations"], 1)
