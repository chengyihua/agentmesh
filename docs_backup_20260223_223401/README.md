# AgentMesh Documentation

Welcome to the AgentMesh documentation! This repository contains comprehensive documentation for the AgentMesh project - an open-source, secure, and decentralized AI Agent registration and discovery infrastructure.

## 📚 Documentation Structure

### Core Documentation

| Document | Description | Status |
|----------|-------------|--------|
| **[Protocol Specification](protocol/protocol_specification.md)** | Complete technical specification of the AgentMesh protocol | ✅ Complete |
| **[API Reference](protocol/api_reference.md)** | Complete API endpoint documentation | ✅ Complete |
| **[Data Models](protocol/data_models.md)** | All data structures and schemas | ✅ Complete |
| **[Quick Start Guide](protocol/quick_start.md)** | 5-minute getting started guide | ✅ Complete |
| **[Best Practices](protocol/best_practices.md)** | Development and deployment guidelines | ✅ Complete |
| **[Security Guide](protocol/security_guide.md)** | Security considerations and best practices | ✅ Complete |

### Language-Specific Documentation

| Language | Documentation | Status |
|----------|---------------|--------|
| **Python** | [Python SDK Documentation](python/) | 🔄 In Progress |
| **JavaScript/TypeScript** | [JavaScript SDK Documentation](javascript/) | 📅 Planned |
| **Go** | [Go SDK Documentation](go/) | 📅 Planned |

### Chinese Documentation (中文文档)

| 文档 | 描述 | 状态 |
|------|------|------|
| **[协议规范](protocol/zh/protocol_specification_zh.md)** | 完整的 AgentMesh 协议技术规范 | ✅ 完成 |
| **[快速开始指南](protocol/zh/quick_start_zh.md)** | 5分钟上手指南 | ✅ 完成 |
| **[API 参考](protocol/zh/api_reference_zh.md)** | 完整的 API 端点文档 | 🔄 进行中 |
| **[数据模型](protocol/zh/data_models_zh.md)** | 所有数据结构和模式 | 🔄 进行中 |

## 🚀 Getting Started

### Quick Start

1. **Install AgentMesh:**
   ```bash
   pip install agentmesh
   ```

2. **Start the server:**
   ```bash
   agentmesh serve --storage memory --port 8000
   ```

3. **Register your first agent:**
   ```python
   from agentmesh import AgentMeshClient
   from agentmesh.core.agent_card import AgentCard, Skill
   
   client = AgentMeshClient(base_url="http://localhost:8000")
   
   agent = AgentCard(
       id="weather-bot-001",
       name="WeatherBot",
       version="1.0.0",
       description="Weather forecasting service",
       skills=[Skill(name="get_weather", description="Get current weather")],
       endpoint="http://localhost:8001/weather"
   )
   
   await client.register_agent(agent)
   ```

4. **Discover agents:**
   ```python
   agents = await client.discover_agents(skill_name="get_weather")
   for agent in agents:
       print(f"Found: {agent.name} - {agent.description}")
   ```

### Examples

Check out the `examples/` directory for complete examples:

```bash
# Basic example
python examples/basic_example.py

# Authentication example
python examples/auth_example.py

# Multi-agent collaboration
python examples/multi_agent_example.py
```

## 📖 Documentation Guide

### For Developers

1. **Start with** [Quick Start Guide](protocol/quick_start.md) to get up and running
2. **Read** [Protocol Specification](protocol/protocol_specification.md) to understand the protocol
3. **Refer to** [API Reference](protocol/api_reference.md) while developing
4. **Follow** [Best Practices](protocol/best_practices.md) for production deployment
5. **Review** [Security Guide](protocol/security_guide.md) for security considerations

### For Contributors

1. **Understand** the [Architecture](architecture.md) (coming soon)
2. **Review** [Contributing Guidelines](../CONTRIBUTING.md)
3. **Check** [Development Setup](../DEVELOPMENT.md)
4. **Read** [Code of Conduct](../CODE_OF_CONDUCT.md)

### For Users

1. **Install** using the [Installation Guide](installation.md) (coming soon)
2. **Configure** using the [Configuration Guide](configuration.md) (coming soon)
3. **Deploy** following the [Deployment Guide](deployment.md) (coming soon)
4. **Monitor** using the [Monitoring Guide](monitoring.md) (coming soon)

## 🔧 API Documentation

### Interactive API Docs

Once you have the AgentMesh server running, you can access:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

### API Versioning

AgentMesh uses semantic versioning for APIs:

- **v1**: Current stable version
- **v0.x**: Development/experimental versions

All API endpoints are prefixed with `/api/v1/`.

## 🎯 Key Concepts

### AgentCard

