# AgentMesh Interactive Examples

Interactive API examples that you can try directly from your browser or terminal.

## 🚀 Quick Start Examples

### 1. Register Your First Agent

**Try it in your terminal:**
```bash
# Start AgentMesh server
agentmesh serve --storage memory --port 8000

# In another terminal, register an agent
curl -X POST http://localhost:8000/api/v1/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_card": {
      "id": "weather-bot-001",
      "name": "WeatherBot",
      "version": "1.0.0",
      "description": "Weather forecasting service",
      "skills": [
        {
          "name": "get_weather",
          "description": "Get current weather for a location"
        }
      ],
      "endpoint": "http://localhost:8001/weather",
      "protocol": "http",
      "tags": ["weather", "forecast", "api"]
    }
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "agent_id": "weather-bot-001",
    "registered_at": "2026-02-23T21:00:00Z"
  },
  "message": "Agent registered successfully",
  "timestamp": "2026-02-23T21:00:00Z"
}
```

### 2. Discover Available Agents

**Find agents with specific skills:**
```bash
curl "http://localhost:8000/api/v1/agents/discover?skill=get_weather"
```

**Find agents by tags:**
```bash
curl "http://localhost:8000/api/v1/agents/discover?tag=weather&tag=api"
```

**Full-text search:**
```bash
curl "http://localhost:8000/api/v1/agents/discover?q=weather+forecast"
```

### 3. Check Agent Health

```bash
curl "http://localhost:8000/api/v1/agents/weather-bot-001/health"
```

## 🐍 Python Examples

### Basic Client Usage

```python
import asyncio
from agentmesh import AgentMeshClient
from agentmesh.core.agent_card import AgentCard, Skill

async def main():
    # Create client
    client = AgentMeshClient(base_url="http://localhost:8000")
    
    # Create an agent
    agent = AgentCard(
        id="translation-bot-001",
        name="TranslationBot",
        version="1.0.0",
        description="Multi-language translation service",
        skills=[
            Skill(
                name="translate_text",
                description="Translate text between languages",
                parameters=[
                    {
                        "name": "text",
                        "type": "string",
                        "required": True,
                        "description": "Text to translate"
                    },
                    {
                        "name": "target_language",
                        "type": "string",
                        "required": True,
                        "description": "Target language code"
                    }
                ]
            )
        ],
        endpoint="http://localhost:8002/translate",
        protocol="http",
        tags=["translation", "nlp", "multilingual"]
    )
    
    # Register agent
    response = await client.register_agent(agent)
    print(f"Registered: {response['data']['agent_id']}")
    
    # Discover agents
    agents = await client.discover_agents(skill_name="translate_text")
    print(f"Found {len(agents)} translation agents")
    
    # Get agent details
    agent_details = await client.get_agent("translation-bot-001")
    print(f"Agent: {agent_details.name} - {agent_details.description}")

# Run the example
if __name__ == "__main__":
    asyncio.run(main())
```

### Advanced: Multi-Agent Collaboration

