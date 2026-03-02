import asyncio
import httpx
import random
from datetime import datetime

BASE_URL = "http://localhost:3000"

async def main():
    agent_id = f"sim-agent-{random.randint(1000, 9999)}"
    print(f"🚀 Starting simulation for {agent_id}")
    
    async with httpx.AsyncClient() as client:
        # 1. Register
        print("Registering...")
        payload = {
            "id": agent_id,
            "name": f"Simulator {agent_id}",
            "version": "1.0.0",
            "endpoint": f"http://localhost:9000/{agent_id}",
            "skills": [{"name": "simulation", "description": "Generating fake traffic"}],
            "tags": ["sim", "test"]
        }
        try:
            # Add proper headers
            headers = {"Content-Type": "application/json"}
            resp = await client.post(f"{BASE_URL}/api/v1/agents", json=payload, headers=headers)
            print(f"Register status: {resp.status_code}")
            if resp.status_code >= 400:
                print(f"Error: {resp.text}")
                return
        except Exception as e:
            print(f"Request failed: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # 2. Heartbeats (Healthy)
        for i in range(5):
            print(f"Sending Heartbeat {i+1}/5...")
            await client.post(f"{BASE_URL}/api/v1/agents/{agent_id}/heartbeat", json={"status": "healthy"})
            await asyncio.sleep(2)
            
        # 3. Degrade Health
        print("Degrading health...")
        await client.post(f"{BASE_URL}/api/v1/agents/{agent_id}/heartbeat", json={"status": "unhealthy"})
        await asyncio.sleep(5)
        
        # 4. Recover
        print("Recovering...")
        await client.post(f"{BASE_URL}/api/v1/agents/{agent_id}/heartbeat", json={"status": "healthy"})
        
        print("Simulation complete.")

if __name__ == "__main__":
    asyncio.run(main())
