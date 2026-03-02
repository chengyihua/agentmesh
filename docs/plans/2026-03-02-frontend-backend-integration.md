# Frontend-Backend Integration Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Verify the full system functionality by running both backend and frontend, simulating agent activities, and observing real-time UI updates.

**Architecture:**
- **Backend**: FastAPI server running on port 8000 (with SSE enabled).
- **Frontend**: Next.js app running on port 3000 (proxying /api to 8000).
- **Simulation**: Python script to act as a dynamic agent (registering, heartbeating, updating).

**Tech Stack:** Python, React, SSE, Shell

---

### Task 1: Environment Setup & Backend Launch

**Files:**
- Modify: `web/next.config.js` (Ensure proxy is configured correctly)
- Run: Backend Server

**Step 1: Verify Next.js Proxy Config**

Check `web/next.config.js` or `web/next.config.mjs`. Ensure it rewrites `/api/:path*` to `http://localhost:8000/api/v1/:path*` (or similar). Since our backend exposes `/api/v1` but also `/events` at root, we need to handle both.

Proposed config check:
```javascript
rewrites() {
    return [
        { source: '/api/events', destination: 'http://127.0.0.1:8000/events' },
        { source: '/api/:path*', destination: 'http://127.0.0.1:8000/api/v1/:path*' },
    ]
}
```

**Step 2: Start Backend**

Command: `python -m src.agentmesh.main serve --storage memory --debug`

### Task 2: Frontend Launch

**Files:**
- Run: Frontend Dev Server

**Step 1: Start Next.js**

Command: `cd web && npm run dev`

### Task 3: Integration Simulation Script

**Files:**
- Create: `scripts/simulate_agent.py`

**Step 1: Create Simulation Script**

Create `scripts/simulate_agent.py`:
```python
import asyncio
import httpx
import random
from datetime import datetime

BASE_URL = "http://localhost:8000"

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
        resp = await client.post(f"{BASE_URL}/api/v1/agents", json=payload)
        print(f"Register status: {resp.status_code}")
        
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
```

### Task 4: Verification Checklist (Manual)

**Files:**
- None (Manual observation)

**Step 1: Run Simulation & Observe UI**

1. Open browser to `http://localhost:3000/agents`.
2. Run `python scripts/simulate_agent.py`.
3. **Verify**:
   - Agent appears in the list automatically (SSE `agent_registered`).
   - Agent status stays green initially.
   - Agent status turns yellow/red when script sends "unhealthy" (SSE `agent_health_changed`).
   - Agent status turns green again when recovered.
