# AgentMesh API Reference

## Base URLs

- API base: `http://localhost:8000/api/v1`
- Service endpoints outside API base:
  - `GET /`
  - `GET /health`
  - `GET /version`
  - `GET /metrics`

## Response Envelope

Success:

```json
{
  "success": true,
  "data": {},
  "message": "Operation successful",
  "timestamp": "2026-02-23T18:00:00Z"
}
```

Error:

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

## Authentication

Authentication is optional by default.

When server starts with `--api-key <value>`, the following endpoints require either:

- `X-API-Key: <value>`, or
- `Authorization: Bearer <access_token>` (issued by `/auth/token`)

Protected endpoints:

- `POST /agents/register`
- `POST /agents`
- `PUT /agents/{agent_id}`
- `DELETE /agents/{agent_id}`
- `POST /agents/{agent_id}/invoke`
- `POST /cache/clear`

## Endpoints

### Agent registration and lifecycle

- `POST /agents/register`
- `POST /agents` (alias)
- `GET /agents?skip=0&limit=100`
- `GET /agents/{agent_id}`
- `PUT /agents/{agent_id}`
- `DELETE /agents/{agent_id}`

Register request body accepts either raw `AgentCard` or wrapped payload:

```json
{
  "id": "weather-bot-001",
  "name": "WeatherBot",
  "version": "1.0.0",
  "skills": [{"name": "get_weather", "description": "Get weather"}],
  "endpoint": "http://localhost:8001/weather",
  "protocol": "http",
  "health_status": "healthy"
}
```

or

```json
{
  "agent_card": {
    "id": "weather-bot-001",
    "name": "WeatherBot",
    "version": "1.0.0",
    "skills": [{"name": "get_weather", "description": "Get weather"}],
    "endpoint": "http://localhost:8001/weather",
    "protocol": "http"
  }
}
```

### Discovery and search

- `GET /agents/discover`
- `GET /discover` (alias)
- `GET /agents/search?q=weather`

`/agents/discover` query parameters:

- `skill` or `skill_name`
- `protocol`
- `tags` (repeatable)
- `tag` (repeatable)
- `q`
- `healthy_only` (default `true`)
- `limit` (1-1000, default `20`)
- `offset` (default `0`)

### Health and stats

- `POST /agents/{agent_id}/heartbeat`
- `GET /agents/{agent_id}/health`
- `GET /agents/{agent_id}/stats`
- `POST /agents/health/check`
- `POST /agents/batch/health-check` (alias)
- `GET /stats`

`GET /stats` includes:

- `storage_sync_enabled`
- `storage_sync_interval_seconds`

Batch health request:

```json
{
  "agent_ids": ["agent-1", "agent-2"]
}
```

### Invocation gateway

- `POST /agents/{agent_id}/invoke`

Request body:

```json
{
  "skill": "get_weather",
  "payload": {"city": "Tokyo"},
  "path": "/weather",
  "method": "POST",
  "timeout_seconds": 30,
  "headers": {"X-Trace-Id": "abc-123"}
}
```

Response data includes:

- `result.protocol`
- `result.target_url`
- `result.status_code`
- `result.ok`
- `result.latency_ms`
- `result.response`

Protocol support in invocation:

- implemented: `http`, `custom`, `a2a`, `mcp`, `grpc`, `websocket`

Protocol-specific notes:

- `grpc`: provide `path` as full RPC method name, e.g. `/package.Service/Method`.
- `websocket`: gateway sends one JSON message and waits for one response message.
- `grpc` bridge requires `grpcio` package at runtime.
- `websocket` bridge requires `websockets` package at runtime.

### Auth

- `POST /auth/token`
- `POST /auth/refresh`
- `GET /auth/verify`

Issue token request:

```json
{
  "agent_id": "weather-bot-001",
  "secret": "agentmesh-dev-secret"
}
```

Refresh token request:

```json
{
  "refresh_token": "..."
}
```

Verify token requires bearer header:

```http
Authorization: Bearer <access_token>
```

### Security utilities

- `POST /security/keypair?algorithm=ed25519`
- `POST /security/sign`
- `POST /security/verify`

Sign request:

```json
{
  "agent_card": {"id": "a", "name": "A", "version": "1.0.0", "skills": [{"name": "x", "description": "x"}], "endpoint": "http://localhost:8001", "protocol": "http"},
  "private_key": "..."
}
```

Verify request:

```json
{
  "agent_card": {"id": "a", "name": "A", "version": "1.0.0", "skills": [{"name": "x", "description": "x"}], "endpoint": "http://localhost:8001", "protocol": "http", "signature": "...", "public_key": "..."}
}
```

### Cache

- `POST /cache/clear`

Returns number of cleared cached searches.

## Rate Limits

- `POST /agents/register`, `POST /agents`, `PUT /agents/{agent_id}`, `DELETE /agents/{agent_id}`: `60/minute`
- `POST /agents/{agent_id}/heartbeat`: `120/minute`
- `POST /agents/{agent_id}/invoke`: `120/minute`
