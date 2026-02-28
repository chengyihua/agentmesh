# AgentMesh Documentation Structure

This file describes the current documentation layout in this repository.

## Directory Layout

```text
docs/
├── README.md
├── DOCUMENTATION_STRUCTURE.md
├── contributing/
│   └── guide.md
├── deployment/
│   └── guide.md
├── protocol/
│   ├── README.md
│   ├── api_reference.md
│   ├── architecture_diagrams.md
│   ├── best_practices.md
│   ├── data_models.md
│   ├── interactive_examples.md
│   ├── protocol_specification.md
│   ├── quick_start.md
│   ├── security_guide.md
│   └── zh/
│       ├── README.md
│       ├── protocol_specification_zh.md
│       └── quick_start_zh.md
├── resources/
│   ├── glossary.md
│   └── troubleshooting.md
├── sdk/
│   └── python.md
└── tutorials/
    └── building_your_first_agent.md
```

## Scope and Source of Truth

- English docs are aligned to current code under:
  - `src/agentmesh/api`
  - `src/agentmesh/core`
  - `src/agentmesh/auth`
  - `src/agentmesh/storage`
  - `src/agentmesh/client.py`
  - `src/agentmesh/cli.py`
- Runtime behavior should be validated against API tests in `tests/`.
- Chinese docs under `docs/protocol/zh/` are maintained separately.

## Reading Order

1. `README.md` (repo root)
2. `docs/README.md`
3. `docs/protocol/quick_start.md`
4. `docs/protocol/api_reference.md`
5. `docs/sdk/python.md`
6. Task-specific guides in `docs/tutorials/`, `docs/deployment/`, and `docs/resources/`
