
import pytest
from unittest.mock import AsyncMock, MagicMock
from agentmesh.core.agent_card import AgentCard, NATType, NetworkProfile, ProtocolType
from agentmesh.protocols.gateway import ProtocolGateway
from agentmesh.protocols.base import InvocationRequest, InvocationResult

@pytest.fixture
def mock_relay_handler():
    handler = AsyncMock()
    handler.invoke.return_value = InvocationResult(
        protocol="relay",
        target_url="relay://test",
        status_code=200,
        ok=True,
        latency_ms=10,
        response={"source": "relay"}
    )
    return handler

@pytest.fixture
def mock_http_handler():
    handler = AsyncMock()
    handler.invoke.return_value = InvocationResult(
        protocol="http",
        target_url="http://test",
        status_code=200,
        ok=True,
        latency_ms=10,
        response={"source": "http"}
    )
    return handler

@pytest.fixture
def gateway(mock_http_handler, mock_relay_handler):
    # Initialize gateway with mocked handlers
    gw = ProtocolGateway()
    # Manually inject mocks into _handlers dictionary
    gw._handlers["http"] = mock_http_handler
    gw._handlers["relay"] = mock_relay_handler
    return gw

@pytest.mark.asyncio
async def test_smart_routing_priority_symmetric_nat(gateway, mock_http_handler, mock_relay_handler):
    """Test that Relay is prioritized for SYMMETRIC NAT."""
    agent = AgentCard(
        id="agent-symmetric",
        name="Symmetric Agent",
        version="1.0.0",
        description="Test Agent",
        skills=[{"name": "test", "description": "test"}],
        endpoint="http://1.2.3.4:8080",
        protocol="http",
        network_profile=NetworkProfile(
            nat_type=NATType.SYMMETRIC,
            relay_endpoint="ws://relay.example.com",
            public_endpoints=["1.2.3.4:8080"]
        )
    )
    
    request = InvocationRequest(
        agent_id="agent-symmetric",
        endpoint="http://1.2.3.4:8080",
        protocol="http",
        skill="test", 
        payload={}
    )
    
    result = await gateway.invoke(agent, request)
    
    # Should use Relay
    assert result.protocol == "relay"
    assert result.response["source"] == "relay"
    
    # Relay handler should be called
    mock_relay_handler.invoke.assert_awaited_once()
    # HTTP handler should NOT be called
    mock_http_handler.invoke.assert_not_awaited()

@pytest.mark.asyncio
async def test_smart_routing_priority_unknown_nat(gateway, mock_http_handler, mock_relay_handler):
    """Test that Relay is prioritized for UNKNOWN NAT."""
    agent = AgentCard(
        id="agent-unknown",
        name="Unknown Agent",
        version="1.0.0",
        description="Test Agent",
        skills=[{"name": "test", "description": "test"}],
        endpoint="http://1.2.3.4:8080",
        protocol="http",
        network_profile=NetworkProfile(
            nat_type=NATType.UNKNOWN,
            relay_endpoint="ws://relay.example.com",
            public_endpoints=[]
        )
    )
    
    request = InvocationRequest(
        agent_id="agent-unknown",
        endpoint="http://1.2.3.4:8080",
        protocol="http",
        skill="test", 
        payload={}
    )
    
    result = await gateway.invoke(agent, request)
    
    # Should use Relay
    assert result.protocol == "relay"
    
    # Relay handler should be called
    mock_relay_handler.invoke.assert_awaited_once()
    # HTTP handler should NOT be called
    mock_http_handler.invoke.assert_not_awaited()

@pytest.mark.asyncio
async def test_smart_routing_fallback_on_failure(gateway, mock_http_handler, mock_relay_handler):
    """Test fallback to Relay when primary protocol fails."""
    agent = AgentCard(
        id="agent-fallback",
        name="Fallback Agent",
        version="1.0.0",
        description="Test Agent",
        skills=[{"name": "test", "description": "test"}],
        endpoint="http://1.2.3.4:8080",
        protocol="http",
        network_profile=NetworkProfile(
            nat_type=NATType.FULL_CONE, # Good NAT, should try direct first
            relay_endpoint="ws://relay.example.com",
            public_endpoints=["1.2.3.4:8080"]
        )
    )
    
    # Make HTTP handler fail
    mock_http_handler.invoke.side_effect = Exception("Connection Refused")
    
    request = InvocationRequest(
        agent_id="agent-failover",
        endpoint="http://1.2.3.4:8080",
        protocol="http",
        skill="test", 
        payload={}
    )
    
    result = await gateway.invoke(agent, request)
    
    # Should fall back to Relay
    assert result.protocol == "relay"
    
    # Both handlers should be called
    mock_http_handler.invoke.assert_awaited_once()
    mock_relay_handler.invoke.assert_awaited_once()

@pytest.mark.asyncio
async def test_smart_routing_no_relay_fallback(gateway, mock_http_handler, mock_relay_handler):
    """Test failure when no relay is available for fallback."""
    agent = AgentCard(
        id="agent-no-relay",
        name="No Relay Agent",
        version="1.0.0",
        description="Test Agent",
        skills=[{"name": "test", "description": "test"}],
        endpoint="http://1.2.3.4:8080",
        protocol="http",
        network_profile=NetworkProfile(
            nat_type=NATType.FULL_CONE,
            relay_endpoint=None, # No relay
            public_endpoints=["1.2.3.4:8080"]
        )
    )
    
    # Make HTTP handler fail
    mock_http_handler.invoke.side_effect = Exception("Connection Refused")
    
    request = InvocationRequest(
        agent_id="agent-no-relay",
        endpoint="http://1.2.3.4:8080",
        protocol="http",
        skill="test", 
        payload={}
    )
    
    with pytest.raises(Exception, match="Connection Refused"):
        await gateway.invoke(agent, request)
    
    # HTTP called, Relay NOT called
    mock_http_handler.invoke.assert_awaited_once()
    mock_relay_handler.invoke.assert_not_awaited()
