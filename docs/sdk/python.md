# Python SDK

This document describes the SDK implemented in `src/agentmesh/client.py`.

## Installation

From PyPI:

```bash
pip install agentmesh-python
```

From this repository (source):

```bash
pip install -e .
```

If you invoke `grpc` or `websocket` protocol agents through SDK, install extras:

```bash
pip install "agentmesh-python[grpc,websocket]"
# or from source
pip install -e ".[grpc,websocket]"
```

## Imports

```python
from agentmesh import AgentMeshClient, SyncAgentMeshClient
```

## Async Client (`AgentMeshClient`)

### Initialization

```python
client = AgentMeshClient(
    base_url="http://localhost:8000",
    api_key=None,
    token=None,
    timeout=30.0,
)
```

Supported constructor args:

- `base_url`
- `api_key`
- `token`
- `timeout`
- `health_check_interval`
- `health_check_timeout`

### Lifecycle

```python
# preferred
async with AgentMeshClient(base_url="http://localhost:8000") as client:
    ...

# or manual
client = AgentMeshClient(base_url="http://localhost:8000")
...
await client.close()
```

### Methods

- `register_agent(agent)`
- `get_agent(agent_id)`
- `list_agents(skip=0, limit=100)`
- `update_agent(agent_id, update_data)`
- `deregister_agent(agent_id)`
- `delete_agent(agent_id)` (alias of `deregister_agent`)
- `discover_agents(skill_name=None, skill=None, tags=None, tag=None, protocol=None, q=None, healthy_only=True, limit=20, offset=0)`
- `search_agents(q, skill=None, tags=None, protocol=None, limit=20, offset=0)`
- `send_heartbeat(agent_id, status="healthy", timestamp=None)`
- `check_agent_health(agent_id)`
- `batch_health_check(agent_ids)`
- `get_stats()`
- `get_agent_stats(agent_id)`
- `invoke_agent(agent_id, payload=None, skill=None, path=None, method="POST", timeout_seconds=30.0, headers=None)`
- `get_token(agent_id, secret)`
- `refresh_token(refresh_token)`
- `verify_token(token=None)`
- `clear_cache()`

## Sync Client (`SyncAgentMeshClient`)

`SyncAgentMeshClient` is for scripts and CLI-like sync flows.

### Methods

- `register_agent(agent)`
- `list_agents(skip=0, limit=100)`
- `get_agent(agent_id)`
- `update_agent(agent_id, update_data)`
- `deregister_agent(agent_id)`
- `invoke_agent(agent_id, payload=None, skill=None, path=None, method="POST", timeout_seconds=30.0, headers=None)`
- `search_agents(skill=None, q=None)`
- `close()`

Note:

- `search_agents(q=...)` calls `/api/v1/agents/search`.
- `search_agents(skill=...)` calls `/api/v1/agents/discover`.

## Examples

### Register + discover (async)

```python
import asyncio
from agentmesh import AgentMeshClient

async def main():
    async with AgentMeshClient(base_url="http://localhost:8000") as client:
        await client.register_agent({
            "id": "sdk-bot-001",
            "name": "SDKBOT",
            "version": "1.0.0",
            "skills": [{"name": "echo", "description": "Echo"}],
            "endpoint": "http://localhost:9000/echo",
            "protocol": "http",
            "health_status": "healthy"
        })

        result = await client.discover_agents(skill="echo")
        print(result["data"]["agents"])

asyncio.run(main())
```

### Token flow

```python
import asyncio
from agentmesh import AgentMeshClient

async def main():
    async with AgentMeshClient(base_url="http://localhost:8000") as client:
        token_data = await client.get_token("sdk-bot-001", "agentmesh-dev-secret")
        access = token_data["data"]["access_token"]

        verified = await client.verify_token(token=access)
        print(verified["data"])

        refresh = token_data["data"]["refresh_token"]
        print((await client.refresh_token(refresh))["data"])

asyncio.run(main())
```

### Protocol invocation

```python
import asyncio
from agentmesh import AgentMeshClient

async def main():
    async with AgentMeshClient(base_url="http://localhost:8000") as client:
        result = await client.invoke_agent(
            "sdk-bot-001",
            payload={"city": "Tokyo"},
            skill="get_weather",
            path="/weather",
        )
        print(result["data"]["result"])

asyncio.run(main())
```

### Sync usage

```python
from agentmesh import SyncAgentMeshClient

client = SyncAgentMeshClient(base_url="http://localhost:8000")
try:
    print(client.list_agents())
finally:
    client.close()
```

## Error Handling

SDK methods call `httpx` and raise `httpx.HTTPStatusError` for non-2xx responses.

Example:

```python
import httpx

try:
    await client.get_agent("missing-agent")
except httpx.HTTPStatusError as exc:
    print(exc.response.status_code)
    print(exc.response.json())
```

## API Compatibility Notes

- SDK expects server routes under `/api/v1`.
- Auth headers are added automatically from `api_key` and `token` constructor values.
- `verify_token(token=...)` sends token via `Authorization: Bearer <token>`.
