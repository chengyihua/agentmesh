# Frontend Perfection and Backend Enhancement Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement secure PoW registration flow in frontend and enhance backend agent listing with server-side sorting.

**Architecture:**
- Frontend: TypeScript `solvePoW` utility using Web Crypto API.
- Backend: Python `AgentRegistry` update to support sorting by trust score.
- API: Exposed query parameters for sorting.

**Tech Stack:**
- Frontend: Next.js, TypeScript, React Query, Web Crypto API.
- Backend: Python, FastAPI.

---

### Task 1: Backend - Sorting Logic in Registry

**Files:**
- Modify: `src/agentmesh/core/registry.py`

**Step 1: Create test for sorting**

Create `tests/test_registry_sorting.py`:

```python
import pytest
import asyncio
from datetime import datetime, timedelta
from agentmesh.core.registry import AgentRegistry
from agentmesh.core.agent_card import AgentCard, HealthStatus

@pytest.mark.asyncio
async def test_list_agents_sorting():
    registry = AgentRegistry()
    
    # Create 3 agents with different trust scores (simulated via mocking or direct assignment)
    agent1 = AgentCard(id="agent1", name="A1", version="1.0", endpoint="http://a1", trust_score=0.1)
    agent2 = AgentCard(id="agent2", name="A2", version="1.0", endpoint="http://a2", trust_score=0.9)
    agent3 = AgentCard(id="agent3", name="A3", version="1.0", endpoint="http://a3", trust_score=0.5)
    
    # Manually inject agents since we want specific trust scores
    registry.agents = {
        "agent1": agent1,
        "agent2": agent2,
        "agent3": agent3,
    }
    
    # Mock trust manager or assign directly? 
    # Registry.list_agents calculates trust score on the fly.
    # We need to mock calculate_trust_score to return consistent values.
    
    async def mock_calculate_trust(agent_id):
        if agent_id == "agent1": return 0.1
        if agent_id == "agent2": return 0.9
        if agent_id == "agent3": return 0.5
        return 0.0
        
    registry.calculate_trust_score = mock_calculate_trust
    
    # Test sort by trust_score desc (default)
    agents = await registry.list_agents(sort_by="trust_score", order="desc")
    assert agents[0].id == "agent2"
    assert agents[1].id == "agent3"
    assert agents[2].id == "agent1"
    
    # Test sort by trust_score asc
    agents = await registry.list_agents(sort_by="trust_score", order="asc")
    assert agents[0].id == "agent1"
    assert agents[1].id == "agent3"
    assert agents[2].id == "agent2"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_registry_sorting.py`
Expected: FAIL (TypeError: list_agents() got an unexpected keyword argument 'sort_by')

**Step 3: Implement sorting in Registry**

Modify `src/agentmesh/core/registry.py`:

```python
    async def list_agents(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        sort_by: str = "updated_at", 
        order: str = "desc"
    ) -> List[AgentCard]:
        """List agents with pagination and sorting."""
        
        # Pre-calculate trust scores if sorting by trust
        if sort_by == "trust_score":
            for agent in self.agents.values():
                if agent.trust_score is None: # Optimization: avoid recalc if cached/fresh
                     agent.trust_score = await self.calculate_trust_score(agent.id)

        # Define sort key
        key_func = lambda x: getattr(x, sort_by, 0)
        if sort_by == "trust_score":
             key_func = lambda x: x.trust_score or 0.0
        elif sort_by == "updated_at":
             key_func = lambda x: x.updated_at.timestamp()
        elif sort_by == "created_at":
             key_func = lambda x: x.created_at.timestamp()
             
        reverse = (order.lower() == "desc")
        
        agents = sorted(self.agents.values(), key=key_func, reverse=reverse)
        paginated = agents[skip : skip + limit]
        
        # Ensure trust score is calculated for returned agents (if not already done)
        if sort_by != "trust_score":
            for agent in paginated:
                agent.trust_score = await self.calculate_trust_score(agent.id)
            
        return paginated
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_registry_sorting.py`
Expected: PASS

**Step 5: Commit**

```bash
git add src/agentmesh/core/registry.py tests/test_registry_sorting.py
git commit -m "feat: add server-side sorting to list_agents"
```

---

### Task 2: Backend - Expose Sorting in API

**Files:**
- Modify: `src/agentmesh/api/routes.py`

**Step 1: Update list_agents route**

Modify `src/agentmesh/api/routes.py`:

