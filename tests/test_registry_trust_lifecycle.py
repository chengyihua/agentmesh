import pytest
import asyncio
from agentmesh.core.registry import AgentRegistry
from agentmesh.core.agent_card import AgentCard
from datetime import datetime, timezone

@pytest.mark.asyncio
async def test_registry_trust_lifecycle():
    # 1. Initialize Registry
    registry = AgentRegistry()
    
    # 2. Register an agent
    agent = AgentCard(
        id="lifecycle-agent",
        name="Lifecycle Agent",
        version="1.0.0",
        endpoint="http://localhost:8000",
        skills=[{"name": "test", "description": "test"}]
    )
    await registry.register_agent(agent)
    
    # 3. Set high trust score manually
    # We need to access the trust manager directly to seed the score
    # because register_agent sets it to 0.5 (initial)
    registry.trust_manager.scores[agent.id] = 0.9
    
    # 4. Configure aggressive decay for testing
    registry.trust_manager.decay_interval = 0.1  # 100ms
    registry.trust_manager.decay_factor = 0.1    # 10% decay per interval
    
    # 5. Start the registry (which starts trust manager loop)
    await registry.start()
    
    try:
        # 6. Wait for a few cycles (300ms = 3 cycles)
        await asyncio.sleep(0.35)
        
        # 7. Verify score decayed
        current_score = await registry.calculate_trust_score(agent.id)
        
        # Expected calculation:
        # Initial: 0.9
        # Target: 0.5
        # Cycle 1: 0.9 - (0.4 * 0.1) = 0.86
        # Cycle 2: 0.86 - (0.36 * 0.1) = 0.824
        # Cycle 3: 0.824 - (0.324 * 0.1) = 0.7916
        
        assert current_score < 0.9, f"Score {current_score} should be less than initial 0.9"
        assert current_score > 0.5, f"Score {current_score} should be greater than target 0.5"
        # It should be roughly around 0.79-0.85 depending on exact timing
        
    finally:
        # 8. Stop registry
        await registry.stop()
