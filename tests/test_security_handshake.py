import pytest
import json
from datetime import datetime, timezone, timedelta
from agentmesh.core.security import SecurityManager
from agentmesh.core.agent_card import AgentCard
from agentmesh.api.server import AgentMeshServer
from fastapi.testclient import TestClient

class TestSecurityHandshake:
    def setup_method(self):
        self.security = SecurityManager()
        self.keys = self.security.generate_key_pair()
        self.private_key = self.keys["private_key"]
        self.public_key = self.keys["public_key"]
        self.agent_id = self.security.derive_agent_id(self.public_key)

    def test_sign_and_verify(self):
        method = "POST"
        path = "/api/v1/invoke"
        timestamp = datetime.now(timezone.utc).isoformat()
        body = {"foo": "bar"}
        body_hash = self.security.hash_body(body)
        
        signature = self.security.create_handshake_token(
            method, path, timestamp, body_hash, self.private_key
        )
        
        assert self.security.verify_handshake_token(
            method, path, timestamp, body_hash, signature, self.public_key
        )

    def test_verify_fails_on_tampering(self):
        method = "POST"
        path = "/api/v1/invoke"
        timestamp = datetime.now(timezone.utc).isoformat()
        body = {"foo": "bar"}
        body_hash = self.security.hash_body(body)
        
        signature = self.security.create_handshake_token(
            method, path, timestamp, body_hash, self.private_key
        )
        
        # Tamper body hash
        assert not self.security.verify_handshake_token(
            method, path, timestamp, "tampered_hash", signature, self.public_key
        )
        
        # Tamper timestamp
        assert not self.security.verify_handshake_token(
            method, path, "2025-01-01T00:00:00Z", body_hash, signature, self.public_key
        )

    def test_verify_fails_on_expiry(self):
        method = "POST"
        path = "/api/v1/invoke"
        # 61 seconds ago
        expired_time = (datetime.now(timezone.utc) - timedelta(seconds=61)).isoformat()
        body = {"foo": "bar"}
        body_hash = self.security.hash_body(body)
        
        signature = self.security.create_handshake_token(
            method, path, expired_time, body_hash, self.private_key
        )
        
        assert not self.security.verify_handshake_token(
            method, path, expired_time, body_hash, signature, self.public_key
        )

@pytest.mark.asyncio
async def test_api_handshake_integration():
    server = AgentMeshServer()
    security = server.security_manager
    keys = security.generate_key_pair()
    caller_id = security.derive_agent_id(keys["public_key"])
    
    # Register caller so server knows public key
    caller_card = AgentCard(
        id=caller_id,
        name="Caller",
        version="1.0",
        endpoint="http://caller",
        public_key=keys["public_key"],
        skills=[{"name": "test", "description": "test"}]
    )
    await server.registry.register_agent(caller_card)
    
    # Register target
    target_card = AgentCard(
        id="target",
        name="Target",
        version="1.0",
        endpoint="http://target",
        skills=[{"name": "test", "description": "test"}]
    )
    await server.registry.register_agent(target_card)
    
    # Mock invoke_agent to avoid network call
    async def mock_invoke(*args, **kwargs):
        return {"status": "mocked_success"}
    server.registry.invoke_agent = mock_invoke

    with TestClient(server.app) as client:
        method = "POST"
        path = "/api/v1/agents/target/invoke"
        body = {"payload": {"test": "data"}, "method": "POST", "timeout_seconds": 30.0}
        
        timestamp = datetime.now(timezone.utc).isoformat()
        # Note: client.post(json=...) uses default json encoder
        # security.hash_body uses json.dumps(sort_keys=True)
        # We must ensure what the server receives is what we hashed.
        # TestClient sends standard JSON. 
        # Server's verify_handshake calls security.hash_body(await request.json()).
        # request.json() returns a dict. security.hash_body(dict) sorts keys.
        # So as long as we pass the dict to hash_body here, it matches.
        body_hash = security.hash_body(body)
        
        signature = security.create_handshake_token(
            method, path, timestamp, body_hash, keys["private_key"]
        )
        
        headers = {
            "X-Agent-ID": caller_id,
            "X-Agent-Timestamp": timestamp,
            "X-Agent-Signature": signature
        }
        
        response = client.post(path, json=body, headers=headers)
        assert response.status_code == 200, f"Response: {response.text}"
        assert response.json()["data"]["result"]["status"] == "mocked_success"
        
        # Test invalid signature
        headers["X-Agent-Signature"] = "invalid"
        response = client.post(path, json=body, headers=headers)
        assert response.status_code == 401
