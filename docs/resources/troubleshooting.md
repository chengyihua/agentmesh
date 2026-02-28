# Troubleshooting

This guide is aligned with current server, SDK, and CLI behavior.

## 1. Server does not respond

Check process and health endpoint:

```bash
python -m agentmesh serve --storage memory --port 8000
curl -i http://localhost:8000/health
```

Expected: HTTP 200 with `success: true`.

## 2. Registration fails (`400`)

Common causes:

- `skills` is empty
- `endpoint` is missing
- invalid `id` characters
- duplicate skill names in one agent card

Quick validation pattern:

```python
from agentmesh.core.agent_card import AgentCard

AgentCard.model_validate(payload)
```

## 3. Registration fails (`401`)

If server started with `--api-key`, protected routes require auth.

Use either:

```http
X-API-Key: <your-key>
```

or

```http
Authorization: Bearer <access_token>
```

## 4. Token endpoints return `401`

`POST /api/v1/auth/token` checks `secret` against server `--auth-secret`.

If you started server with default options, use:

```json
{"agent_id":"your-agent","secret":"agentmesh-dev-secret"}
```

## 5. Discovery returns empty list

Check these points:

1. Agent is actually registered (`GET /api/v1/agents`).
2. `healthy_only=true` hides unhealthy/unknown agents.
3. Skill/tag values are exact matches.

Try:

```bash
curl "http://localhost:8000/api/v1/agents/discover?healthy_only=false&limit=100"
```

## 6. `429 Too Many Requests`

Current limits:

- Register/update/delete: 60/minute
- Heartbeat: 120/minute

Mitigation:

1. Backoff and retry.
2. Batch operations where possible.
3. Avoid bursty re-registration loops.

## 7. Redis/PostgreSQL storage errors

### Redis

```bash
redis-cli ping
```

Run server:

```bash
python -m agentmesh serve --storage redis --redis-url redis://localhost:6379
```

### PostgreSQL

```bash
psql postgresql://localhost:5432/agentmesh -c "SELECT 1;"
```

Run server:

```bash
python -m agentmesh serve --storage postgres --postgres-url postgresql://localhost:5432/agentmesh
```

## 8. CLI uses wrong endpoint

Check and set config:

```bash
agentmesh config get
agentmesh config set endpoint http://localhost:8000
```

Use one-off override:

```bash
agentmesh --endpoint http://localhost:8000 agents list
```

## 9. SDK connection cleanup warnings

Use async context manager:

```python
async with AgentMeshClient(base_url="http://localhost:8000") as client:
    ...
```

or always call:

```python
await client.close()
```

## 10. Quick contract test

Run built-in tests:

```bash
python -m unittest discover -s tests -v
```
