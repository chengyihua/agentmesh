import argparse
import pytest
from unittest.mock import MagicMock, patch
from agentmesh.cli import _cmd_agents, build_parser

@pytest.fixture
def mock_client():
    client = MagicMock()
    client.register_agent.return_value = {"status": "success"}
    client.update_agent.return_value = {"status": "success"}
    client.private_key = None  # Ensure private_key is None by default
    return client

@patch("agentmesh.cli._build_client")
@patch("agentmesh.cli._load_config")
def test_cli_register_with_rate_limits(mock_load_config, mock_build_client, mock_client):
    mock_load_config.return_value = {}
    mock_build_client.return_value = mock_client
    
    mock_client.discover_agents.return_value = {"agents": [], "total": 0}
    
    parser = build_parser()
    args = parser.parse_args([
        "agents", "register",
        "--id", "cli-test",
        "--qps-budget", "10.5",
        "--concurrency-limit", "5",
        "--vector-desc", "custom vector desc"
    ])
    
    _cmd_agents(args)
    
    # Verify client was called with correct payload
    call_args = mock_client.register_agent.call_args[0][0]
    assert call_args["id"] == "cli-test"
    assert call_args["qps_budget"] == 10.5
    assert call_args["concurrency_limit"] == 5
    assert call_args["vector_desc"] == "custom vector desc"

@patch("agentmesh.cli._build_client")
@patch("agentmesh.cli._load_config")
def test_cli_update_with_rate_limits(mock_load_config, mock_build_client, mock_client):
    mock_load_config.return_value = {}
    mock_build_client.return_value = mock_client
    
    parser = build_parser()
    args = parser.parse_args([
        "agents", "update",
        "cli-test",
        "--qps-budget", "20.0",
        "--concurrency-limit", "10",
        "--vector-desc", "new vector desc",
        "--protocol", "grpc"
    ])
    
    _cmd_agents(args)
    
    # Verify client was called with correct payload
    call_args = mock_client.update_agent.call_args
    agent_id = call_args[0][0]
    payload = call_args[0][1]
    
    assert agent_id == "cli-test"
    assert payload["qps_budget"] == 20.0
    assert payload["concurrency_limit"] == 10
    assert payload["vector_desc"] == "new vector desc"
    assert payload["protocol"] == "grpc"

@patch("agentmesh.cli._build_client")
@patch("agentmesh.cli._load_config")
def test_cli_discover_calls_correct_method(mock_load_config, mock_build_client, mock_client):
    mock_load_config.return_value = {}
    mock_build_client.return_value = mock_client
    
    mock_client.discover_agents.return_value = {"agents": [], "total": 0}
    
    parser = build_parser()
    args = parser.parse_args([
        "agents", "discover",
        "some query",
        "--skill", "python",
        "--limit", "5"
    ])
    
    _cmd_agents(args)
    
    # Verify client.discover_agents was called, not search_agents
    mock_client.discover_agents.assert_called_once()
    mock_client.search_agents.assert_not_called()
    
    call_args = mock_client.discover_agents.call_args[1]
    assert call_args["q"] == "some query"
    assert call_args["skill"] == "python"
    assert call_args["limit"] == 5

@patch("agentmesh.cli._build_client")
@patch("agentmesh.cli._load_config")
@patch("agentmesh.cli.SecurityManager")
def test_cli_register_with_config_key(mock_sm_cls, mock_load_config, mock_build_client, mock_client):
    # Setup mocks
    mock_sm = MagicMock()
    mock_sm_cls.return_value = mock_sm
    mock_sm.get_public_key_from_private.return_value = "mock_public_key"
    mock_sm.derive_agent_id.return_value = "derived-id-123"
    mock_sm._prepare_signature_data.return_value = b"data_to_sign"
    mock_sm.sign_data.return_value = "mock_signature"
    
    # Config has private key
    mock_load_config.return_value = {"private_key": "config_private_key"}
    
    # Client has private key from config
    mock_client.private_key = "config_private_key"
    mock_build_client.return_value = mock_client
    
    parser = build_parser()
    args = parser.parse_args([
        "agents", "register",
        "--name", "SignedAgent"
    ])
    
    _cmd_agents(args)
    
    # Verify SecurityManager was used
    mock_sm.get_public_key_from_private.assert_called_with("config_private_key")
    mock_sm.derive_agent_id.assert_called_with("mock_public_key")
    mock_sm.sign_data.assert_called()
    
    # Verify client register called with signed payload
    call_args = mock_client.register_agent.call_args[0][0]
    assert call_args["id"] == "derived-id-123"
    assert call_args["public_key"] == "mock_public_key"
    assert call_args["manifest_signature"] == "mock_signature"
