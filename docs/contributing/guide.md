# Contributing Guide

This guide is aligned with the current repository structure and toolchain.

## 1. Development setup

```bash
git clone <your-fork-or-local-clone>
cd agentmesh
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

## 2. Run tests

Core test command currently used in this repo:

```bash
python -m unittest discover -s tests -v
```

Optional pytest (requires dev deps):

```bash
python -m pytest -q
```

## 3. Run server locally

```bash
python -m agentmesh serve --storage memory --port 8000
```

## 4. Project layout

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

## 5. Coding expectations

1. Preserve API response envelope format.
2. Keep docs synced with implemented routes and SDK methods.
3. Add/update tests for behavior changes.
4. Keep storage backends behind `StorageBackend` interface.
5. Keep protocol handlers consistent with `/agents/{id}/invoke` contract.

## 6. Doc parity checklist (required for API/SDK changes)

When changing public behavior, update:

- `README.md`
- `docs/protocol/api_reference.md`
- `docs/protocol/quick_start.md`
- `docs/protocol/interactive_examples.md`
- `docs/sdk/python.md`

## 7. Suggested PR checklist

1. Tests pass locally.
2. New/changed behavior has test coverage.
3. Public docs updated.
4. Backward compatibility impact documented.
