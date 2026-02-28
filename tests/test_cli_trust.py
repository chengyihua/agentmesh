import argparse
from unittest.mock import MagicMock, patch
from agentmesh.cli import _cmd_agents, build_parser

def test_cli_trust_command():
    mock_client = MagicMock()
    mock_client.get_trust_score.return_value = {"trust_score": 0.95}

    with patch("agentmesh.cli._build_client", return_value=mock_client), \
         patch("agentmesh.cli._load_config", return_value={}):
        
        parser = build_parser()
        args = parser.parse_args([
            "agents", "trust",
            "agent-123"
        ])
        
        _cmd_agents(args)
        
        mock_client.get_trust_score.assert_called_once_with("agent-123")

def test_cli_discover_with_min_trust():
    mock_client = MagicMock()
    mock_client.discover_agents.return_value = {"agents": [], "total": 0}

    with patch("agentmesh.cli._build_client", return_value=mock_client), \
         patch("agentmesh.cli._load_config", return_value={}):
        
        parser = build_parser()
        args = parser.parse_args([
            "agents", "discover",
            "query",
            "--min-trust", "0.8"
        ])
        
        _cmd_agents(args)
        
        mock_client.discover_agents.assert_called_once()
        call_kwargs = mock_client.discover_agents.call_args[1]
        assert call_kwargs["min_trust"] == 0.8
        assert call_kwargs["q"] == "query"

def test_cli_discover_without_min_trust():
    mock_client = MagicMock()
    mock_client.discover_agents.return_value = {"agents": [], "total": 0}

    with patch("agentmesh.cli._build_client", return_value=mock_client), \
         patch("agentmesh.cli._load_config", return_value={}):
        
        parser = build_parser()
        args = parser.parse_args([
            "agents", "discover",
            "query"
        ])
        
        _cmd_agents(args)
        
        mock_client.discover_agents.assert_called_once()
        call_kwargs = mock_client.discover_agents.call_args[1]
        assert call_kwargs["min_trust"] is None
