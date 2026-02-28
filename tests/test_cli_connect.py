
import argparse
import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agentmesh.cli import _cmd_connect

# Mock Config
MOCK_CONFIG = {
    "agent_id": "cli-agent-test",
    "private_key": "MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIzNDU2Nzg5MDE=",  # Valid base64 32-byte key
    "endpoint": "http://localhost:8000"
}

@pytest.fixture
def mock_load_config():
    with patch("agentmesh.cli._load_config", return_value=MOCK_CONFIG) as m:
        yield m

@pytest.fixture
def mock_client():
    with patch("agentmesh.client.AgentMeshClient") as MockClient:
        client_instance = AsyncMock()
        MockClient.return_value.__aenter__.return_value = client_instance
        
        # Mock methods
        client_instance.start_p2p.return_value = {
            "nat_type": "full_cone",
            "public_endpoints": ["1.2.3.4:5678"],
            "local_endpoints": ["192.168.1.10:5678"]
        }
        client_instance.connect_relay.return_value = True
        client_instance.update_agent.return_value = {"id": "cli-agent-test"}
        client_instance.health_check_interval = 0.1
        
        yield client_instance

def test_connect_full_flow(mock_load_config, mock_client):
    """Test full connect flow: P2P -> Relay -> Registry -> Heartbeat"""
    
    # Mock args
    args = argparse.Namespace(
        relay_url="ws://relay.example.com",
        target_url=None,
        agent_id=None,
        private_key=None,
        port=0,
        webhook_url="https://example.com/webhook",
        no_register=False,
        endpoint=None,
        api_key=None
    )
    
    # We need to interrupt the infinite loop
    # Mock asyncio.sleep to raise CancelledError after a few calls
    # The _run_connect_agent has two infinite loops: heartbeat and main wait
    # We'll patch sleep to raise CancelledError on the second call (main loop wait)
    
    # However, mocking sleep inside the function is tricky because it's used in heartbeat too.
    # Let's mock _run_connect_agent execution by mocking asyncio.run
    
    with patch("asyncio.run") as mock_run:
        # We can't easily test the internal logic of _run_connect_agent via _cmd_connect 
        # because asyncio.run takes a coroutine.
        # So we should test _run_connect_agent directly if we want to verify the steps.
        # Or we can just trust that _cmd_connect calls asyncio.run with the coroutine.
        
        ret = _cmd_connect(args)
        assert ret == 0
        mock_run.assert_called_once()
        
        # To test the logic inside _run_connect_agent, we need to invoke it directly
        # or use a real asyncio loop in test.
        pass

@pytest.mark.asyncio
async def test_run_connect_agent_logic(mock_load_config):
    """Test the async logic of _run_connect_agent directly"""
    from agentmesh.cli import _run_connect_agent
    
    # Mock Client context manager
    mock_client_instance = AsyncMock()
    # Setup mock return values
    mock_client_instance.start_p2p.return_value = {
        "nat_type": "full_cone",
        "public_endpoints": ["1.2.3.4:5678"],
        "local_endpoints": ["192.168.1.10:5678"]
    }
    mock_client_instance.connect_relay.return_value = True
    mock_client_instance.update_agent.return_value = {"id": "cli-agent-test"}
    mock_client_instance.health_check_interval = 0.1
    
    # Mock __aenter__ to return the instance
    mock_client_class = MagicMock()
    mock_client_class.return_value.__aenter__.return_value = mock_client_instance
    
    # Patch agentmesh.client.AgentMeshClient because it is imported inside the function
    with patch("agentmesh.client.AgentMeshClient", new=mock_client_class), \
         patch("agentmesh.cli._forward_request", new_callable=AsyncMock) as mock_fwd:
    
        args = argparse.Namespace(
            relay_url="ws://relay.example.com",
            target_url="http://localhost:8080",
            agent_id="cli-agent-test", # Explicit ID
            private_key="MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIzNDU2Nzg5MDE=", # Explicit Key
            port=1234,
            webhook_url="https://example.com/webhook",
            no_register=False
        )
        
        client_config = MagicMock()
        client_config.base_url = "http://test-api"
        client_config.api_key = None
        
        # Custom sleep mock to control loop exit
        async def mock_sleep_func(seconds):
            if seconds == 1: # Main loop sleep duration
                raise asyncio.CancelledError()
            # Heartbeat sleep (0.1) just returns
            return

        with patch("asyncio.sleep", side_effect=mock_sleep_func):
            try:
                # Need to mock config dictionary too
                config = {"agent_id": "cli-agent-test", "private_key": "..."}
                await _run_connect_agent(args, config, client_config)
            except asyncio.CancelledError:
                pass
        
        # Verification
        
        # 1. Client Init
        mock_client_class.assert_called_once()
        _, kwargs = mock_client_class.call_args
        assert kwargs["agent_id"] == "cli-agent-test"
        
        # 2. P2P Started
        mock_client_instance.start_p2p.assert_awaited_once_with(port=1234, update_registry=False)
        
        # 3. Relay Connected
        mock_client_instance.connect_relay.assert_awaited_once()
        call_args = mock_client_instance.connect_relay.call_args
        assert call_args[0][0] == "ws://relay.example.com"
        assert call_args[1]["update_registry"] is False
        
        # Check callback handler
        handler = call_args[1]["on_request"]
        assert callable(handler)
        
        # Test Handler Logic (Reverse Proxy)
        await handler({"method": "POST", "path": "/foo"})
        mock_fwd.assert_awaited_with("http://localhost:8080", {"method": "POST", "path": "/foo"})
        
        # 4. Registry Updated
        mock_client_instance.update_agent.assert_awaited_once()
        update_arg = mock_client_instance.update_agent.call_args[0][1]
        assert update_arg["webhook_url"] == "https://example.com/webhook"
        assert update_arg["network_profile"]["relay_endpoint"] == "ws://relay.example.com"

