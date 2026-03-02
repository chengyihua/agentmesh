import asyncio
import httpx
import random
import uuid
import time

BASE_URL = "http://127.0.0.1:8000"

# Pre-defined tags to simulate different agent types
TAGS = [
    "compute", "storage", "network", "ai", "inference", "database", 
    "cache", "gateway", "sensor", "iot", "mobile", "desktop"
]

async def register_agent(client, i):
    # Generate a deterministic ID based on index for easier debugging if needed, 
    # but append random part to ensure uniqueness across runs if database isn't cleared.
    # Actually, let's use random UUID to ensure we hit different regions in the hash function.
    agent_id = f"agent-{uuid.uuid4().hex[:12]}"
    
    # Simulate different trust scores to create visual hierarchy
    # Most agents are average, some are high trust
    r = random.random()
    if r > 0.95:
        trust_score = random.uniform(0.9, 0.99) # Elite
    elif r > 0.8:
        trust_score = random.uniform(0.7, 0.9) # High
    else:
        trust_score = random.uniform(0.1, 0.7) # Normal
        
    payload = {
        "id": agent_id,
        "name": f"Node {i:04d}",
        "version": "1.0.0",
        "endpoint": f"http://10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}:8000",
        "skills": [{"name": "process", "description": "General processing unit"}],
        "tags": random.sample(TAGS, k=random.randint(1, 3)),
        "trust_score": trust_score,
        "health_status": "healthy" if random.random() > 0.05 else "unhealthy" # 5% unhealthy
    }
    
    try:
        resp = await client.post(f"{BASE_URL}/api/v1/agents", json=payload)
        if resp.status_code in [200, 201]:
            return True
        else:
            if i < 5: # Only print first few errors
                print(f"Failed {agent_id}: {resp.status_code} {resp.text}")
            return False
    except Exception as e:
        if i < 5:
            print(f"Error {agent_id}: {e}")
        return False

async def main():
    print(f"🚀 Starting massive agent simulation (target: 1000 agents)...")
    print(f"📡 Connecting to {BASE_URL}")
    
    start_time = time.time()
    success_count = 0
    
    # Increase limits for high concurrency
    limits = httpx.Limits(max_keepalive_connections=100, max_connections=100)
    
    async with httpx.AsyncClient(timeout=30.0, limits=limits, trust_env=False) as client:
        # Check if server is up
        try:
            await client.get(f"{BASE_URL}/api/v1/agents?limit=1")
        except Exception:
            print("❌ Server not reachable. Please start the backend with 'make run' or 'agentmesh serve'")
            return

        tasks = []
        total_agents = 1000
        batch_size = 50
        
        for i in range(total_agents):
            tasks.append(register_agent(client, i))
            
            if len(tasks) >= batch_size:
                results = await asyncio.gather(*tasks)
                success_count += sum(1 for r in results if r)
                tasks = []
                
                # Progress bar
                progress = (i + 1) / total_agents
                bar_length = 30
                filled_length = int(bar_length * progress)
                bar = '█' * filled_length + '-' * (bar_length - filled_length)
                print(f"\r[{bar}] {int(progress * 100)}% ({success_count}/{i+1})", end="")
        
        # Process remaining
        if tasks:
            results = await asyncio.gather(*tasks)
            success_count += sum(1 for r in results if r)
            
    duration = time.time() - start_time
    print(f"\n\n✅ Simulation complete!")
    print(f"Successfully registered: {success_count}/{total_agents}")
    print(f"Time taken: {duration:.2f}s ({success_count/duration:.1f} agents/sec)")

if __name__ == "__main__":
    asyncio.run(main())
