import pytest
from agentmesh.core.agent_card import AgentCard

@pytest.mark.asyncio
async def test_register_connect_invoke(api_client):
    # 1. Register Agent A
    agent_a = {
        "id": "agent-a",
        "name": "Agent A",
        "version": "1.0.0",
        "endpoint": "http://localhost:8001",
        "skills": [{"name": "echo", "description": "echoes input"}]
    }
    resp = api_client.post("/api/v1/agents", json=agent_a)
    assert resp.status_code == 201

    # 2. Register Agent B
    agent_b = {
        "id": "agent-b",
        "name": "Agent B",
        "version": "1.0.0",
        "endpoint": "http://localhost:8002",
        "skills": [{"name": "ask", "description": "asks questions"}]
    }
    resp = api_client.post("/api/v1/agents", json=agent_b)
    assert resp.status_code == 201

    # 3. Discovery
    resp = api_client.get("/api/v1/agents?skill=echo")
    data = resp.json()
    assert len(data["data"]["agents"]) >= 1
    # Check if agent-a is in the list
    agent_ids = [agent["id"] for agent in data["data"]["agents"]]
    assert "agent-a" in agent_ids

    # 4. Health Check (Simulated)
    # Trigger heartbeat
    resp = api_client.post("/api/v1/agents/agent-a/heartbeat", json={"status": "healthy"})
    assert resp.status_code == 200

    # 5. Check Leaderboard
    resp = api_client.get("/api/v1/agents/leaderboard")
    assert resp.status_code == 200
