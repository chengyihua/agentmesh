import asyncio
import httpx
import random
import uuid
from typing import List

API_BASE = "http://localhost:8000"

# Sample data for generation
PREFIXES = ["Quantum", "Neural", "Cyber", "Eco", "Data", "Cloud", "Edge", "Meta", "Hyper", "Nano"]
SUFFIXES = ["Sentinel", "Oracle", "Nexus", "Node", "Gateway", "Engine", "Core", "Link", "Pulse", "Mind"]
DOMAINS = ["finance", "health", "weather", "security", "supply-chain", "gaming", "social", "iot", "logistics", "edu"]
PROTOCOLS = ["http", "grpc", "ws", "mcp"]

def generate_agent_payload(index: int):
    domain = random.choice(DOMAINS)
    name = f"{random.choice(PREFIXES)} {random.choice(SUFFIXES)} {index}"
    agent_id = f"did:agent:{uuid.uuid4().hex}"
    
    return {
        "id": agent_id,
        "name": name,
        "endpoint": f"http://localhost:{8000 + index}/v1",
        "referrer": f"did:agent:{uuid.uuid4().hex}" if random.random() > 0.7 else None,
        "webhook_url": f"http://webhook.site/{uuid.uuid4().hex}" if random.random() > 0.8 else None,
        "nat_type": random.choice(["symmetric", "full_cone", "restricted", "unknown"]),
        "p2p_protocols": ["udp-json"],
        # Extra fields that /hello might merge or we might update later
        "description": f"A specialized agent for {domain} tasks.",
        "tags": [domain, "simulation", f"shard-{index % 10}"]
    }

async def register_single(client: httpx.AsyncClient, payload: dict):
    try:
        # Using /hello for frictionless registration (bypasses PoW)
        resp = await client.post(f"{API_BASE}/hello", json=payload)
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"❌ Failed to register {payload['name']}: {e}")
        return False

async def main():
    print("🚀 Starting simulation of 1000 agents...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = []
        for i in range(1000):
            payload = generate_agent_payload(i)
            tasks.append(register_single(client, payload))
            
            # Batch to avoid overwhelming the server connection pool
            if len(tasks) >= 5:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                success_count = sum(1 for r in results if r is True)
                print(f"✅ Batch completed: {success_count}/{len(tasks)} success")
                tasks = []
                await asyncio.sleep(1.0) # Longer breather
        
        if tasks:
            results = await asyncio.gather(*tasks)
            success_count = sum(1 for r in results if r)
            print(f"✅ Final batch completed: {success_count}/{len(tasks)} success")

    print("\n✨ Simulation complete! Check the Network Map.")

if __name__ == "__main__":
    asyncio.run(main())
