# AgentMesh Interactive Examples

## 1) Start server

```bash
python -m agentmesh serve --storage memory --port 8000
```

## 2) Register one agent

```bash
curl -X POST http://localhost:8000/api/v1/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "id": "weather-bot-001",
    "name": "WeatherBot",
    "version": "1.0.0",
    "description": "Weather forecasting service",
    "skills": [{"name": "get_weather", "description": "Get weather"}],
    "endpoint": "http://localhost:8001/weather",
    "protocol": "http",
    "tags": ["weather", "api"],
    "health_status": "healthy"
  }'
```

## 3) Discover and search

```bash
curl "http://localhost:8000/api/v1/agents/discover?skill=get_weather"
curl "http://localhost:8000/api/v1/agents/discover?tag=weather&tag=api"
curl "http://localhost:8000/api/v1/agents/search?q=weather"
```

## 4) Health and stats

```bash
curl -X POST http://localhost:8000/api/v1/agents/weather-bot-001/heartbeat \
  -H "Content-Type: application/json" \
  -d '{"status": "healthy"}'

curl http://localhost:8000/api/v1/agents/weather-bot-001/health
curl http://localhost:8000/api/v1/agents/weather-bot-001/stats
curl http://localhost:8000/api/v1/stats
```

## 5) Token endpoints

```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"weather-bot-001","secret":"agentmesh-dev-secret"}'
```

```bash
curl http://localhost:8000/api/v1/auth/verify \
  -H "Authorization: Bearer <access_token>"
```

## 6) Invoke a registered agent via protocol gateway

```bash
curl -X POST http://localhost:8000/api/v1/agents/weather-bot-001/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "skill": "get_weather",
    "payload": {"city": "Tokyo"},
    "path": "/weather",
    "method": "POST"
  }'
```

## 7) Python SDK (async)

```python
import asyncio
from agentmesh import AgentMeshClient

async def main():
    async with AgentMeshClient(base_url="http://localhost:8000") as client:
        await client.register_agent({
            "id": "translate-bot-001",
            "name": "TranslationBot",
            "version": "1.0.0",
            "description": "Translation service",
            "skills": [{"name": "translate_text", "description": "Translate text"}],
            "endpoint": "http://localhost:8002/translate",
            "protocol": "http",
            "tags": ["translation", "nlp"],
            "health_status": "healthy"
        })

        discovered = await client.discover_agents(skill="translate_text")
        print(discovered["data"]["agents"])
        print((await client.get_agent("translate-bot-001"))["data"]["agent"])
        print((await client.invoke_agent("translate-bot-001", payload={"text": "hello"}, path="/translate"))["data"]["result"])

asyncio.run(main())
```

## 8) CLI flow

```bash
agentmesh config set endpoint http://localhost:8000
agentmesh agents register --id cli-agent-001 --name CLIAgent --skill execute_command --tag cli
agentmesh agents list
agentmesh agents search --skill execute_command
agentmesh agents get cli-agent-001
agentmesh agents invoke cli-agent-001 --payload '{"task":"echo"}'
agentmesh agents delete cli-agent-001
```