@pytest.mark.asyncio
async def test_run_connect_agent_retry_logic(mock_load_config):
    """Test the retry logic of _run_connect_agent for registry updates"""
    from agentmesh.cli import _run_connect_agent
    import httpx
    
    # Mock Client context manager
    mock_client_instance = AsyncMock()
    mock_client_instance.start_p2p.return_value = {}
    mock_client_instance.connect_relay.return_value = True
    mock_client_instance.health_check_interval = 0.1
    
    # Mock update_agent to fail twice then succeed
    mock_client_instance.update_agent.side_effect = [
        httpx.HTTPStatusError("500 Error", request=MagicMock(), response=MagicMock(status_code=500)),
        Exception("Network Error"),
        {"id": "cli-agent-test"} # Success on 3rd attempt
    ]
    
    # Mock __aenter__ to return the instance
    mock_client_class = MagicMock()
    mock_client_class.return_value.__aenter__.return_value = mock_client_instance
    
    with patch("agentmesh.client.AgentMeshClient", new=mock_client_class), \
         patch("agentmesh.cli._forward_request", new_callable=AsyncMock):
    
        args = argparse.Namespace(
            relay_url="ws://relay.example.com",
            target_url=None,
            agent_id="cli-agent-test",
            private_key="MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIzNDU2Nzg5MDE=",
            port=1234,
            webhook_url=None,
            no_register=False
        )
        
        client_config = MagicMock()
        client_config.base_url = "http://test-api"
        client_config.api_key = None
        
        # Custom sleep mock to control loop exit and speed up retry wait
        # We need to distinguish between retry sleep (1.0) and main loop sleep (1.0)
        # We expect:
        # 1. Retry sleep 1.0 (after 1st failure) -> continue
        # 2. Retry sleep 2.0 (after 2nd failure) -> continue
        # 3. Heartbeat sleep 0.1 -> continue
        # 4. Main loop sleep 1 -> raise CancelledError
        
        sleep_call_count = 0
        
        async def mock_sleep_func(seconds):
            nonlocal sleep_call_count
            sleep_call_count += 1
            
            # If we are in the retry phase (first few calls)
            if seconds == 1.0 and sleep_call_count == 1:
                 # First retry delay
                 return
            
            if seconds == 2.0:
                 # Second retry delay
                 return
                 
            if seconds == 0.1:
                # Heartbeat
                return
                
            if seconds == 1.0 and sleep_call_count > 1:
                # Main loop (or subsequent 1s sleeps if any)
                # We assume main loop comes after retries
                raise asyncio.CancelledError()
            
            return

        with patch("asyncio.sleep", side_effect=mock_sleep_func):
            try:
                config = {"agent_id": "cli-agent-test", "private_key": "..."}
                await _run_connect_agent(args, config, client_config)
            except asyncio.CancelledError:
                pass
        
        # Verification
        # Should have called update_agent 3 times
        assert mock_client_instance.update_agent.call_count == 3