```python
import asyncio
from agentmesh import AgentMeshClient
from agentmesh.core.agent_card import AgentCard, Skill

class MultiAgentSystem:
    def __init__(self, base_url="http://localhost:8000"):
        self.client = AgentMeshClient(base_url=base_url)
        self.agents = {}
    
    async def register_agents(self):
        """Register multiple specialized agents."""
        agents_data = [
            {
                "id": "weather-bot-001",
                "name": "WeatherBot",
                "skills": ["get_weather", "get_forecast"],
                "tags": ["weather", "api"]
            },
            {
                "id": "translation-bot-001",
                "name": "TranslationBot",
                "skills": ["translate_text"],
                "tags": ["translation", "nlp"]
            },
            {
                "id": "sentiment-bot-001",
                "name": "SentimentBot",
                "skills": ["analyze_sentiment"],
                "tags": ["nlp", "sentiment"]
            }
        ]
        
        for agent_data in agents_data:
            agent = AgentCard(
                id=agent_data["id"],
                name=agent_data["name"],
                version="1.0.0",
                description=f"{agent_data['name']} service",
                skills=[Skill(name=skill, description=f"{skill} capability") 
                       for skill in agent_data["skills"]],
                endpoint=f"http://localhost:8000/{agent_data['id']}",
                protocol="http",
                tags=agent_data["tags"]
            )
            
            await self.client.register_agent(agent)
            self.agents[agent_data["id"]] = agent
            print(f"Registered: {agent_data['name']}")
    
    async def collaborative_task(self, task_description):
        """Execute a task using multiple agents."""
        print(f"\nExecuting task: {task_description}")
        
        # Step 1: Find relevant agents
        relevant_agents = []
        
        if "weather" in task_description.lower():
            weather_agents = await self.client.discover_agents(tag="weather")
            relevant_agents.extend(weather_agents)
        
        if "translate" in task_description.lower():
            translation_agents = await self.client.discover_agents(tag="translation")
            relevant_agents.extend(translation_agents)
        
        if "sentiment" in task_description.lower():
            sentiment_agents = await self.client.discover_agents(tag="sentiment")
            relevant_agents.extend(sentiment_agents)
        
        # Step 2: Execute task with relevant agents
        results = []
        for agent in relevant_agents:
            print(f"  Using: {agent.name}")
            # In a real scenario, you would call the agent's endpoint here
            result = f"Result from {agent.name}"
            results.append(result)
        
        return results

async def main():
    system = MultiAgentSystem()
    
    # Register agents
    await system.register_agents()
    
    # Execute collaborative tasks
    tasks = [
        "Get weather in Tokyo and translate to Spanish",
        "Analyze sentiment of customer reviews",
        "Translate weather forecast and analyze sentiment"
    ]
    
    for task in tasks:
        results = await system.collaborative_task(task)
        print(f"Results: {results}\n")

if __name__ == "__main__":
    asyncio.run(main())
```

## 🌐 Web Examples

### HTML/JavaScript Client

```html
<!DOCTYPE html>
<html>
<head>
    <title>AgentMesh Web Client</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .container { background: #f5f5f5; padding: 20px; border-radius: 8px; }
        input, textarea, button { width: 100%; padding: 10px; margin: 10px 0; }
        .result { background: white; padding: 15px; border-radius: 5px; margin: 10px 0; }
        .agent { border: 1px solid #ddd; padding: 10px; margin: 5px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>AgentMesh Web Client</h1>
        
        <div>
            <h2>Discover Agents</h2>
            <input type="text" id="searchQuery" placeholder="Search by skill or tag...">
            <button onclick="discoverAgents()">Search</button>
            <div id="discoveryResults"></div>
        </div>
        
        <div>
            <h2>Register New Agent</h2>
            <input type="text" id="agentName" placeholder="Agent Name">
            <input type="text" id="agentSkills" placeholder="Skills (comma separated)">
            <textarea id="agentDescription" placeholder="Description"></textarea>
            <button onclick="registerAgent()">Register Agent</button>
            <div id="registrationResult"></div>
        </div>
    </div>

    <script>
        const API_BASE = 'http://localhost:8000/api/v1';
        
        async function discoverAgents() {
            const query = document.getElementById('searchQuery').value;
            const resultsDiv = document.getElementById('discoveryResults');
            resultsDiv.innerHTML = '<p>Searching...</p>';
            
            try {
                const response = await fetch(`${API_BASE}/agents/discover?q=${encodeURIComponent(query)}`);
                const data = await response.json();
                
                if (data.success) {
                    let html = `<h3>Found ${data.data.agents.length} agents:</h3>`;
                    data.data.agents.forEach(agent => {
                        html += `
                            <div class="agent">
                                <strong>${agent.name}</strong> (${agent.id})<br>
                                ${agent.description}<br>
                                <small>Skills: ${agent.skills.map(s => s.name).join(', ')}</small><br>
                                <small>Tags: ${agent.tags.join(', ')}</small>
                            </div>
                        `;
                    });
                    resultsDiv.innerHTML = html;
                } else {
                    resultsDiv.innerHTML = `<p class="error">Error: ${data.message}</p>`;
                }
            } catch (error) {
                resultsDiv.innerHTML = `<p class="error">Error: ${error.message}</p>`;
            }
        }
        
        async function registerAgent() {
            const name = document.getElementById('agentName').value;
            const skills = document.getElementById('agentSkills').value.split(',').map(s => s.trim());
            const description = document.getElementById('agentDescription').value;
            const resultDiv = document.getElementById('registrationResult');
            
            const agentData = {
                agent_card: {
                    id: `web-agent-${Date.now()}`,
                    name: name,
                    version: "1.0.0",
                    description: description,
                    skills: skills.map(skill => ({
                        name: skill,
                        description: `${skill} capability`
                    })),
                    endpoint: "http://localhost:8080/web-agent",
                    protocol: "http",
                    tags: ["web", "demo"]
                }
            };
            
            try {
                const response = await fetch(`${API_BASE}/agents/register`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(agentData)
                });
                
                const data = await response.json();
                
                if (data.success) {
                    resultDiv.innerHTML = `
                        <div class="result success">
                            <strong>Success!</strong><br>
                            Agent ID: ${data.data.agent_id}<br>
                            Registered at: ${new Date(data.data.registered_at).toLocaleString()}
                        </div>
                    `;
                } else {
                    resultDiv.innerHTML = `<div class="result error">Error: ${data.message}</div>`;
                }
            } catch (error) {
                resultDiv.innerHTML = `<div class="result error">Error: ${error.message}</div>`;
            }
        }
    </script>
</body>
</html>
```

