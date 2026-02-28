from agentmesh.core.agent_card import AgentCard, ProtocolType

def test_agent_card_extended_fields():
    card = AgentCard(
        id="test-agent-1",
        name="Test Agent",
        version="1.0.0",
        skills=[{"name": "test_skill", "description": "test description"}],
        endpoint="http://localhost:8000",
        protocol=ProtocolType.HTTP,
        public_key="some_public_key",
        manifest_signature="some_signature",
        pricing={"model": "token", "rate": 0.001},
        qps_budget=100,
        concurrency_limit=10,
        vector_desc="This is a test agent for vector search",
        models=["gpt-4", "claude-3"]
    )
    assert card.public_key == "some_public_key"
    assert card.manifest_signature == "some_signature"
    assert card.pricing["model"] == "token"
    assert card.qps_budget == 100
    assert card.concurrency_limit == 10
    assert card.vector_desc == "This is a test agent for vector search"
    assert "gpt-4" in card.models


def test_agent_card_network_profile():
    from agentmesh.core.agent_card import NetworkProfile, NATType
    
    card = AgentCard(
        id="p2p-agent",
        name="P2P Agent",
        version="1.0.0",
        skills=[{"name": "test", "description": "test"}],
        endpoint="http://localhost:8000",
        network_profile=NetworkProfile(
            nat_type=NATType.FULL_CONE,
            public_endpoints=["1.2.3.4:9000"],
            p2p_protocols=["libp2p"],
            relay_endpoint="wss://relay.net/agent"
        )
    )
    
    assert card.network_profile.nat_type == NATType.FULL_CONE
    assert "1.2.3.4:9000" in card.network_profile.public_endpoints
    assert card.network_profile.relay_endpoint == "wss://relay.net/agent"

def test_agent_card_update_network_profile():
    from agentmesh.core.agent_card import AgentCardUpdate, NetworkProfile, NATType
    
    update = AgentCardUpdate(
        network_profile=NetworkProfile(
            nat_type=NATType.SYMMETRIC,
            public_endpoints=["5.6.7.8:1234"]
        )
    )
    
    assert update.network_profile.nat_type == NATType.SYMMETRIC
    assert "5.6.7.8:1234" in update.network_profile.public_endpoints
