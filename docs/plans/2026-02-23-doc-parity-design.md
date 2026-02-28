# Strong Doc-Implementation Parity Design

Date: 2026-02-23
Scope: `/README.md`, `/docs/README.md`, `/docs/protocol/api_reference.md`, `/docs/protocol/quick_start.md`, `/docs/protocol/interactive_examples.md`

## Goals

1. Make documented API endpoints actually available.
2. Provide a real SDK (`AgentMeshClient`) matching docs examples.
3. Provide a real CLI command surface used by docs.
4. Keep compatibility with existing paths where practical.

## Architecture

- `AgentRegistry` becomes persistent and app-scoped (single instance), backed by pluggable storage.
- Storage layer provides `MemoryStorage`, `RedisStorage`, `PostgresStorage` with one async interface.
- API routes return a unified response shape: `success/data/message/timestamp`.
- Auth layer adds JWT access token + refresh flow and optional API key guard for protected routes.

## Components

- Core: `core/registry.py`, `core/agent_card.py`, `core/security.py`
- API: `api/server.py`, `api/routes.py`
- Storage: `storage/{base,memory,redis,postgres}.py`
- Auth: `auth/token_manager.py`
- SDK: `client.py`
- CLI: `cli.py`, module entrypoint via `__main__.py`

## Data Flow

1. CLI/SDK sends request to `/api/v1/*`.
2. Router validates auth headers and payload.
3. Router calls app-state singleton `AgentRegistry`.
4. Registry updates in-memory indexes and selected storage backend.
5. Router returns standard response envelope.

## Error Handling

- API errors emit a standard error envelope with structured `error.code/message/details`.
- 4xx for validation/not found/auth failures; 500 for unexpected failures.

## Testing Plan

1. API lifecycle test: register -> get -> discover -> stats -> delete.
2. Search and heartbeat test.
3. Token issue/verify/refresh test.
4. CLI smoke test against in-process server where practical.

## Risks

- Redis/Postgres may not be available in local CI environments; memory remains default.
- Existing demos may rely on older response shapes; update demos or keep compatibility where needed.

## Out of Scope

- Full production clustering and distributed locking.
- Advanced relevance ranking beyond lightweight text scoring.
