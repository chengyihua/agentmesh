
import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient
from agentmesh.api.server import AgentMeshServer
from agentmesh.core.agent_card import AgentCard, HealthStatus
from agentmesh.core.trust import TrustEvent

# Use pytest-asyncio for async tests
pytestmark = pytest.mark.asyncio

@pytest.fixture
def test_app():
    # Mock VectorIndexManager to avoid loading models
    mock_vector_index = AsyncMock()
    mock_vector_index.search.return_value = []
    mock_vector_index.add_agent.return_value = None
    
    server = AgentMeshServer(debug=True, vector_index=mock_vector_index)
    return server.app, server

@pytest.fixture
def client(test_app):
    app, _ = test_app
    return TestClient(app)

async def test_rate_limit_trust_impact(client, test_app):
    app, server = test_app
    registry = server.registry
    trust_manager = registry.trust_manager
    
    # 1. Register a test agent with low QPS budget
    agent_id = "limited-agent"
    agent = AgentCard(
        id=agent_id,
        name="Limited Agent",
        version="1.0.0",
        description="Test agent for rate limiting",
        health_status=HealthStatus.HEALTHY,
        skills=[{"name": "echo", "description": "echo"}],  # Fixed skills format
        qps_budget=0.5,  # 1 request every 2 seconds
        concurrency_limit=10,
        endpoint="http://localhost:8000" # Required field
    )
    
    # Manually register to bypass signature check if enabled (server defaults to false anyway)
    await registry.register_agent(agent)
    
    # Verify initial trust score (should be 0.5 default)
    score = await registry.calculate_trust_score(agent_id)
    assert score == 0.5
    
    # 2. Send requests to trigger rate limit
    # First request should succeed (bucket has capacity)
    # This consumes the token (1.0)
    response = client.post(f"/api/v1/agents/{agent_id}/invoke", json={
        "payload": {"msg": "hello"},
        "method": "POST"
    })
    
    # Send second request immediately
    # Token bucket is empty (0.0 < 1.0), so this should be rate limited
    response = client.post(f"/api/v1/agents/{agent_id}/invoke", json={
        "payload": {"msg": "hello"},
        "method": "POST"
    })
    
    print(f"Response status: {response.status_code}")
    print(f"Response json: {response.json()}")
    
    assert response.status_code == 429
    error_data = response.json()["error"]
    assert error_data["message"] == "Rate limit exceeded"
    assert error_data["details"]["reason"] == "Rate limit exceeded"
    
    # 3. Check trust score
    # First request failed (invokation failure: -0.10) because no backend
    # Second request rate limited (-0.02)
    # Total expected drop: 0.12
    new_score = await registry.calculate_trust_score(agent_id)
    # Allow some float precision error
    expected_score = 0.5 - 0.10 - 0.02
    assert abs(new_score - expected_score) < 0.001
    
    # 4. Verify discovery filtering
    # Default min_trust is None, so agent should appear
    response = client.get("/api/v1/agents/discover", params={"q": "echo"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert any(a["id"] == agent_id for a in data["agents"])
    
    # Filter with min_trust=0.35 (should still appear, score ~0.38)
    response = client.get("/api/v1/agents/discover", params={"q": "echo", "min_trust": 0.35})
    data = response.json()["data"]
    assert any(a["id"] == agent_id for a in data["agents"])
    
    # Filter with min_trust=0.40 (should disappear, score ~0.38 < 0.40)
    response = client.get("/api/v1/agents/discover", params={"q": "echo", "min_trust": 0.40})
    data = response.json()["data"]
    assert not any(a["id"] == agent_id for a in data["agents"])

