# AgentMesh

AgentMesh is an open-source registry and discovery service for AI agents.
It provides a standard `AgentCard` model, REST API, SDK, CLI, optional token auth, and pluggable storage backends.

## What is implemented

- Agent registration, update, deletion, listing
- Agent discovery (skill/protocol/tags/query) and search
- Protocol invocation gateway (`http`, `custom`, `a2a`, `mcp`, `grpc`, `websocket`)
- Heartbeat + health checks
- System and per-agent statistics
- Token endpoints (`/auth/token`, `/auth/refresh`, `/auth/verify`)
- Optional API key protection for write/admin routes
- Production safety mode (`--production`) to require strong auth config
- Signature utilities (`/security/keypair`, `/security/sign`, `/security/verify`)
- Storage backends: memory (default), Redis, PostgreSQL
- Python SDK: async `AgentMeshClient` + sync `SyncAgentMeshClient`
- CLI: `serve`, `config`, `agents` commands

## Install

From PyPI:

```bash
pip install agentmesh-python
```

From source (for development):

```bash
pip install -e .
```

Optional protocol extras (for grpc/websocket invocation bridges):

```bash
pip install "agentmesh-python[grpc,websocket]"
# or from source
pip install -e ".[grpc,websocket]"
```

## Quick start

### 1) Run server

```bash
# in-memory (default)
python -m agentmesh serve --storage memory --port 8000

# Redis
python -m agentmesh serve --storage redis --redis-url redis://localhost:6379 --port 8000

# PostgreSQL
python -m agentmesh serve --storage postgres --postgres-url postgresql://localhost:5432/agentmesh --port 8000

# production safety checks enabled
python -m agentmesh serve --storage postgres --postgres-url postgresql://localhost:5432/agentmesh \
  --api-key YOUR_API_KEY --auth-secret YOUR_STRONG_SECRET --production --port 8000
```

### 2) Register and discover with SDK

```python
import asyncio
from agentmesh import AgentMeshClient

async def main():
    client = AgentMeshClient(base_url="http://localhost:8000")

    await client.register_agent({
        "id": "weather-bot-001",
        "name": "WeatherBot",
        "version": "1.0.0",
        "description": "Weather forecasting service",
        "skills": [
            {"name": "get_weather", "description": "Get current weather"}
        ],
        "endpoint": "http://localhost:8001/weather",
        "protocol": "http",
        "tags": ["weather", "api"],
        "health_status": "healthy"
    })

    result = await client.discover_agents(skill="get_weather")
    print(result["data"]["agents"])

    invoke_result = await client.invoke_agent(
        "weather-bot-001",
        payload={"city": "Tokyo"},
        path="/weather"
    )
    print(invoke_result["data"]["result"]["response"])

    await client.close()

asyncio.run(main())
```

### 3) Web Dashboard (EvoMap UI)

AgentMesh now includes a high-fidelity web console inspired by `evomap.ai`.

```bash
# Register some demo agents first
python seed_registry.py

# Start backend
python -m agentmesh serve --debug

# Start frontend (in a new terminal)
cd web
npm install
npm run dev
```
Visit [http://localhost:3000](http://localhost:3000) to view analytics, search agents (⌘K), and test Manifests in the Sandbox.

### 4) Use CLI

```bash
# configure endpoint
agentmesh config set endpoint http://localhost:8000

# register
agentmesh agents register \
  --id cli-agent-001 \
  --name CLIAgent \
  --description "CLI agent" \
  --skill execute_command \
  --tag cli

# list/search/get/update/delete
agentmesh agents list
agentmesh agents search --skill execute_command
agentmesh agents get cli-agent-001
agentmesh agents invoke cli-agent-001 --payload '{"task":"ping"}'
agentmesh agents update cli-agent-001 --description "Updated description"
agentmesh agents delete cli-agent-001
```

## 🔒 Production Readiness

The server includes a `--production` mode that enforces security best practices:

```bash
agentmesh serve --production \
  --api-key your-production-key \
  --auth-secret your-strong-jwt-secret \
  --storage postgres \
  --postgres-url postgresql://user:pass@db:5432/agentmesh
```

**What production mode enforces:**
- `X-API-Key` is mandatory for all write operations.
- `auth-secret` must be provided and cannot be the default value.
- Rate limiting is enabled on sensitive endpoints.
- Prometheus `/metrics` are exposed for observability.

## API docs

- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

Detailed reference: `docs/protocol/api_reference.md`.

## Response format

Successful responses:

```json
{
  "success": true,
  "data": {},
  "message": "Operation successful",
  "timestamp": "2026-02-23T18:00:00Z"
}
```

Error responses:

```json
{
  "success": false,
  "error": {
    "code": "400",
    "message": "Validation failed",
    "details": {}
  },
  "timestamp": "2026-02-23T18:00:00Z"
}
```

## Run tests

```bash
python -m unittest discover -s tests -v
```

## Project layout

```text
src/agentmesh/
├── __init__.py
├── __main__.py
├── cli.py
├── client.py
├── api/
│   ├── routes.py
│   └── server.py
├── auth/
│   └── token_manager.py
├── core/
│   ├── agent_card.py
│   ├── registry.py
│   └── security.py
├── storage/
│   ├── base.py
│   ├── memory.py
│   ├── redis.py
│   └── postgres.py
├── protocols/
│   ├── base.py
│   ├── gateway.py
│   ├── http_custom.py
│   ├── a2a.py
│   ├── mcp.py
│   ├── grpc.py
│   └── websocket.py
└── utils/
    └── responses.py
```

## License

Apache-2.0
