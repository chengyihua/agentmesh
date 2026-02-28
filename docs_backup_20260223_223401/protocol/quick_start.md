# AgentMesh Quick Start Guide

Get started with AgentMesh in 5 minutes!

## 🚀 Installation

### Install from PyPI

```bash
pip install agentmesh
```

### Install from source

```bash
git clone https://github.com/agentmesh/agentmesh.git
cd agentmesh
pip install -e .
```

## 📦 Basic Usage

### 1. Start the AgentMesh Server

```bash
# Start with memory storage (development)
agentmesh serve --storage memory --port 8000

# Start with Redis storage (production)
agentmesh serve --storage redis --redis-url redis://localhost:6379 --port 8000
```

### 2. Register Your First Agent

```python
import asyncio
from agentmesh import AgentMeshClient
from agentmesh.core.agent_card import AgentCard, Skill, ProtocolType, HealthStatus

async def register_agent():
    # Create client
    client = AgentMeshClient(base_url="http://localhost:8000")
    
    # Create agent card
    agent = AgentCard(
        id="weather-bot-001",
        name="WeatherBot",
        version="1.0.0",
        description="Weather forecasting service",
        skills=[
            Skill(name="get_weather", description="Get current weather"),
            Skill(name="get_forecast", description="Get weather forecast")
        ],
        endpoint="http://localhost:8001/weather",
        protocol=ProtocolType.HTTP,
        tags=["weather", "forecast", "api"],
        health_status=HealthStatus.HEALTHY
    )
    
    # Register agent
    response = await client.register_agent(agent)
    print(f"Agent registered: {response['agent_id']}")
    
    # Send heartbeat
    await client.send_heartbeat("weather-bot-001")

# Run
asyncio.run(register_agent())
```

### 3. Discover Agents

```python
import asyncio
from agentmesh import AgentMeshClient

async def discover_agents():
    client = AgentMeshClient(base_url="http://localhost:8000")
    
    # Discover by skill
    agents = await client.discover_agents(skill_name="get_weather")
    print(f"Found {len(agents)} agents with weather skill:")
    for agent in agents:
        print(f"  - {agent.name}: {agent.description}")
    
    # Discover by tags
    agents = await client.discover_agents(tags=["api"])
    print(f"Found {len(agents)} agents with API tag")

asyncio.run(discover_agents())
```

### 4. Call an Agent Service

```python
import asyncio
import aiohttp
from agentmesh import AgentMeshClient

async def call_agent_service():
    client = AgentMeshClient(base_url="http://localhost:8000")
    
    # Find a weather agent
    agents = await client.discover_agents(skill_name="get_weather")
    if not agents:
        print("No weather agents found")
        return
    
    weather_agent = agents[0]
    
    # Call the agent's service
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{weather_agent.endpoint}/current?city=Beijing"
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"Weather in Beijing: {data}")
            else:
                print(f"Failed to get weather: {response.status}")

asyncio.run(call_agent_service())
```

## 🔧 Advanced Usage

### Using Authentication

```python
from agentmesh import AgentMeshClient

# Create authenticated client
client = AgentMeshClient(
    base_url="http://localhost:8000",
    api_key="your-api-key"
)

# Or use token authentication
client = AgentMeshClient(
    base_url="http://localhost:8000",
    token="your-bearer-token"
)
```

### Custom Storage Backend

```python
from agentmesh import AgentMeshServer
from agentmesh.storage import RedisStorage

# Create custom storage
storage = RedisStorage(
    url="redis://localhost:6379",
    prefix="agentmesh:"
)

# Start server with custom storage
server = AgentMeshServer(storage=storage)
server.run(port=8000)
```

### Health Check Configuration

```python
from agentmesh import AgentMeshClient

client = AgentMeshClient(
    base_url="http://localhost:8000",
    health_check_interval=60,  # Check every 60 seconds
    health_check_timeout=10    # Timeout after 10 seconds
)

# Manually check agent health
health = await client.check_agent_health("weather-bot-001")
print(f"Agent health: {health}")
```

## 📚 Examples

Check the `examples/` directory for more complete examples:

```bash
# Run the basic example
python examples/basic_example.py

# Run the authentication example
python examples/auth_example.py

# Run the multi-agent example
python examples/multi_agent_example.py
```

## 🔍 Monitoring

### Check Server Status

```bash
# Check server health
curl http://localhost:8000/health

# Get server statistics
curl http://localhost:8000/api/v1/stats
```

### View Registered Agents

```bash
# List all agents
curl http://localhost:8000/api/v1/agents

# Get agent details
curl http://localhost:8000/api/v1/agents/weather-bot-001
```

## 🐛 Troubleshooting

### Common Issues

1. **Connection refused**
   ```bash
   # Make sure server is running
   agentmesh serve --storage memory --port 8000
   ```

2. **Agent not found**
   ```bash
   # Check if agent is registered
   curl http://localhost:8000/api/v1/agents/weather-bot-001
   ```

3. **Authentication failed**
   ```python
   # Check your API key or token
   client = AgentMeshClient(base_url="...", api_key="correct-key")
   ```

### Enable Debug Logging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Or for specific modules
logging.getLogger("agentmesh").setLevel(logging.DEBUG)
```

## 📖 Next Steps

1. Read the [Protocol Specification](protocol_specification.md) for details
2. Check the [API Reference](api_reference.md) for all available endpoints
3. Explore [Best Practices](best_practices.md) for production deployment
4. Join the [Community](https://github.com/agentmesh/agentmesh/discussions) for help and discussions

## 🆘 Need Help?

- [GitHub Issues](https://github.com/agentmesh/agentmesh/issues) - Report bugs or request features
- [Documentation](https://agentmesh.io/docs) - Complete documentation
- [Discord](https://discord.gg/agentmesh) - Community support (coming soon)