## 📱 CLI Tool Examples

### Using the AgentMesh CLI

```bash
# Install the CLI
pip install agentmesh-cli

# Configure the CLI
agentmesh config set endpoint http://localhost:8000
agentmesh config set api-key your-api-key

# Register an agent
agentmesh agents register \
  --id "cli-agent-001" \
  --name "CLIAgent" \
  --description "Command line interface agent" \
  --skill "execute_command" \
  --skill "file_operations" \
  --tag "cli" \
  --tag "automation"

# List all agents
agentmesh agents list

# Search for agents
agentmesh agents search --skill "execute_command"

# Get agent details
agentmesh agents get cli-agent-001

# Update agent
agentmesh agents update cli-agent-001 --description "Updated description"

# Delete agent
agentmesh agents delete cli-agent-001
```

### Custom CLI Script

```python
#!/usr/bin/env python3
"""
Custom AgentMesh CLI tool
"""

import click
import requests
import json
from tabulate import tabulate

API_BASE = "http://localhost:8000/api/v1"

@click.group()
def cli():
    """AgentMesh Command Line Interface"""
    pass

@cli.command()
@click.option('--skill', help='Filter by skill')
@click.option('--tag', help='Filter by tag')
@click.option('--query', help='Full-text search query')
def discover(skill, tag, query):
    """Discover available agents"""
    params = {}
    if skill:
        params['skill'] = skill
    if tag:
        params['tag'] = tag
    if query:
        params['q'] = query
    
    response = requests.get(f"{API_BASE}/agents/discover", params=params)
    data = response.json()
    
    if data['success']:
        agents = data['data']['agents']
        if agents:
            table_data = []
            for agent in agents:
                table_data.append([
                    agent['id'],
                    agent['name'],
                    ', '.join([s['name'] for s in agent['skills']]),
                    agent['health_status'],
                    agent.get('last_seen', 'N/A')
                ])
            
            headers = ['ID', 'Name', 'Skills', 'Status', 'Last Seen']
            print(tabulate(table_data, headers=headers, tablefmt='grid'))
        else:
            print("No agents found")
    else:
        print(f"Error: {data['message']}")

@cli.command()
@click.argument('agent_id')
def health(agent_id):
    """Check agent health"""
    response = requests.get(f"{API_BASE}/agents/{agent_id}/health")
    data = response.json()
    
    if data['success']:
        health_data = data['data']
        print(f"Agent: {health_data['agent_id']}")
        print(f"Status: {health_data['health_status']}")
        print(f"Last Heartbeat: {health_data['last_heartbeat']}")
        print(f"Uptime: {health_data.get('uptime', 'N/A')}")
    else:
        print(f"Error: {data['message']}")

@cli.command()
def stats():
    """Get system statistics"""
    response = requests.get(f"{API_BASE}/stats")
    data = response.json()
    
    if data['success']:
        stats_data = data['data']
        print("=== System Statistics ===")
        print(f"Total Agents: {stats_data['total_agents']}")
        print(f"Healthy Agents: {stats_data['healthy_agents']}")
        print(f"Unhealthy Agents: {stats_data['unhealthy_agents']}")
        print(f"Total Skills: {stats_data['total_skills']}")
        print(f"System Uptime: {stats_data['uptime']}")
        print(f"Requests/Minute: {stats_data['requests_per_minute']}")
    else:
        print(f"Error: {data['message']}")

if __name__ == '__main__':
    cli()
```

