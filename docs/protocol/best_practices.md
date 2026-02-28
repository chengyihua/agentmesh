# AgentMesh Best Practices

## Registration

1. Keep agent IDs stable and unique.
2. Include at least one skill and a reachable endpoint.
3. Re-register only when identity changes; use update for metadata changes.

## Discovery

1. Prefer exact filters (`skill`, `tag`, `protocol`) before broad `q` search.
2. Keep tags normalized (lowercase, singular naming).
3. Use pagination (`limit`, `offset`) for large result sets.

## Health

1. Send heartbeat regularly (`POST /agents/{id}/heartbeat`).
2. Use `status` values `healthy|unhealthy|unknown` consistently.
3. Track `last_health_check` in your operational dashboards.

## Auth and Access

1. In production, start server with both `--api-key` and non-default `--auth-secret`.
2. Use bearer tokens for automation; keep API key for controlled admin clients.
3. Rotate API keys and secrets periodically.

## SDK Usage

1. Prefer `async with AgentMeshClient(...)` to guarantee connection cleanup.
2. Use `SyncAgentMeshClient` only for scripts/CLI-style sync workflows.
3. Handle `httpx.HTTPStatusError` and inspect returned error envelope.

## Protocol Invocation

1. Use `POST /agents/{id}/invoke` for unified protocol dispatch.
2. For `http/custom`, pass explicit `path` and `method` when endpoint root is not callable.
3. For `a2a/mcp`, keep payload schema stable and versioned in your agent implementation.
4. For `grpc`, pass full RPC method path (e.g. `/package.Service/Method`) and explicit timeout.
5. For `websocket`, design your endpoint for one request message and one response message.

## Storage

1. Use memory storage only for local development and tests.
2. Use Redis for simple persistent deployments.
3. Use PostgreSQL when you need transactional persistence and queryability.

## Operational

1. Monitor `/health`, `/version`, `/metrics`, and `/api/v1/stats`.
2. Alert on rising `unhealthy_agents` or repeated `401/429` responses.
3. Keep docs and examples aligned with `src/agentmesh` before each release.
