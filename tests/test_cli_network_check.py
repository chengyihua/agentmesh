import pytest
import argparse
from unittest.mock import patch, MagicMock, AsyncMock
from agentmesh.cli import _run_network_check, _cmd_network_check

@pytest.mark.asyncio
async def test_run_network_check_success(capsys):
    """Test successful network check execution."""
    # Mock P2PNode
    with patch("agentmesh.p2p.node.P2PNode") as MockP2PNode:
        mock_node = MockP2PNode.return_value
        mock_node.start = AsyncMock()
        mock_node.nat_type = "full_cone"
        mock_node.public_endpoint = ("1.2.3.4", 8000)
        mock_node.local_endpoints = ["192.168.1.5:8000"]
        mock_node.transport = MagicMock()
        
        args = argparse.Namespace()
        await _run_network_check(args)
        
        # Verify node was started with port 0 (ephemeral)
        MockP2PNode.assert_called_with(port=0)
        mock_node.start.assert_awaited_once()
        
        # Check output
        captured = capsys.readouterr()
        assert "Analyzing Network Configuration" in captured.out
        assert "NAT Type:        FULL_CONE" in captured.out
        assert "Public Endpoint: 1.2.3.4:8000" in captured.out
        assert "P2P Friendly" in captured.out
        
        # Verify cleanup
        mock_node.transport.close.assert_called_once()

@pytest.mark.asyncio
async def test_run_network_check_symmetric(capsys):
    """Test network check with symmetric NAT."""
    with patch("agentmesh.p2p.node.P2PNode") as MockP2PNode:
        mock_node = MockP2PNode.return_value
        mock_node.start = AsyncMock()
        mock_node.nat_type = "symmetric"
        mock_node.public_endpoint = ("1.2.3.4", 8000)
        mock_node.local_endpoints = []
        mock_node.transport = MagicMock()
        
        args = argparse.Namespace()
        await _run_network_check(args)
        
        captured = capsys.readouterr()
        assert "Symmetric NAT" in captured.out
        assert "rely on the Relay server" in captured.out

@pytest.mark.asyncio
async def test_run_network_check_failure(capsys):
    """Test network check failure handling."""
    with patch("agentmesh.p2p.node.P2PNode") as MockP2PNode:
        mock_node = MockP2PNode.return_value
        mock_node.start = AsyncMock(side_effect=Exception("STUN error"))
        mock_node.transport = None  # No transport to close
        
        args = argparse.Namespace()
        await _run_network_check(args)
        
        captured = capsys.readouterr()
        assert "Analysis Failed: STUN error" in captured.err

def test_cmd_network_check_wrapper():
    """Test the synchronous wrapper command."""
    with patch("agentmesh.cli._run_network_check", new_callable=AsyncMock) as mock_run:
        args = argparse.Namespace()
        ret = _cmd_network_check(args)
        
        assert ret == 0
        mock_run.assert_awaited_once_with(args)
