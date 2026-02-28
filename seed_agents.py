
import asyncio
import logging
import os
import sys
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from agentmesh.core.registry import AgentRegistry
from agentmesh.storage.postgres import PostgresStorage
from agentmesh.storage.redis import RedisStorage
from agentmesh.core.agent_card import AgentCard
from agentmesh.core.security import SecurityManager
from agentmesh.core.telemetry import TelemetryManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    print("🚀 Starting direct DB seeding...")
    
    # Try Postgres first
    storage = None
    try:
        print("🔌 Connecting to Postgres...")
        storage = PostgresStorage(dsn="postgresql://localhost:5432/agentmesh")
        await storage.connect()
        print("✅ Connected to Postgres")
    except Exception as e:
        print(f"❌ Postgres connection failed: {e}")
        
        # Try Redis
        try:
            print("🔌 Connecting to Redis...")
            storage = RedisStorage(url="redis://localhost:6379")
            await storage.connect()
            print("✅ Connected to Redis")
        except Exception as e2:
            print(f"❌ Redis connection failed: {e2}")
            print("❌ No storage available. Cannot seed.")
            return

    # Initialize Registry
    security = SecurityManager()
    telemetry = TelemetryManager()
    registry = AgentRegistry(security, storage=storage, telemetry=telemetry)
    
    # Generate and Register Agents
    import random
    import uuid
    
    PREFIXES = ["Quantum", "Neural", "Cyber", "Eco", "Data", "Cloud", "Edge", "Meta", "Hyper", "Nano"]
    SUFFIXES = ["Sentinel", "Oracle", "Nexus", "Node", "Gateway", "Engine", "Core", "Link", "Pulse", "Mind"]
    DOMAINS = ["finance", "health", "weather", "security", "supply-chain", "gaming", "social", "iot", "logistics", "edu"]

    tasks = []
    
    print("🌱 Generating 1000 agents...")
    
    for i in range(1000):
        domain = random.choice(DOMAINS)
        name = f"{random.choice(PREFIXES)} {random.choice(SUFFIXES)} {i}"
        agent_id = f"did:agent:{uuid.uuid4().hex}"
        
        card_data = {
            "id": agent_id,
            "name": name,
            "description": f"A specialized agent for {domain} tasks.",
            "version": "0.1.0",
            "skills": [
                {
                    "name": "ping",
                    "description": "Respond with pong",
                    "schema": {"type": "object", "properties": {}}
                }
            ],
            "endpoint": f"http://localhost:{8000 + i}/v1",
            "protocol": "http",
            "trust_score": random.uniform(0.1, 0.99),
            "tags": [domain, "simulation", f"shard-{i % 10}"],
            "network_profile": {
                "nat_type": random.choice(["symmetric", "full_cone", "restricted_cone", "unknown"]),
                "public_endpoints": [],
                "p2p_protocols": ["udp-json"]
            },
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z"
        }
        
        agent_card = AgentCard(**card_data)
        
        # We can use registry.register_agent or direct storage.save_agent
        # register_agent might trigger side effects (telemetry, trust) which is good
        # But for speed, direct storage save might be faster if we don't care about trust init
        # Let's use register_agent to be safe
        tasks.append(registry.register_agent(agent_card))
        
        if len(tasks) >= 50:
            await asyncio.gather(*tasks, return_exceptions=True)
            print(f"✅ Batch {i//50 + 1} registered")
            tasks = []
            
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
        print("✅ Final batch registered")
        
    print("✨ Seeding complete!")
    await storage.close()

if __name__ == "__main__":
    asyncio.run(main())