The core data structure representing an AI Agent:

```python
{
  "id": "unique-agent-id",
  "name": "Human-readable name",
  "version": "1.0.0",
  "description": "Agent description",
  "skills": [
    {
      "name": "skill_name",
      "description": "What this skill does"
    }
  ],
  "endpoint": "http://agent-service.example.com",
  "protocol": "http",
  "tags": ["tag1", "tag2"],
  "health_status": "healthy"
}
```

### Skills

Capabilities that an agent provides:

- **Name**: Unique identifier for the skill
- **Description**: What the skill does
- **Parameters**: Input parameters (optional)
- **Returns**: Output schema (optional)
- **Examples**: Usage examples (optional)

### Discovery

Find agents based on:
- Skills they provide
- Tags
- Protocol type
- Health status
- Full-text search

## 🔐 Security

### Authentication Methods

1. **API Key**: Simple key-based authentication
2. **JWT Tokens**: Token-based authentication with expiration
3. **OAuth 2.0**: Integration with external providers

### Security Features

- **HTTPS/TLS** support
- **Rate limiting** to prevent abuse
- **Input validation** and sanitization
- **Audit logging** for security monitoring
- **Data encryption** at rest and in transit

## 📊 Monitoring & Observability

### Metrics

AgentMesh provides metrics in Prometheus format:

```bash
# Access metrics endpoint
curl http://localhost:8000/metrics
```

### Health Checks

```bash
# Check server health
curl http://localhost:8000/health

# Check agent health
curl http://localhost:8000/api/v1/agents/{agent_id}/health
```

### Logging

Configure logging levels:

```python
import logging

# Enable debug logging
logging.getLogger("agentmesh").setLevel(logging.DEBUG)
```

## 🚀 Deployment

### Docker

```bash
# Pull the Docker image
docker pull agentmesh/agentmesh:latest

# Run with Docker
docker run -p 8000:8000 agentmesh/agentmesh:latest
```

### Kubernetes

```yaml
# Example Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agentmesh
spec:
  replicas: 3
  selector:
    matchLabels:
      app: agentmesh
  template:
    metadata:
      labels:
        app: agentmesh
    spec:
      containers:
      - name: agentmesh
        image: agentmesh/agentmesh:latest
        ports:
        - containerPort: 8000
```

### Cloud Providers

- **AWS**: ECS, EKS, EC2
- **Google Cloud**: GKE, Cloud Run
- **Azure**: AKS, Container Instances
- **DigitalOcean**: Kubernetes, Droplets

## 🔗 Related Resources

### Official Resources

- **GitHub Repository**: https://github.com/agentmesh/agentmesh
- **PyPI Package**: https://pypi.org/project/agentmesh/
- **Docker Hub**: https://hub.docker.com/r/agentmesh/agentmesh
- **Documentation Site**: https://agentmesh.io/docs (coming soon)

### Community Resources

- **Discord Community**: https://discord.gg/agentmesh (coming soon)
- **Stack Overflow**: https://stackoverflow.com/questions/tagged/agentmesh
- **GitHub Discussions**: https://github.com/agentmesh/agentmesh/discussions

### Tutorials & Examples

- **Blog Posts**: https://blog.agentmesh.io (coming soon)
- **Video Tutorials**: https://youtube.com/@agentmesh (coming soon)
- **Example Projects**: https://github.com/agentmesh/examples

## 🆘 Getting Help

### Documentation Issues

If you find issues with the documentation:

1. **Check** if the issue is already reported in [GitHub Issues](https://github.com/agentmesh/agentmesh/issues)
2. **Create** a new issue with the "documentation" label
3. **Or** submit a pull request with the fix

### Questions & Support

- **GitHub Discussions**: For questions and discussions
- **Discord**: For real-time chat support (coming soon)
- **Email**: support@agentmesh.io

### Reporting Bugs

When reporting bugs, please include:

1. **AgentMesh version**
2. **Python version**
3. **Operating system**
4. **Steps to reproduce**
5. **Expected behavior**
6. **Actual behavior**

### Feature Requests

Feature requests are welcome! Please:

1. **Check** if the feature already exists or is planned
2. **Describe** the use case clearly
3. **Explain** why it's important
4. **Suggest** implementation ideas if possible

## 📄 License

AgentMesh is open-source software licensed under the [MIT License](../LICENSE).

## 🤝 Contributing

We welcome contributions! Please see the [Contributing Guidelines](../CONTRIBUTING.md) for details.

## 📞 Contact

- **Website**: https://agentmesh.io
- **Email**: hello@agentmesh.io
- **Twitter**: @agentmesh (coming soon)
- **GitHub**: https://github.com/agentmesh

---

*Last updated: February 23, 2026*