
import asyncio
import sys
import os
from datetime import datetime, timedelta, timezone

# Add src to path so we can import agentmesh
sys.path.append(os.path.join(os.getcwd(), "src"))

from agentmesh.core.registry import AgentRegistry
from agentmesh.core.agent_card import AgentCard, Skill, ProtocolType

async def main():
    print("Initializing Registry...")
    registry = AgentRegistry()
    # We don't start the registry fully to avoid side effects like storage sync or health check loops
    # unless necessary. But start() initializes trust manager.
    await registry.start()

    # Mock trust scores logic
    # We will patch calculate_trust_score on the instance
    trust_scores = {
        "agent-1": 0.9,
        "agent-2": 0.5,
        "agent-3": 0.1
    }

    async def mock_calculate_trust_score(agent_id):
        return trust_scores.get(agent_id, 0.0)
    
    registry.calculate_trust_score = mock_calculate_trust_score

    print("Registering 3 agents...")
    
    # Create agents with staggered updated_at times
    now = datetime.now(timezone.utc)
    
    agents_data = [
        ("agent-1", now),
        ("agent-2", now - timedelta(hours=1)),
        ("agent-3", now - timedelta(hours=2))
    ]

    for agent_id, updated_time in agents_data:
        card = AgentCard(
            id=agent_id,
            name=f"Agent {agent_id}",
            version="1.0.0",
            description=f"Test Agent {agent_id}",
            skills=[Skill(name="test", description="test skill")],
            endpoint=f"http://localhost:8000/{agent_id}",
            protocol=ProtocolType.HTTP,
            trust_score=trust_scores[agent_id]
        )
        await registry.register_agent(card)
        
        # Manually set updated_at since register sets it to now()
        # Access internal storage directly for test setup
        registry.agents[agent_id].updated_at = updated_time

    print("\n--- Verifying Sort by Trust Score (DESC) ---")
    sorted_agents = await registry.list_agents(sort_by="trust_score", order="desc")
    ids = [a.id for a in sorted_agents]
    scores = [a.trust_score for a in sorted_agents]
    print(f"IDs: {ids}")
    print(f"Scores: {scores}")
    
    assert ids == ["agent-1", "agent-2", "agent-3"], f"Expected order [agent-1, agent-2, agent-3], got {ids}"
    assert scores == [0.9, 0.5, 0.1], f"Expected scores [0.9, 0.5, 0.1], got {scores}"
    print("✅ Sort by Trust Score verified.")

    print("\n--- Verifying Sort by Updated At (DESC) ---")
    sorted_agents = await registry.list_agents(sort_by="updated_at", order="desc")
    ids = [a.id for a in sorted_agents]
    print(f"IDs: {ids}")
    
    assert ids == ["agent-1", "agent-2", "agent-3"], f"Expected order [agent-1, agent-2, agent-3], got {ids}"
    print("✅ Sort by Updated At verified.")

    print("\n--- Verifying Leaderboard Fields ---")
    # Simulate some metrics to populate leaderboard
    # Agent 1: High activity
    registry._agent_metrics["agent-1"]["heartbeats"] = 100
    registry._agent_metrics["agent-1"]["invocations"] = 50
    registry._agent_metrics["agent-1"]["latency_sum"] = 5.0
    registry._agent_metrics["agent-1"]["latency_count"] = 50
    registry._agent_metrics["agent-1"]["uptime_streak"] = 99

    leaderboard = await registry.get_leaderboard()
    print(f"Leaderboard entries: {len(leaderboard)}")
    
    found_agent_1 = False
    for entry in leaderboard:
        print(f"Entry: {entry['agent_id']} - Metrics: {entry.get('metrics')}")
        metrics = entry.get("metrics", {})
        
        if "latency_avg" not in metrics:
            print(f"❌ latency_avg missing in metrics for {entry['agent_id']}")
            sys.exit(1)
        
        if "uptime_percentage" not in metrics:
            print(f"❌ uptime_percentage missing in metrics for {entry['agent_id']}")
            sys.exit(1)
            
        if entry["agent_id"] == "agent-1":
            found_agent_1 = True
            # Verify calculation correctness if possible
            # latency_avg = 5.0 / 50 = 0.1
            if metrics["latency_avg"] != 0.1:
                 print(f"⚠️ Warning: Expected latency_avg 0.1, got {metrics['latency_avg']}")

    if not found_agent_1:
        print("❌ Agent 1 not found in leaderboard")
        sys.exit(1)

    print("✅ Leaderboard fields verified.")
    
    await registry.stop()

if __name__ == "__main__":
    asyncio.run(main())
