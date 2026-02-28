import pytest
import asyncio
from agentmesh.api.server import AgentMeshServer
from agentmesh.core.agent_card import AgentCard
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

@pytest.mark.asyncio
async def test_qps_limit():
    server = AgentMeshServer()
    # Register agent with QPS=1
    agent = AgentCard(
        id="qps-agent",
        name="QPS Agent",
        version="1.0",
        endpoint="http://mock",
        qps_budget=1,
        skills=[{"name": "test", "description": "test"}]
    )
    await server.registry.register_agent(agent)
    
    # Mock invoke
    async def mock_invoke(*args, **kwargs):
        return {"status": "ok"}
    server.registry.invoke_agent = mock_invoke
    
    with TestClient(server.app) as client:
        # First call OK
        resp1 = client.post("/api/v1/agents/qps-agent/invoke", json={"payload": {}})
        assert resp1.status_code == 200
        
        # Second call immediately -> 429
        resp2 = client.post("/api/v1/agents/qps-agent/invoke", json={"payload": {}})
        print(f"Resp2: {resp2.status_code} {resp2.text}")
        assert resp2.status_code == 429
        assert "Rate limit exceeded" in str(resp2.json())

@pytest.mark.asyncio
async def test_concurrency_limit():
    server = AgentMeshServer()
    # Register agent with Concurrency=1
    agent = AgentCard(
        id="conc-agent",
        name="Conc Agent",
        version="1.0",
        endpoint="http://mock",
        concurrency_limit=1,
        skills=[{"name": "test", "description": "test"}]
    )
    await server.registry.register_agent(agent)
    
    # Mock slow invoke
    async def mock_invoke(*args, **kwargs):
        await asyncio.sleep(0.2)
        return {"status": "ok"}
    server.registry.invoke_agent = mock_invoke
    
    async with AsyncClient(transport=ASGITransport(app=server.app), base_url="http://test") as client:
        # Launch two requests concurrently
        # Note: In asyncio, we need to ensure they actually run in parallel on the server.
        # Since FastAPI runs in same loop here, we rely on `await` in mock_invoke yielding control.
        
        t1 = asyncio.create_task(client.post("/api/v1/agents/conc-agent/invoke", json={"payload": {}}))
        # Small sleep to ensure t1 starts and acquires lock
        await asyncio.sleep(0.01)
        t2 = asyncio.create_task(client.post("/api/v1/agents/conc-agent/invoke", json={"payload": {}}))
        
        r1 = await t1
        r2 = await t2
        
        # One should succeed, one should fail
        status_codes = {r1.status_code, r2.status_code}
        assert 200 in status_codes
        assert 429 in status_codes
