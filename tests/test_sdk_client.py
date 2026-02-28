import asyncio
import sys
import unittest

import httpx

sys.path.insert(0, "src")

from agentmesh import AgentMeshClient
from agentmesh.api.server import create_server
from agentmesh.protocols import ProtocolGateway


class _FakeRequester:
    async def __call__(self, *, method, url, timeout, headers=None, params=None, json_body=None):
        request = httpx.Request(method, url)
        return httpx.Response(
            status_code=200,
            json={"remote_ok": True, "url": url, "echo": json_body or params},
            headers={"content-type": "application/json"},
            request=request,
        )


class TestAgentMeshClient(unittest.TestCase):
    def test_async_client_with_asgi_transport(self):
        async def _run_test():
            server = create_server(debug=False)
            server.registry.protocol_gateway = ProtocolGateway(http_request=_FakeRequester().__call__)
            app = server.app
            transport = httpx.ASGITransport(app=app)

            client = AgentMeshClient(base_url="http://testserver")
            await client._client.aclose()
            client._client = httpx.AsyncClient(transport=transport, base_url="http://testserver")

            payload = {
                "id": "sdk-bot-001",
                "name": "SDKBOT",
                "version": "1.0.0",
                "skills": [{"name": "echo", "description": "Echo"}],
                "endpoint": "http://localhost:9000/echo",
                "protocol": "http",
                "health_status": "healthy",
            }

            register_resp = await client.register_agent(payload)
            self.assertTrue(register_resp["success"])

            search_resp = await client.search_agents(skill="echo")
            self.assertEqual(len(search_resp["data"]["results"]), 1)

            stats_resp = await client.get_stats()
            self.assertEqual(stats_resp["data"]["total_agents"], 1)

            invoke_resp = await client.invoke_agent(
                "sdk-bot-001",
                payload={"message": "hello"},
                path="/invoke",
            )
            self.assertTrue(invoke_resp["success"])
            self.assertTrue(invoke_resp["data"]["result"]["ok"])

            await client.close()

        asyncio.run(_run_test())

    def test_client_signing(self):
        from agentmesh.core.security import SecurityManager
        
        async def _run_test():
            security = SecurityManager()
            keys = security.generate_key_pair()
            agent_id = security.derive_agent_id(keys["public_key"])
            private_key = keys["private_key"]
            
            client = AgentMeshClient(
                base_url="http://test",
                private_key=private_key,
                agent_id=agent_id
            )
            
            # Check internal method _get_auth_headers
            headers = client._get_auth_headers("POST", "/test", {"foo": "bar"})
            self.assertEqual(headers["X-Agent-ID"], agent_id)
            self.assertIn("X-Agent-Timestamp", headers)
            self.assertIn("X-Agent-Signature", headers)
            
            # Verify signature
            body_hash = security.hash_body({"foo": "bar"})
            valid = security.verify_handshake_token(
                "POST", "/test", headers["X-Agent-Timestamp"], body_hash, headers["X-Agent-Signature"], keys["public_key"]
            )
            self.assertTrue(valid)
            
            await client.close()
            
        asyncio.run(_run_test())


if __name__ == "__main__":
    unittest.main()
