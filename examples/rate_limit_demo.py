"""
Rate Limit Demo Script for AgentMesh
Demonstrates QPS budget and Concurrency limits in action.
"""
import asyncio
import time
from agentmesh.core.agent_card import AgentCard
from agentmesh.core.rate_limit import AgentRateLimiter

async def worker(limiter, agent, request_id):
    """Simulates a single request"""
    start = time.time()
    try:
        async with limiter.limit(agent):
            # Simulate processing time
            await asyncio.sleep(0.1)
            print(f"Request {request_id}: Success")
            return True
    except Exception as e:
        print(f"Request {request_id}: Failed ({e.detail['reason'] if hasattr(e, 'detail') else str(e)})")
        return False

async def main():
    print("Initializing Rate Limit Demo...")
    
    # Define an agent with 5 QPS and 2 Concurrent Requests
    agent = AgentCard(
        id="demo-agent",
        name="Demo Agent",
        version="1.0.0",
        endpoint="http://localhost",
        skills=[{"name": "test", "description": "test"}],
        qps_budget=5.0,
        concurrency_limit=2
    )
    
    limiter = AgentRateLimiter()
    
    print(f"Agent Configuration: QPS={agent.qps_budget}, Concurrency={agent.concurrency_limit}")
    print("\n--- Phase 1: Concurrency Test (Send 5 requests instantly) ---")
    tasks = []
    for i in range(5):
        tasks.append(worker(limiter, agent, i))
    
    results = await asyncio.gather(*tasks)
    success_count = sum(1 for r in results if r)
    print(f"Concurrency Test Results: {success_count}/5 successful (Expected ~2 concurrent)")
    
    # Wait for QPS bucket to refill
    print("\nRefilling bucket (wait 2s)...")
    await asyncio.sleep(2.0)
    
    print("\n--- Phase 2: QPS Burst Test (Send 10 requests) ---")
    # Reset concurrency state for clarity (simulating new burst)
    limiter._concurrency = {} 
    
    tasks = []
    start_time = time.time()
    for i in range(10):
        tasks.append(worker(limiter, agent, i + 10))
        # Add slight delay to not hit concurrency limit instantly if desired, 
        # but for QPS test we want to hit rate limit.
        # However, concurrency limit (2) will likely be hit first if we don't delay.
        # Let's increase concurrency limit to isolate QPS test.
    
    agent.concurrency_limit = 100
    print(f"Agent Configuration Updated: QPS={agent.qps_budget}, Concurrency={agent.concurrency_limit}")
    
    results = await asyncio.gather(*tasks)
    end_time = time.time()
    
    success_count = sum(1 for r in results if r)
    print(f"QPS Test Results: {success_count}/10 successful in {end_time - start_time:.2f}s (Expected ~5-6 due to bucket + refill)")

if __name__ == "__main__":
    asyncio.run(main())
