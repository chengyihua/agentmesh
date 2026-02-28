
import pytest
from unittest.mock import AsyncMock, MagicMock
from agentmesh.protocols.gateway import ProtocolGateway
from agentmesh.protocols.base import InvocationRequest
from agentmesh.core.agent_card import AgentCard, NetworkProfile, NATType, ProtocolType

@pytest.mark.asyncio
async def test_smart_routing_nat_unknown_prefers_relay():
    gateway = ProtocolGateway()
    
    # Mock handlers
    relay_handler = MagicMock()
    relay_handler.invoke = AsyncMock(return_value={"status": "relay_success"})
    
    direct_handler = MagicMock()
    direct_handler.invoke = AsyncMock(return_value={"status": "direct_success"})
    
    # Directly set handlers since there is no register_handler method
    gateway._handlers["relay"] = relay_handler
    gateway._handlers["http"] = direct_handler
    
    # Agent with UNKNOWN NAT
    agent = AgentCard(
        id="agent-unknown-nat",
        name="Unknown NAT Agent",
        version="1.0",
        skills=[{"name": "test-skill", "description": "test"}],
        endpoint="http://direct.example.com",
        protocol=ProtocolType.HTTP,
        network_profile=NetworkProfile(
            nat_type=NATType.UNKNOWN,
            relay_endpoint="relay://relay.example.com",
            public_endpoints=[],
            local_endpoints=[]
        )
    )
    
    request = InvocationRequest(
        agent_id=agent.id,
        protocol="http",
        endpoint=str(agent.endpoint),
        method="GET",
        path="/test",
    )
    
    # Invoke
    result = await gateway.invoke(agent, request)
    
    # Verify Relay was called
    assert result["status"] == "relay_success"
    relay_handler.invoke.assert_called_once()
    
    # Verify request passed to relay handler had relay protocol
    call_args = relay_handler.invoke.call_args[0][0]
    assert call_args.protocol == "relay"
    assert call_args.endpoint == "relay://relay.example.com"
    
    # Verify Direct was NOT called (since relay succeeded)
    direct_handler.invoke.assert_not_called()

@pytest.mark.asyncio
async def test_smart_routing_fallback_to_direct_if_relay_fails():
    gateway = ProtocolGateway()
    
    # Mock handlers
    relay_handler = MagicMock()
    relay_handler.invoke = AsyncMock(side_effect=Exception("Relay failed"))
    
    direct_handler = MagicMock()
    direct_handler.invoke = AsyncMock(return_value={"status": "direct_success"})
    
    gateway._handlers["relay"] = relay_handler
    gateway._handlers["http"] = direct_handler
    
    # Agent with UNKNOWN NAT
    agent = AgentCard(
        id="agent-unknown-nat",
        name="Unknown NAT Agent",
        version="1.0",
        skills=[{"name": "test-skill", "description": "test"}],
        endpoint="http://direct.example.com",
        protocol=ProtocolType.HTTP,
        network_profile=NetworkProfile(
            nat_type=NATType.UNKNOWN,
            relay_endpoint="relay://relay.example.com",
            public_endpoints=[],
            local_endpoints=[]
        )
    )
    
    request = InvocationRequest(
        agent_id=agent.id,
        protocol="http",
        endpoint=str(agent.endpoint),
        method="GET",
        path="/test",
    )
    
    # Invoke
    result = await gateway.invoke(agent, request)
    
    # Verify Relay was called first
    relay_handler.invoke.assert_called_once()
    
    # Verify Direct was called after relay failure
    direct_handler.invoke.assert_called_once()
    assert result["status"] == "direct_success"
