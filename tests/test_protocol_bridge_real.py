import asyncio
import json
import sys
import unittest

sys.path.insert(0, "src")

from agentmesh.core.agent_card import AgentCard, Skill
from agentmesh.protocols import InvocationRequest, ProtocolGateway


def _agent(agent_id: str, protocol: str, endpoint: str) -> AgentCard:
    return AgentCard(
        id=agent_id,
        name=f"{agent_id}-name",
        version="1.0.0",
        skills=[Skill(name="run", description="run")],
        endpoint=endpoint,
        protocol=protocol,
    )


class TestProtocolBridgeReal(unittest.TestCase):
    def test_websocket_bridge_real(self):
        try:
            import websockets
        except ImportError:
            self.skipTest("websockets not installed")

        async def _run():
            async def ws_handler(websocket):
                raw = await websocket.recv()
                payload = json.loads(raw)
                await websocket.send(json.dumps({"ok": True, "echo": payload}))

            try:
                server = await websockets.serve(ws_handler, "127.0.0.1", 0)
            except PermissionError as exc:
                raise unittest.SkipTest(f"websocket bind not permitted in this environment: {exc}") from exc
            port = server.sockets[0].getsockname()[1]
            try:
                gateway = ProtocolGateway()
                agent = _agent("ws-real-001", "websocket", f"127.0.0.1:{port}")
                result = await gateway.invoke(
                    agent,
                    InvocationRequest(
                        agent_id=agent.id,
                        endpoint=str(agent.endpoint),
                        protocol="websocket",
                        payload={"message": "hello"},
                    ),
                )
                self.assertTrue(result.ok)
                self.assertEqual(result.protocol, "websocket")
                self.assertEqual(result.response["echo"]["payload"]["message"], "hello")
            finally:
                server.close()
                await server.wait_closed()

        asyncio.run(_run())

    def test_grpc_bridge_real(self):
        try:
            import grpc
        except ImportError:
            self.skipTest("grpcio not installed")

        async def _run():
            def grpc_handler(raw: bytes, _context):
                data = json.loads(raw.decode("utf-8"))
                return json.dumps({"ok": True, "echo": data}).encode("utf-8")

            server = grpc.aio.server()
            handler = grpc.unary_unary_rpc_method_handler(
                grpc_handler,
                request_deserializer=lambda item: item,
                response_serializer=lambda item: item,
            )
            generic = grpc.method_handlers_generic_handler("agentmesh.Invoke", {"Call": handler})
            server.add_generic_rpc_handlers((generic,))
            try:
                port = server.add_insecure_port("127.0.0.1:0")
            except PermissionError as exc:
                raise unittest.SkipTest(f"grpc bind not permitted in this environment: {exc}") from exc
            if port == 0:
                raise unittest.SkipTest("grpc bind failed in this environment")
            await server.start()
            try:
                gateway = ProtocolGateway()
                agent = _agent("grpc-real-001", "grpc", f"127.0.0.1:{port}")
                result = await gateway.invoke(
                    agent,
                    InvocationRequest(
                        agent_id=agent.id,
                        endpoint=str(agent.endpoint),
                        protocol="grpc",
                        payload={"value": 42},
                        path="/agentmesh.Invoke/Call",
                    ),
                )
                self.assertTrue(result.ok)
                self.assertEqual(result.protocol, "grpc")
                self.assertEqual(result.response["echo"]["value"], 42)
            finally:
                await server.stop(0)

        asyncio.run(_run())
