import pytest
from httpx import AsyncClient, ASGITransport
from agentmesh.api.server import AgentMeshServer

@pytest.fixture
async def client(unused_tcp_port):
    server = AgentMeshServer(port=unused_tcp_port)
    transport = ASGITransport(app=server.app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_get_trust_score(client):
    # Register an agent first
    agent_id = "trust-test-agent"
    response = await client.post("/api/v1/agents/register", json={
        "id": agent_id,
        "name": "Trust Agent",
        "version": "1.0.0",
        "endpoint": "http://localhost:8000",
        "skills": [{"name": "test", "description": "test"}]
    })
    assert response.status_code == 201

    # Get trust score
    response = await client.get(f"/api/v1/agents/{agent_id}/trust")
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["success"] is True
    data = json_response["data"]
    assert data["agent_id"] == agent_id
    assert data["trust_score"] == 0.5

@pytest.mark.asyncio
async def test_get_trust_score_not_found(client):
    response = await client.get("/api/v1/agents/non-existent-agent/trust")
    assert response.status_code == 404
