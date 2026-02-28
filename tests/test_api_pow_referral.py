
import pytest
import hashlib
import asyncio
from fastapi.testclient import TestClient
from agentmesh.api.server import create_server
from agentmesh.core.trust import TrustEvent

@pytest.fixture
def client_and_registry():
    # Set an API key so that requests without it are considered unauthenticated
    # and thus require PoW.
    server = create_server(debug=False, api_key="secret-key")
    app = server.app
    # Lower difficulty for testing
    app.state.registry.pow_manager.difficulty = 2
    client = TestClient(app)
    return client, app.state.registry

def solve_pow(nonce, difficulty):
    prefix = "0" * difficulty
    for i in range(1000000):
        solution = str(i)
        data = f"{nonce}{solution}".encode("utf-8")
        digest = hashlib.sha256(data).hexdigest()
        if digest.startswith(prefix):
            return solution
    return None

def test_pow_enforcement(client_and_registry):
    client, registry = client_and_registry
    
    agent_payload = {
        "id": "pow-agent-1",
        "name": "PoW Agent",
        "version": "1.0.0",
        "skills": [{"name": "test", "description": "test"}],
        "endpoint": "http://localhost:8000"
    }

    # 1. Try registering without PoW -> Should Fail (400)
    response = client.post("/api/v1/agents/register", json=agent_payload)
    assert response.status_code == 400
    # Custom error handler wraps details in "error" object
    assert "PoW required" in response.json()["error"]["message"]

    # 2. Get Challenge
    resp = client.get("/api/v1/auth/challenge")
    assert resp.status_code == 200
    data = resp.json()["data"]
    nonce = data["nonce"]
    difficulty = data["difficulty"]
    assert difficulty == 2

    # 3. Solve PoW
    solution = solve_pow(nonce, difficulty)
    assert solution is not None

    # 4. Register with PoW -> Should Succeed (201)
    headers = {
        "X-PoW-Nonce": nonce,
        "X-PoW-Solution": solution
    }
    response = client.post("/api/v1/agents/register", json=agent_payload, headers=headers)
    assert response.status_code == 201
    assert response.json()["data"]["agent_id"] == "pow-agent-1"

    # 5. Replay Attack -> Should Fail (400) - Nonce consumed
    response = client.post("/api/v1/agents/register", json={**agent_payload, "id": "pow-agent-2"}, headers=headers)
    assert response.status_code == 400
    assert "Invalid PoW" in response.json()["error"]["message"]

@pytest.mark.asyncio
async def test_referral_system(client_and_registry):
    client, registry = client_and_registry
    
    # Setup: Register Referrer
    referrer_id = "referrer-agent"
    # Bypass PoW for setup by using internal register call or mock
    # Or just solve PoW again (easy with diff=2)
    nonce = registry.pow_manager.create_challenge()
    solution = solve_pow(nonce, 2)
    
    referrer_payload = {
        "id": referrer_id,
        "name": "Referrer",
        "version": "1.0.0",
        "skills": [{"name": "ref", "description": "ref"}],
        "endpoint": "http://localhost:8001"
    }
    client.post("/api/v1/agents/register", json=referrer_payload, headers={
        "X-PoW-Nonce": nonce,
        "X-PoW-Solution": solution
    })
    
    # Verify referrer exists and get initial score
    ref_agent = await registry.get_agent(referrer_id)
    initial_score = ref_agent.trust_score or 0.5
    
    # 2. Register New Agent via /hello with referrer
    resp = client.post("/hello", json={"id": "new-agent", "referrer": referrer_id})
    assert resp.status_code == 200
    new_agent_id = resp.json()["agent_id"]
    
    # Verify new agent has referrer_id set
    new_agent = await registry.get_agent(new_agent_id)
    assert new_agent.referrer_id == referrer_id
    assert new_agent.referral_paid is False
    
    # 3. Simulate Interactions (Success events)
    trust_manager = registry.trust_manager
    
    # Interaction 1-4 (Should not trigger bonus)
    for i in range(4):
        await trust_manager.record_event(new_agent_id, TrustEvent.SUCCESS, source_agent_id=f"peer-{i}")
        
    # Verify no bonus yet
    # We need to wait a bit as bonus is async task? 
    # Actually record_event for bonus is awaited or created as task.
    # We can check referral_paid flag
    new_agent = await registry.get_agent(new_agent_id)
    assert new_agent.referral_paid is False
    
    # Interaction 5 (Should trigger bonus)
    await trust_manager.record_event(new_agent_id, TrustEvent.SUCCESS, source_agent_id="peer-5")
    
    # Wait for async tasks (referral bonus task)
    await asyncio.sleep(0.1)
    
    # Verify bonus paid
    new_agent = await registry.get_agent(new_agent_id)
    assert new_agent.referral_paid is True
    
    # Verify referrer score increased
    # Bonus is TrustEvent.SUCCESS (0.05) or INVOCATION?
    # Code: await self.record_event(referrer_id, TrustEvent.SUCCESS, "system_referral_bonus")
    # So referrer should get +0.05
    
    # Force flush or check memory
    # TrustManager flushes every 10s. We can check trust_manager.scores
    referrer_score = await trust_manager.get_score(referrer_id)
    assert referrer_score > initial_score
    
    # Also verify Diversity Factor
    # Record event with SAME peer -> Should have diminishing returns
    # But trust_manager.record_event logic: if source==last, reduce delta.
    
    # Reset score for testing diversity
    # Manually set score to 0.5
    trust_manager.scores[new_agent_id] = 0.5
    
    # 1. First interaction with peer-X
    await trust_manager.record_event(new_agent_id, TrustEvent.SUCCESS, source_agent_id="peer-X")
    score_1 = trust_manager.scores[new_agent_id]
    delta_1 = score_1 - 0.5
    assert delta_1 > 0.04 # approx 0.05
    
    # 2. Second interaction with SAME peer-X -> Should be penalized
    await trust_manager.record_event(new_agent_id, TrustEvent.SUCCESS, source_agent_id="peer-X")
    score_2 = trust_manager.scores[new_agent_id]
    delta_2 = score_2 - score_1
    
    # Check penalty (should be ~50% of delta_1)
    assert delta_2 < delta_1
    assert delta_2 > 0
    
