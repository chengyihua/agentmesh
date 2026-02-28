# AgentMesh Quick Start

## 1. Install

```bash
# Install from PyPI
pip install agentmesh-python

# optional extras for grpc/websocket invoke bridges
pip install "agentmesh-python[grpc,websocket]"

# Or install from source
pip install -e .
```

## 2. Run server

```bash
# in-memory (default)
python -m agentmesh serve --storage memory --port 8000

# Redis
python -m agentmesh serve --storage redis --redis-url redis://localhost:6379 --port 8000

# PostgreSQL
python -m agentmesh serve --storage postgres --postgres-url postgresql://localhost:5432/agentmesh --port 8000

# production safety mode
python -m agentmesh serve --storage postgres --postgres-url postgresql://localhost:5432/agentmesh \
  --api-key YOUR_API_KEY --auth-secret YOUR_STRONG_SECRET --production --port 8000
```

## 3. Register and discover with SDK

```python
import asyncio
from agentmesh import AgentMeshClient

async def main():
    async with AgentMeshClient(base_url="http://localhost:8000") as client:
        await client.register_agent({
            "id": "weather-bot-001",
            "name": "WeatherBot",
            "version": "1.0.0",
            "description": "Weather forecasting service",
            "skills": [{"name": "get_weather", "description": "Get weather"}],
            "endpoint": "http://localhost:8001/weather",
            "protocol": "http",
            "tags": ["weather", "api"],
            "health_status": "healthy"
        })

        discovered = await client.discover_agents(skill="get_weather")
        print(discovered["data"]["agents"])

        await client.send_heartbeat("weather-bot-001")
        print((await client.check_agent_health("weather-bot-001"))["data"])

        invoke_result = await client.invoke_agent(
            "weather-bot-001",
            payload={"city": "Tokyo"},
            skill="get_weather",
            path="/weather",
        )
        print(invoke_result["data"]["result"]["response"])

asyncio.run(main())
```

## 4. CLI workflow

```bash
agentmesh config set endpoint http://localhost:8000

agentmesh agents register \
  --id cli-agent-001 \
  --name CLIAgent \
  --description "CLI demo agent" \
  --skill execute_command \
  --tag cli

agentmesh agents list
agentmesh agents search --skill execute_command
agentmesh agents get cli-agent-001
agentmesh agents invoke cli-agent-001 --payload '{"task":"ping"}'
agentmesh agents update cli-agent-001 --description "Updated description"
agentmesh agents delete cli-agent-001
```

## 5. Token flow

```python
import asyncio
from agentmesh import AgentMeshClient

async def main():
    async with AgentMeshClient(base_url="http://localhost:8000") as client:
        token_resp = await client.get_token("weather-bot-001", "agentmesh-dev-secret")
        access = token_resp["data"]["access_token"]
        refresh = token_resp["data"]["refresh_token"]

        print((await client.verify_token(token=access))["data"])
        print((await client.refresh_token(refresh))["data"])

asyncio.run(main())
```

## 6. Check service endpoints

```bash
curl http://localhost:8000/health
curl http://localhost:8000/version
curl http://localhost:8000/api/v1/stats
```
