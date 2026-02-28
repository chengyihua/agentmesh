# AgentMesh Data Models

This document reflects model definitions in `src/agentmesh/core/agent_card.py` and related API request models.

## Enums

### `ProtocolType`

- `a2a`
- `mcp`
- `http`
- `grpc`
- `websocket`
- `custom`

### `HealthStatus`

- `healthy`
- `unhealthy`
- `unknown`

### `PermissionLevel`

- `read`
- `write`
- `execute`
- `admin`

## Skill Models

### `SkillInputOutput`

```json
{
  "type": "object",
  "properties": {"city": {"type": "string"}},
  "required": ["city"],
  "items": null
}
```

Fields:

- `type` (required)
- `properties` (optional)
- `required` (optional)
- `items` (optional)

### `Skill`

Fields:

- `name` (required, 1-100 chars)
- `description` (required, 1-500 chars)
- `input_schema` (optional, `SkillInputOutput`)
- `output_schema` (optional, `SkillInputOutput`)
- `examples` (optional, list of objects)
- `tags` (optional, list of strings)

## Permission Model

### `Permission`

Fields:

- `resource` (required, 1-100 chars)
- `level` (required, `PermissionLevel`)
- `description` (optional)

## Agent Models

### `AgentCard`

Required fields:

- `id`
- `name`
- `version`
- `skills` (min 1)
- `endpoint`

Optional/common fields:

- `description`
- `protocol` (default `a2a`)
- `auth_required`, `auth_method`
- `permissions`
- `max_execution_time`
- `rate_limit`
- `provider`
- `tags`
- `documentation_url`
- `source_code_url`
- `health_status` (default `unknown`)
- `last_health_check`
- `signature`, `public_key`
- `created_at`, `updated_at`

Validation rules:

- `id` allows letters, digits, `_`, `-`
- skill names must be unique in one card

Example:

```json
{
  "id": "weather-bot-001",
  "name": "WeatherBot",
  "version": "1.0.0",
  "description": "Weather forecasting service",
  "skills": [
    {
      "name": "get_weather",
      "description": "Get current weather",
      "input_schema": {
        "type": "object",
        "properties": {"city": {"type": "string"}},
        "required": ["city"]
      }
    }
  ],
  "endpoint": "http://localhost:8001/weather",
  "protocol": "http",
  "tags": ["weather", "api"],
  "health_status": "healthy"
}
```

### `AgentCardUpdate`

Partial update model used by `PUT /agents/{agent_id}`.

Allowed fields:

- `name`
- `description`
- `endpoint`
- `health_status`
- `tags`

Unknown fields are rejected (`extra="forbid"`).

## Auth Request Models

### `TokenRequest`

```json
{
  "agent_id": "weather-bot-001",
  "secret": "agentmesh-dev-secret"
}
```

### `RefreshRequest`

```json
{
  "refresh_token": "..."
}
```

## Health Request Models

### `HeartbeatRequest`

```json
{
  "status": "healthy",
  "timestamp": "2026-02-24T12:00:00Z"
}
```

### `BatchHealthRequest`

```json
{
  "agent_ids": ["agent-1", "agent-2"]
}
```

## Invocation Models

### `InvokeRequest`

Used by `POST /agents/{agent_id}/invoke`.

```json
{
  "skill": "get_weather",
  "payload": {"city": "Tokyo"},
  "path": "/weather",
  "method": "POST",
  "timeout_seconds": 30.0,
  "headers": {"X-Trace-Id": "abc-123"}
}
```

Fields:

- `skill` (optional string)
- `payload` (object, default `{}`)
- `path` (optional string)
- `method` (string, default `POST`)
- `timeout_seconds` (float, >0 and <=300)
- `headers` (optional object)

### `InvocationResult` (response `data.result`)

```json
{
  "protocol": "http",
  "target_url": "http://localhost:8001/weather",
  "status_code": 200,
  "ok": true,
  "latency_ms": 12.34,
  "response": {"temperature": 22},
  "response_headers": {"content-type": "application/json"}
}
```