```python
@router.get("/agents")
async def list_agents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    sort_by: str = Query("updated_at", regex="^(updated_at|created_at|trust_score)$"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    registry: AgentRegistry = Depends(get_registry),
):
    agents = await registry.list_agents(skip=skip, limit=limit, sort_by=sort_by, order=order)
    return success_response(
        {
            "agents": [agent.to_dict() for agent in agents],
            "total": len(agents),
            "limit": limit,
            "offset": skip,
            "sort_by": sort_by,
            "order": order,
        },
        message="Agents retrieved successfully",
    )
```

**Step 2: Commit**

```bash
git add src/agentmesh/api/routes.py
git commit -m "feat: expose sort params in /agents endpoint"
```

---

### Task 3: Frontend - PoW Utility

**Files:**
- Create: `web/src/utils/pow.ts`

**Step 1: Create utility**

```typescript
/**
 * Solves a Proof of Work challenge.
 * Finds a suffix such that SHA256(nonce + suffix) starts with '0' * difficulty (in hex).
 * 
 * @param nonce The challenge nonce string
 * @param difficulty The number of leading zero hex characters required
 * @returns The solution string (suffix)
 */
export async function solvePoW(nonce: string, difficulty: number): Promise<string> {
    const encoder = new TextEncoder();
    let counter = 0;
    
    while (true) {
        const solution = counter.toString();
        const data = encoder.encode(nonce + solution);
        const hashBuffer = await crypto.subtle.digest('SHA-256', data);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
        
        if (hashHex.startsWith('0'.repeat(difficulty))) {
            return solution;
        }
        
        counter++;
        
        // Yield to main thread every 1000 iterations to avoid freezing UI completely
        if (counter % 1000 === 0) {
             await new Promise(resolve => setTimeout(resolve, 0));
        }
    }
}
```

**Step 2: Commit**

```bash
git add web/src/utils/pow.ts
git commit -m "feat: add client-side PoW solver"
```

---

### Task 4: Frontend - Registration Page Update

**Files:**
- Modify: `web/src/app/register/page.tsx`

**Step 1: Add fetchChallenge function**

Add inside `RegisterPage` component or outside:

```typescript
async function fetchChallenge() {
    const res = await axios.get(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/auth/challenge`);
    return res.data.data; // { nonce, difficulty, ttl_seconds }
}
```

**Step 2: Update handleRegister**

Replace the simulated logic with:

```typescript
import { solvePoW } from "@/utils/pow";

// Inside handleRegister:
    try {
        // Step 1: Get Challenge
        addLog("Requesting PoW Challenge from Registry...", "info");
        const challenge = await fetchChallenge();
        addLog(`Challenge received: Difficulty ${challenge.difficulty}`, "success");
        
        // Step 2: Solve PoW
        addLog("Mining PoW solution...", "pending");
        const startTime = Date.now();
        const solution = await solvePoW(challenge.nonce, challenge.difficulty);
        const duration = ((Date.now() - startTime) / 1000).toFixed(2);
        addLog(`PoW Solved in ${duration}s! Solution: ${solution}`, "success");

        // Step 3: Register
        const data = JSON.parse(jsonInput);
        addLog(`Connecting to Registry Node...`, "pending");
        
        const res = await axios.post(
            `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/agents/register`, 
            data,
            {
                headers: {
                    "X-PoW-Nonce": challenge.nonce,
                    "X-PoW-Solution": solution
                }
            }
        );
        
        // ... success handling ...
```

**Step 3: Commit**

```bash
git add web/src/app/register/page.tsx
git commit -m "feat: implement real PoW registration flow"
```

---

### Task 5: Frontend - Agent List Sorting

**Files:**
- Modify: `web/src/hooks/useRegistry.ts`
- Modify: `web/src/app/agents/page.tsx`

**Step 1: Update hook**

```typescript
export function useAgents(sortBy = "updated_at", order = "desc") {
    return useQuery<Agent[]>({
        queryKey: ["agents", sortBy, order],
        queryFn: async () => {
            const response = await axios.get(`${API_BASE}/agents`, {
                params: { sort_by: sortBy, order }
            });
            return response.data.data.agents;
        },
    });
}
```

**Step 2: Update Page**

Modify `AgentsPage` to use the new hook signature and update state when user clicks sort buttons.

**Step 3: Commit**

```bash
git add web/src/hooks/useRegistry.ts web/src/app/agents/page.tsx
git commit -m "feat: use server-side sorting for agent list"
```