## 🔧 Docker Examples

### Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  agentmesh:
    image: agentmesh/agentmesh:latest
    ports:
      - "8000:8000"
    environment:
      - STORAGE_BACKEND=redis
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/agentmesh
      - JWT_SECRET=your-secret-key-here
    depends_on:
      - redis
      - postgres
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=agentmesh
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  pgadmin:
    image: dpage/pgadmin4
    environment:
      - PGADMIN_DEFAULT_EMAIL=admin@agentmesh.io
      - PGADMIN_DEFAULT_PASSWORD=admin
    ports:
      - "5050:80"
    depends_on:
      - postgres

volumes:
  redis_data:
  postgres_data:
```

### Docker Run Commands

```bash
# Run AgentMesh with Redis
docker run -d \
  --name agentmesh \
  -p 8000:8000 \
  -e STORAGE_BACKEND=redis \
  -e REDIS_URL=redis://host.docker.internal:6379 \
  agentmesh/agentmesh:latest

# Run with PostgreSQL
docker run -d \
  --name agentmesh \
  -p 8000:8000 \
  -e STORAGE_BACKEND=postgres \
  -e DATABASE_URL=postgresql://user:pass@host.docker.internal:5432/agentmesh \
  agentmesh/agentmesh:latest

# Run with custom config
docker run -d \
  --name agentmesh \
  -p 8000:8000 \
  -v $(pwd)/config:/app/config \
  agentmesh/agentmesh:latest
```

## 🧪 Testing Examples

### Unit Tests

```python
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from agentmesh.core.agent_card import AgentCard, Skill
from agentmesh.registry import AgentRegistry

@pytest.fixture
def mock_storage():
    storage = AsyncMock()
    storage.save_agent = AsyncMock(return_value=True)
    storage.get_agent = AsyncMock(return_value=None)
    return storage

@pytest.fixture
def registry(mock_storage):
    return AgentRegistry(storage=mock_storage)

@pytest.mark.asyncio
async def test_register_agent(registry, mock_storage):
    """Test agent registration."""
    agent = AgentCard(
        id="test-agent",
        name="TestAgent",
        version="1.0.0",
        description="Test agent",
        skills=[Skill(name="test", description="Test skill")],
        endpoint="http://localhost:8000"
    )
    
    result = await registry.register_agent(agent)
    
    assert result["success"] == True
    assert result["data"]["agent_id"] == "test-agent"
    mock_storage.save_agent.assert_called_once_with(agent)

@pytest.mark.asyncio
async def test_discover_agents(registry, mock_storage):
    """Test agent discovery."""
    # Mock storage to return some agents
    mock_agents = [
        AgentCard(
            id="agent-1",
            name="Agent1",
            version="1.0.0",
            description="First agent",
            skills=[Skill(name="skill1", description="Skill 1")],
            endpoint="http://localhost:8001"
        ),
        AgentCard(
            id="agent-2",
            name="Agent2",
            version="1.0.0",
            description="Second agent",
            skills=[Skill(name="skill2", description="Skill 2")],
            endpoint="http://localhost:8002"
        )
    ]
    
    mock_storage.search_agents = AsyncMock(return_value=mock_agents)
    
    agents = await registry.discover_agents(skill_name="skill1")
    
    assert len(agents) == 1
    assert agents[0].id == "agent-1"
```

### Integration Tests

```python
import pytest
import httpx
import asyncio
from agentmesh import AgentMeshServer
from agentmesh.core.agent_card import AgentCard, Skill

@pytest.fixture
async def test_server():
    """Create a test server instance."""
    server = AgentMeshServer(storage="memory")
    await server.start()
    yield server
    await server.stop()

