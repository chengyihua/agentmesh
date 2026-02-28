import pytest
import asyncio
from unittest.mock import AsyncMock
from agentmesh.core.federation import FederationManager
from agentmesh.core.registry import AgentRegistry

@pytest.mark.asyncio
async def test_background_loop():
    registry = AgentRegistry()
    federation = FederationManager(registry)
    
    # Mock sync_from_seeds to track calls
    federation.sync_from_seeds = AsyncMock()
    
    # Start loop task
    # We expect start_background_sync to exist and run
    task = asyncio.create_task(federation.start_background_sync(interval=0.1))
    
    await asyncio.sleep(0.25)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
        
    # Should have run at least twice (0s, 0.1s, 0.2s...)
    assert federation.sync_from_seeds.call_count >= 2
