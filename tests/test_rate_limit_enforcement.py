import pytest
import asyncio
import time
from unittest.mock import MagicMock
from fastapi import HTTPException

from agentmesh.core.agent_card import AgentCard
from agentmesh.core.rate_limit import AgentRateLimiter
from agentmesh.core.telemetry import TelemetryManager

@pytest.fixture
def mock_telemetry():
    telemetry = MagicMock(spec=TelemetryManager)
    telemetry.rate_limit_rejections = MagicMock()
    telemetry.rate_limit_rejections.labels.return_value = MagicMock()
    return telemetry

@pytest.fixture
def rate_limiter(mock_telemetry):
    return AgentRateLimiter(telemetry=mock_telemetry)

@pytest.fixture
def agent():
    return AgentCard(
        id="test-agent",
        name="Test Agent",
        version="1.0.0",
        endpoint="http://localhost",
        skills=[{"name": "test", "description": "test"}]
    )

@pytest.mark.asyncio
async def test_concurrency_limit(rate_limiter, agent):
    agent.concurrency_limit = 2
    
    # Acquire 2 slots
    assert await rate_limiter._acquire(agent) is True
    assert await rate_limiter._acquire(agent) is True
    
    # 3rd should fail
    assert await rate_limiter._acquire(agent) is False
    
    # Verify telemetry
    rate_limiter.telemetry.rate_limit_rejections.labels.assert_called_with(
        agent_id="test-agent", limit_type="concurrency"
    )
    
    # Release one
    await rate_limiter._release(agent)
    
    # Acquire again should succeed
    assert await rate_limiter._acquire(agent) is True

@pytest.mark.asyncio
async def test_qps_limit(rate_limiter, agent):
    # 10 QPS
    agent.qps_budget = 10.0
    
    # Should be able to acquire initial burst (capacity = 10)
    for _ in range(10):
        assert await rate_limiter._acquire(agent) is True
        
    # Next one might fail if done instantly (bucket empty)
    # But refill is time based. If time doesn't move, it fails.
    assert await rate_limiter._acquire(agent) is False
    
    # Verify telemetry
    rate_limiter.telemetry.rate_limit_rejections.labels.assert_called_with(
        agent_id="test-agent", limit_type="qps"
    )

@pytest.mark.asyncio
async def test_low_qps_limit(rate_limiter, agent):
    # 0.5 QPS (1 request per 2 seconds)
    agent.qps_budget = 0.5
    
    # First request should succeed (capacity min 1.0)
    assert await rate_limiter._acquire(agent) is True
    
    # Immediate second request should fail
    assert await rate_limiter._acquire(agent) is False
    
    # Wait 2.1 seconds
    # We can mock time.time or just sleep if it's short. 
    # Mocking time.time is better but requires patching.
    # For now, let's manually manipulate _qps_state for testing refill logic
    
    # Reset state to simulate time passing
    # Current state: (now, tokens=0.5 - 1.0 = -0.5?? No wait)
    # Logic:
    # capacity = 1.0
    # initial tokens = 1.0
    # acquire -> tokens = 0.0
    # next acquire -> tokens=0.0, refill=0 -> fail.
    
    # Simulate 2.1 seconds passed
    last_refill, tokens = rate_limiter._qps_state[agent.id]
    rate_limiter._qps_state[agent.id] = (last_refill - 2.1, tokens)
    
    # Now it should succeed
    assert await rate_limiter._acquire(agent) is True

@pytest.mark.asyncio
async def test_limit_context_manager(rate_limiter, agent):
    agent.concurrency_limit = 1
    
    async with rate_limiter.limit(agent):
        # Inside lock
        # Try to acquire another -> should raise 429
        with pytest.raises(HTTPException) as exc:
            async with rate_limiter.limit(agent):
                pass
        assert exc.value.status_code == 429
    
    # After exit, should succeed
    async with rate_limiter.limit(agent):
        pass
