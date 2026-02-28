import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from agentmesh.p2p.utils import get_network_profile
from agentmesh.core.agent_card import NATType

@pytest.mark.asyncio
async def test_get_network_profile_success():
    """Test successful network profile retrieval."""
    with patch("agentmesh.p2p.utils.P2PNode") as MockP2PNode:
        mock_node = MockP2PNode.return_value
        mock_node.start = AsyncMock()
        mock_node.nat_type = "full_cone"
        mock_node.public_endpoint = ("1.2.3.4", 8000)
        mock_node.local_endpoints = ["192.168.1.5:8000"]
        mock_node.transport = MagicMock()
        
        profile = await get_network_profile()
        
        assert profile.nat_type == NATType.FULL_CONE
        assert profile.public_endpoints == ["1.2.3.4:8000"]
        assert profile.local_endpoints == ["192.168.1.5:8000"]
        
        mock_node.start.assert_awaited_once()
        mock_node.transport.close.assert_called_once()

@pytest.mark.asyncio
async def test_get_network_profile_timeout():
    """Test timeout handling."""
    with patch("agentmesh.p2p.utils.P2PNode") as MockP2PNode:
        mock_node = MockP2PNode.return_value
        # Simulate timeout by waiting longer than timeout
        async def slow_start():
            await asyncio.sleep(0.2)
            
        mock_node.start = AsyncMock(side_effect=asyncio.TimeoutError)
        mock_node.nat_type = "unknown"
        mock_node.local_endpoints = []
        mock_node.transport = MagicMock()
        
        profile = await get_network_profile(stun_timeout=0.1)
        
        assert profile.nat_type == NATType.UNKNOWN
        mock_node.transport.close.assert_called_once()
