import asyncio
import random
from agentmesh import AgentMeshClient

SAMPLE_AGENTS = [
    {
        "id": "weather-bot-001",
        "name": "Global Weather Sentinel",
        "version": "1.2.0",
        "description": "Real-time weather monitoring and forecasting service using satellite data.",
        "skills": [{"name": "get_forecast", "description": "Get 7-day forecast"}, {"name": "current_weather", "description": "Local conditions"}],
        "endpoint": "http://weather-api.local/v1",
        "protocol": "http",
        "tags": ["weather", "environmental", "satellite"]
    },
    {
        "id": "crypto-analyst-pro",
        "name": "CryptoAnalyst Pro",
        "version": "0.9.5-beta",
        "description": "High-frequency trading signals and sentiment analysis for crypto markets.",
        "skills": [{"name": "get_price", "description": "Live prices"}, {"name": "sentiment_score", "description": "Social media sentiment"}],
        "endpoint": "https://crypto.service.mesh",
        "protocol": "grpc",
        "tags": ["finance", "crypto", "trading"]
    },
    {
        "id": "code-reviewer-ai",
        "name": "GitHub PR Assistant",
        "version": "2.1.0",
        "description": "Automated code review and security vulnerability scanning for Pull Requests.",
        "skills": [{"name": "review_pr", "description": "Scan files for bugs"}, {"name": "fix_lint", "description": "Auto-fix linting errors"}],
        "endpoint": "http://localhost:9000/github",
        "protocol": "http",
        "tags": ["development", "devops", "security"]
    },
    {
        "id": "travel-planner-v2",
        "name": "Nomad Travel Planner",
        "version": "1.0.1",
        "description": "Personalized travel itineraries and flight/hotel bookings.",
        "skills": [{"name": "book_flight", "description": "Search and book tickets"}, {"name": "plan_route", "description": "Generate city guides"}],
        "endpoint": "http://travel.nomad.mesh",
        "protocol": "mcp",
        "tags": ["travel", "concierge", "api"]
    },
    {
        "id": "legal-doc-summarizer",
        "name": "LegalEagle Summarizer",
        "version": "1.4.0",
        "description": "Extracting key clauses and risks from complex legal contracts.",
        "skills": [{"name": "summarize", "description": "TL;DR of doc"}, {"name": "risk_assessment", "description": "Identify bad clauses"}],
        "endpoint": "http://legal.internal/api",
        "protocol": "http",
        "tags": ["legal", "productivity", "nlp"]
    },
    {
        "id": "health-tracker-iot",
        "name": "BioMetrics Pulse",
        "version": "0.5.0",
        "description": "Aggregating data from wearable health devices for medical monitoring.",
        "skills": [{"name": "fetch_heartrate", "description": "Get BPM"}, {"name": "sleep_analysis", "description": "Get sleep stages"}],
        "endpoint": "https://health.iot.mesh",
        "protocol": "http",
        "tags": ["health", "iot", "biotech"]
    }
]

async def seed():
    client = AgentMeshClient(base_url="http://localhost:8000")
    print("🌱 Starting Registry Seeding...")
    
    for agent_data in SAMPLE_AGENTS:
        try:
            # Randomize health for visual variety
            agent_data["health_status"] = random.choice(["healthy", "healthy", "healthy", "healthy", "unhealthy"])
            
            res = await client.register_agent(agent_data)
            agent_id = agent_data["id"]
            print(f"✅ Registered: {agent_data['name']} ({agent_id})")

            # Simulate some activity for trust score calculation visibility
            # Perform heartbeats
            heartbeat_count = random.randint(5, 15)
            for _ in range(heartbeat_count):
                await client.post(f"/api/v1/agents/{agent_id}/heartbeat", json={"status": "healthy"})
            
            # Simulate invocations (some successful, some failed)
            # Since client.invoke_agent might actually try to hit the endpoint, 
            # we manually record metrics via a hidden internal-like simulation or just register high heartbeats.
            # For seeding purposes, we'll just log that we are simulating metrics.
            print(f"   📊 Simulated {heartbeat_count} heartbeats for {agent_id}")

        except Exception as e:
            print(f"❌ Failed to register {agent_id}: {e}")
    
    await client.close()
    print("\n✨ Seeding Complete! Refresh your dashboard to see the magic.")

if __name__ == "__main__":
    asyncio.run(seed())
