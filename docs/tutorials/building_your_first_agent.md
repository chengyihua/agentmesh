# Building Your First Agent

This tutorial builds a small weather agent service and registers it to AgentMesh.

## Prerequisites

- Python 3.8+
- AgentMesh repository cloned locally
- `pip install agentmesh-python` (or `pip install -e .` from source)

## 1) Start AgentMesh

```bash
python -m agentmesh serve --storage memory --port 8000
```

## 2) Create a simple weather agent service

Create `weather_agent.py`:

```python
from datetime import datetime, timezone
from fastapi import FastAPI

app = FastAPI(title="Weather Agent")

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/weather")
async def weather(city: str):
    return {
        "city": city,
        "temperature_c": 22,
        "condition": "sunny"
    }
```

Run it:

```bash
uvicorn weather_agent:app --host 0.0.0.0 --port 8001
```

## 3) Register agent in AgentMesh

Create `register_weather_agent.py`:

```python
import asyncio
from agentmesh import AgentMeshClient

AGENT = {
    "id": "weather-agent-001",
    "name": "WeatherAgent",
    "version": "1.0.0",
    "description": "Simple weather service",
    "skills": [
        {
            "name": "get_weather",
            "description": "Get weather by city"
        }
    ],
    "endpoint": "http://localhost:8001",
    "protocol": "http",
    "tags": ["weather", "demo"],
    "health_status": "healthy"
}

async def main():
    async with AgentMeshClient(base_url="http://localhost:8000") as client:
        print(await client.register_agent(AGENT))
        print(await client.get_agent("weather-agent-001"))

asyncio.run(main())
```

Run:

```bash
python register_weather_agent.py
```

## 4) Discover the agent

Using cURL:

```bash
curl "http://localhost:8000/api/v1/agents/discover?skill=get_weather"
```

Using SDK:

```python
import asyncio
from agentmesh import AgentMeshClient

async def main():
    async with AgentMeshClient(base_url="http://localhost:8000") as client:
        result = await client.discover_agents(skill="get_weather")
        print(result["data"]["agents"])

asyncio.run(main())
```

## 5) Send heartbeat

```python
import asyncio
from agentmesh import AgentMeshClient

async def main():
    async with AgentMeshClient(base_url="http://localhost:8000") as client:
        print(await client.send_heartbeat("weather-agent-001", status="healthy"))
        print(await client.check_agent_health("weather-agent-001"))

asyncio.run(main())
```

## 6) Update and delete

```bash
agentmesh config set endpoint http://localhost:8000
agentmesh agents update weather-agent-001 --description "Updated weather service"
agentmesh agents delete weather-agent-001
```

## 7) Optional: protect write routes with API key

Start server with key:

```bash
python -m agentmesh serve --storage memory --port 8000 --api-key my-key --auth-secret my-secret
```

Register with SDK using API key:

```python
client = AgentMeshClient(base_url="http://localhost:8000", api_key="my-key")
```

Issue token:

```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"weather-agent-001","secret":"my-secret"}'
```
