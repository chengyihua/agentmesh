import asyncio
import json
import os
import sys
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from agentmesh.storage.redis import RedisStorage
from agentmesh.core.agent_card import AgentCard

async def migrate():
    print("Starting migration of Redis ZSET index...")
    storage = RedisStorage()
    await storage.connect()
    
    # We can't use list_agents because it's broken (depends on ZSET)
    # So we access _client directly
    client = storage._client
    
    keys = []
    async for key in client.scan_iter(match=f"{storage.prefix}agent:*"):
        keys.append(key)
        
    print(f"Found {len(keys)} agent keys.")
    
    count = 0
    async with client.pipeline() as pipe:
        # Iterate over keys, but we need values
        # Batch get values
        for i in range(0, len(keys), 100):
            batch_keys = keys[i:i+100]
            if not batch_keys:
                continue
                
            raw_values = await client.mget(batch_keys)
            
            for raw in raw_values:
                if not raw:
                    continue
                    
                try:
                    data = json.loads(raw)
                    # We can't validate fully because pydantic might be strict, let's just use dict
                    # agent = AgentCard.model_validate(data)
                    agent_id = data.get("id")
                    updated_at_str = data.get("updated_at")
                    
                    if not agent_id or not updated_at_str:
                        continue
                        
                    # Parse timestamp
                    try:
                        ts = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00")).timestamp()
                    except:
                        ts = datetime.now().timestamp()
                    
                    pipe.zadd(storage._updated_at_key(), {agent_id: ts})
                    count += 1
                except Exception as e:
                    print(f"Error parsing agent: {e}")
            
            # Execute batch
            await pipe.execute()
            print(f"Processed {count} agents...")
        
    print(f"Migration complete. Indexed {count} agents.")
    await storage.close()

if __name__ == "__main__":
    asyncio.run(migrate())
