# AgentMesh Glossary

## AgentCard

The structured identity/capability record for an agent. It includes fields such as:

- `id`, `name`, `version`
- `skills`
- `endpoint`, `protocol`
- optional tags, auth metadata, and signature fields

## Skill

A named capability inside an `AgentCard`. Each skill has:

- `name`
- `description`
- optional `input_schema` and `output_schema`

## Discovery

Lookup operation for agents via:

- `GET /api/v1/agents/discover`
- filters by `skill`, `protocol`, `tag`/`tags`, `q`, `healthy_only`

## Search

Ranked text retrieval via `GET /api/v1/agents/search?q=...`.

## Heartbeat

Agent liveness update sent to `POST /api/v1/agents/{agent_id}/heartbeat`.

## Health Status

Current state of an agent:

- `healthy`
- `unhealthy`
- `unknown`

## Registry

`AgentRegistry` is the in-process service maintaining:

- in-memory indexes for discovery/search
- metrics per agent
- synchronization with configured storage backend

## Storage Backend

Persistence implementation behind `StorageBackend` interface.

Available backends:

- `MemoryStorage`
- `RedisStorage`
- `PostgresStorage`

## API Key Mode

Optional authorization mode enabled by starting server with `--api-key`. Protected write/admin routes then require API key or valid bearer token.

## Access Token

JWT returned by `POST /api/v1/auth/token`, used with:

```http
Authorization: Bearer <access_token>
```

## Refresh Token

Opaque token returned by `/auth/token`, exchanged at `/auth/refresh` for new access tokens.

## Signature Utilities

Security endpoints for cryptographic operations:

- `/api/v1/security/keypair`
- `/api/v1/security/sign`
- `/api/v1/security/verify`

## Response Envelope

Standard response format used across API routes:

- success path: `success`, `data`, `message`, `timestamp`
- error path: `success`, `error`, `timestamp`
