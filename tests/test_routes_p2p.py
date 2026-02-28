
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from agentmesh.api.server import AgentMeshServer
from agentmesh.core.agent_card import AgentCard, Skill

@pytest.fixture
def mock_registry():
    registry = AsyncMock()
    registry.get_agent.return_value = AgentCard(
        id="test-agent",
        name="Test Agent",
        version="1.0.0",
        skills=[Skill(name="sys.p2p.handshake", description="P2P Handshake Skill")],
        endpoint="http://localhost:8000",
        protocol="http"
    )
    registry.trust_manager = MagicMock()
    # Ensure rate limiter works
    registry.trust_manager.get_trust_score = AsyncMock(return_value=1.0)
    return registry

@pytest.fixture
def client(mock_registry):
    # Patch dependencies to avoid side effects
    with patch("agentmesh.api.server.P2PNode") as MockP2PNode, \
         patch("agentmesh.api.server.RedisStorage"), \
         patch("agentmesh.api.server.PostgresStorage"):
        
        mock_p2p = AsyncMock()
        mock_p2p.public_endpoint = ("1.2.3.4", 9999)
        mock_p2p.connect_to_peer = AsyncMock()
        
        MockP2PNode.return_value = mock_p2p
        
        server = AgentMeshServer(registry=mock_registry, production=False, storage="memory")
        
        # Ensure p2p_node is set on state (it is done in __init__ but we mocked it)
        server.app.state.p2p_node = mock_p2p
        
        return TestClient(server.app), mock_p2p

def test_p2p_handshake_forwarding(client, mock_registry):
    test_client, mock_p2p = client
    
    payload = {
        "skill": "sys.p2p.handshake",
        "payload": {
            "public_endpoint": "5.6.7.8:1234"
        }
    }
    
    # Mock invoke_agent to return success
    mock_registry.invoke_agent.return_value = {"status": "forwarded"}
    
    response = test_client.post("/api/v1/agents/test-agent/invoke", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # Verify registry.invoke_agent was called (forwarding)
    mock_registry.invoke_agent.assert_called_once()
    call_args = mock_registry.invoke_agent.call_args
    assert call_args[0][0] == "test-agent"
    assert call_args[1]["skill"] == "sys.p2p.handshake"
    assert call_args[1]["payload"]["public_endpoint"] == "5.6.7.8:1234"

def test_p2p_handshake_missing_endpoint_forwarding(client, mock_registry):
    test_client, mock_p2p = client
    
    payload = {
        "skill": "sys.p2p.handshake",
        "payload": {} # Missing endpoint
    }
    
    # Mock invoke_agent to return success (it will be validated by the target agent, not the router)
    mock_registry.invoke_agent.return_value = {"status": "forwarded_bad_payload"}
    
    response = test_client.post("/api/v1/agents/test-agent/invoke", json=payload)
    
    assert response.status_code == 200
    
    # Verify registry.invoke_agent was called (router doesn't validate payload deep content)
    mock_registry.invoke_agent.assert_called_once()
