# AgentMesh Protocol Specification (Current Implementation)

This specification describes the protocol behavior implemented by this repository.

## 1. Transport and Versioning

- Transport: HTTP/JSON
- API prefix: `/api/v1`
- Service endpoints outside API prefix:
  - `/` (service metadata)
  - `/health` (service health)
  - `/version` (service/API version and supported protocols)
  - `/metrics` (Prometheus metrics)

## 2. Core Responsibilities

AgentMesh provides:

- Agent registration and updates
- Agent discovery and text search
- Protocol-based agent invocation gateway
- Agent heartbeat and health checks
- System and per-agent stats
- Optional API key protection for write/admin routes
- Token issuance/refresh/verification endpoints
- Agent card signing and signature verification utilities

## 3. Response Contract

### Success envelope

```json
{
  "success": true,
  "data": {},
  "message": "Operation successful",
  "timestamp": "<ISO-8601 UTC>"
}
```

### Error envelope

```json
{
  "success": false,
  "error": {
    "code": "<http-status-or-code>",
    "message": "<summary>",
    "details": {}
  },
  "timestamp": "<ISO-8601 UTC>"
}
```

## 4. Agent Lifecycle Protocol

- Register: `POST /api/v1/agents/register` (alias: `POST /api/v1/agents`)
- Read: `GET /api/v1/agents/{agent_id}`
- List: `GET /api/v1/agents`
- Update: `PUT /api/v1/agents/{agent_id}`
- Delete: `DELETE /api/v1/agents/{agent_id}`

Validation highlights:

- `skills` must contain at least one item.
- `endpoint` is required.
- Agent IDs must be unique.
- Optional signature is verified when present.

## 5. Discovery and Search Protocol

- Discovery:
  - `GET /api/v1/agents/discover`
  - `GET /api/v1/discover` (alias)
- Search:
  - `GET /api/v1/agents/search?q=<text>`

Discovery filters:

- `skill` or `skill_name`
- `protocol`
- `tag`/`tags`
- `q`
- `healthy_only`
- `limit`, `offset`

Search returns ranked results with score and matched fields.

## 6. Health and Metrics Protocol

- Heartbeat: `POST /api/v1/agents/{agent_id}/heartbeat`
- Agent health: `GET /api/v1/agents/{agent_id}/health`
- Batch health:
  - `POST /api/v1/agents/health/check`
  - `POST /api/v1/agents/batch/health-check` (alias)
- Agent stats: `GET /api/v1/agents/{agent_id}/stats`
- System stats: `GET /api/v1/stats`

Behavior:

- Heartbeat updates `health_status`, `last_health_check`, and `updated_at`.
- Health checks can mark stale agents unhealthy based on server thresholds.

## 7. Authentication and Authorization Protocol

Token endpoints:

- `POST /api/v1/auth/token`
- `POST /api/v1/auth/refresh`
- `GET /api/v1/auth/verify`

Token issuance requires `agent_id` and `secret`.

Authorization model:

- If server is started without `--api-key`, protected routes are open.
- If started with `--api-key`, protected routes require matching `X-API-Key` or a valid bearer token.

## 8. Signature Utilities

- Generate key pair: `POST /api/v1/security/keypair?algorithm=ed25519|rsa`
- Sign agent card: `POST /api/v1/security/sign`
- Verify signature: `POST /api/v1/security/verify`

## 9. Protocol Invocation Gateway

- Invoke endpoint: `POST /api/v1/agents/{agent_id}/invoke`
- Request fields:
  - `skill` (optional)
  - `payload` (object)
  - `path` (optional URL path override)
  - `method` (default `POST`)
  - `timeout_seconds`
  - `headers` (optional)

Invocation implementation coverage:

- implemented: `http`, `custom`, `a2a`, `mcp`, `grpc`, `websocket`

## 10. Storage and Consistency Model

Supported backends:

- Memory (default)
- Redis
- PostgreSQL

Registry behavior:

- In-memory indexes power discovery/search performance.
- On startup, registry loads agents from configured storage.
- Storage is updated on register/update/delete/heartbeat.
- Registry periodically refreshes in-memory indexes from persistent storage for cross-instance convergence.

## 11. Rate Limits

Route limits currently configured:

- Register/update/delete: `60/minute`
- Heartbeat: `120/minute`
- Invoke: `120/minute`
