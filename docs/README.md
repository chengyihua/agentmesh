# AgentMesh Documentation

This documentation is aligned with the implementation in this repository.

## Start Here

- [Protocol Quick Start](protocol/quick_start.md)
- [API Reference](protocol/api_reference.md)
- [Python SDK](sdk/python.md)
- [Interactive Examples](protocol/interactive_examples.md)

## Protocol Docs

- [Protocol Specification](protocol/protocol_specification.md)
- [Data Models](protocol/data_models.md)
- [Security Guide](protocol/security_guide.md)
- [Best Practices](protocol/best_practices.md)
- [Architecture Diagrams](protocol/architecture_diagrams.md)

## Operational Docs

- [Deployment Guide](deployment/guide.md)
- [Troubleshooting](resources/troubleshooting.md)
- [Glossary](resources/glossary.md)
- [Contributing Guide](contributing/guide.md)

## 5-Minute Run

```bash
pip install agentmesh-python
# or from source
pip install -e .
python -m agentmesh serve --storage memory --port 8000
```

Register an agent:

```bash
curl -X POST http://localhost:8000/api/v1/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "id": "hello-agent-001",
    "name": "HelloAgent",
    "version": "1.0.0",
    "skills": [{"name": "hello", "description": "Say hello"}],
    "endpoint": "http://localhost:9000",
    "protocol": "http",
    "health_status": "healthy"
  }'
```

Discover agents:

```bash
curl "http://localhost:8000/api/v1/agents/discover?skill=hello"
```

## Validation Command

```bash
python -m unittest discover -s tests -v
```