@pytest.fixture
async def test_client(test_server):
    """Create a test HTTP client."""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        yield client

@pytest.mark.asyncio
async def test_agent_registration_integration(test_client):
    """Test agent registration through the API."""
    agent_data = {
        "agent_card": {
            "id": "integration-test-agent",
            "name": "IntegrationTestAgent",
            "version": "1.0.0",
            "description": "Agent for integration testing",
            "skills": [
                {
                    "name": "integration_test",
                    "description": "Integration testing capability"
                }
            ],
            "endpoint": "http://localhost:9999/test",
            "protocol": "http",
            "tags": ["test", "integration"]
        }
    }
    
    response = await test_client.post("/api/v1/agents/register", json=agent_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["success"] == True
    assert data["data"]["agent_id"] == "integration-test-agent"

@pytest.mark.asyncio
async def test_agent_discovery_integration(test_client):
    """Test agent discovery through the API."""
    # First register an agent
    agent_data = {
        "agent_card": {
            "id": "discovery-test-agent",
            "name": "DiscoveryTestAgent",
            "version": "1.0.0",
            "description": "Agent for discovery testing",
            "skills": [{"name": "discovery_test", "description": "Test"}],
            "endpoint": "http://localhost:9999/discovery",
            "protocol": "http",
            "tags": ["test", "discovery"]
        }
    }
    
    await test_client.post("/api/v1/agents/register", json=agent_data)
    
    # Then discover it
    response = await test_client.get("/api/v1/agents/discover?skill=discovery_test")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert len(data["data"]["agents"]) >= 1
    assert any(a["id"] == "discovery-test-agent" for a in data["data"]["agents"])
```

## 🎮 Interactive Playground

### Jupyter Notebook Example

```python
# In a Jupyter notebook cell
import asyncio
import nest_asyncio
nest_asyncio.apply()

from agentmesh import AgentMeshClient
from agentmesh.core.agent_card import AgentCard, Skill
import pandas as pd

# Create client
client = AgentMeshClient(base_url="http://localhost:8000")

# Register multiple agents
agents_to_register = [
    {
        "id": "notebook-weather-001",
        "name": "NotebookWeather",
        "skills": ["get_weather", "get_forecast"],
        "tags": ["weather", "notebook"]
    },
    {
        "id": "notebook-translate-001",
        "name": "NotebookTranslate",
        "skills": ["translate_text"],
        "tags": ["translation", "notebook"]
    }
]

for agent_data in agents_to_register:
    agent = AgentCard(
        id=agent_data["id"],
        name=agent_data["name"],
        version="1.0.0",
        description=f"{agent_data['name']} for notebook demo",
        skills=[Skill(name=skill, description=f"{skill} skill") 
               for skill in agent_data["skills"]],
        endpoint=f"http://localhost:8000/{agent_data['id']}",
        protocol="http",
        tags=agent_data["tags"]
    )
    
    response = await client.register_agent(agent)
    print(f"Registered: {agent_data['name']}")

# Discover and display as DataFrame
agents = await client.discover_agents()
df = pd.DataFrame([{
    'ID': a.id,
    'Name': a.name,
    'Skills': ', '.join([s.name for s in a.skills]),
    'Tags': ', '.join(a.tags),
    'Status': a.health_status
} for a in agents])

display(df)
```

## 📚 Additional Resources

### Try Online
- **REST Client**: Use [Postman](https://www.postman.com/) or [Insomnia](https://insomnia.rest/)
- **WebSocket Testing**: Use [WebSocket King](https://websocketking.com/)
- **API Documentation**: Access Swagger UI at `http://localhost:8000/docs`

### Learning Path
1. Start with the **Quick Start** examples
2. Try the **Python** examples for programmatic access
3. Experiment with the **Web** examples for browser-based interaction
4. Use the **CLI** tools for command-line operations
5. Explore **Docker** examples for containerized deployment

### Need Help?
- Check the [API Reference](api_reference.md) for detailed endpoint information
- Visit the [Troubleshooting Guide](../resources/troubleshooting.md) for common issues
- Join the [Community Discord](https://discord.gg/agentmesh) for real-time help

---

*Examples last tested: February 23, 2026*