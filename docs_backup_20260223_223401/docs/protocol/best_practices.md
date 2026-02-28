# AgentMesh Best Practices

Guidelines and recommendations for building robust, scalable, and secure AgentMesh applications.

## 🎯 Design Principles

### 1. Keep Agents Focused

**Do:**
- Create specialized agents with clear, focused capabilities
- Each agent should excel at one specific task or domain
- Use clear, descriptive skill names

**Don't:**
- Create monolithic agents that try to do everything
- Overload agents with unrelated capabilities

**Example:**
```python
# Good: Focused agents
weather_agent = AgentCard(
    name="WeatherBot",
    skills=[Skill(name="get_weather", description="Get current weather")]
)

translation_agent = AgentCard(
    name="TranslationBot", 
    skills=[Skill(name="translate_text", description="Translate between languages")]
)

# Bad: Monolithic agent
monolithic_agent = AgentCard(
    name="DoEverythingBot",
    skills=[
        Skill(name="get_weather", description="Get weather"),
        Skill(name="translate_text", description="Translate text"),
        Skill(name="analyze_sentiment", description="Analyze sentiment"),
        Skill(name="generate_image", description="Generate images")
    ]
)
```

### 2. Use Semantic Versioning

**Always:**
- Follow semantic versioning (MAJOR.MINOR.PATCH)
- Increment MAJOR for breaking changes
- Increment MINOR for new features
- Increment PATCH for bug fixes

**Example:**
```python
# Version progression
version="1.0.0"    # Initial release
version="1.0.1"    # Bug fix
version="1.1.0"    # New feature (backward compatible)
version="2.0.0"    # Breaking change
```

### 3. Provide Clear Descriptions

**Do:**
- Write concise, informative descriptions
- Include examples in skill definitions
- Document parameters and return types

**Example:**
```python
skill = Skill(
    name="calculate_shipping",
    description="Calculate shipping cost and delivery time",
    parameters=[
        {
            "name": "weight",
            "type": "number",
            "required": True,
            "description": "Package weight in kilograms",
            "minimum": 0.1,
            "maximum": 100
        },
        {
            "name": "destination",
            "type": "string",
            "required": True,
            "description": "Destination country code (ISO 3166-1 alpha-2)"
        }
    ],
    returns={
        "type": "object",
        "properties": {
            "cost": {"type": "number", "description": "Shipping cost in USD"},
            "delivery_days": {"type": "integer", "description": "Estimated delivery days"},
            "carrier": {"type": "string", "description": "Recommended carrier"}
        }
    },
    examples=[
        {
            "input": {"weight": 2.5, "destination": "US"},
            "output": {"cost": 15.99, "delivery_days": 3, "carrier": "FedEx"}
        }
    ]
)
```

## 🔐 Security Best Practices

### 1. Always Use Authentication

**Production Deployment:**
```python
# Always use authentication in production
client = AgentMeshClient(
    base_url="https://agentmesh.example.com",
    api_key="your-secure-api-key"  # Or use token authentication
)

# For agent registration
agent = AgentCard(
    id="secure-bot-001",
    # ... other fields
    signature="sha256=..."  # Sign your agent cards
)
```

### 2. Implement Rate Limiting

**Server-side:**
```python
from agentmesh.server import AgentMeshServer
from agentmesh.security import RateLimiter

server = AgentMeshServer(
    rate_limiter=RateLimiter(
        requests_per_minute=100,  # Per agent
        burst_limit=20
    )
)
```

**Client-side:**
```python
import asyncio
import aiolimiter

class RateLimitedClient:
    def __init__(self):
        self.limiter = aiolimiter.AsyncLimiter(10, 1)  # 10 requests per second
    
    async def call_agent(self, agent, request):
        async with self.limiter:
            return await agent.process(request)
```

### 3. Validate All Inputs

**Always validate:**
- Agent registration data
- Discovery query parameters
- Heartbeat requests
- Webhook payloads

**Example:**
```python
from pydantic import ValidationError

async def register_agent_handler(request_data):
    try:
        # Validate input
        agent_card = AgentCard(**request_data)
        
        # Additional business logic validation
        if not self._is_agent_authorized(agent_card):
            raise ValidationError("Agent not authorized")
        
        # Process registration
        return await self.registry.register_agent(agent_card)
        
    except ValidationError as e:
        return {
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": str(e),
                "details": e.errors()
            }
        }
```

## 🚀 Performance Optimization

### 1. Implement Caching

**Server-side caching:**
```python
from agentmesh.storage import CachedStorage

storage = CachedStorage(
    primary_storage=RedisStorage(url="redis://localhost:6379"),
    cache_ttl=300,  # 5 minutes
    cache_max_size=10000
)
```

**Client-side caching:**
```python
import asyncio
from datetime import datetime, timedelta

class CachedAgentMeshClient:
    def __init__(self, base_url, cache_ttl=60):
        self.client = AgentMeshClient(base_url)
        self.cache = {}
        self.cache_ttl = cache_ttl
    
    async def discover_agents(self, **kwargs):
        cache_key = str(kwargs)
        
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                return cached_data
        
        # Fetch fresh data
        agents = await self.client.discover_agents(**kwargs)
        self.cache[cache_key] = (agents, datetime.now())
        return agents
```

### 2. Use Connection Pooling

```python
import aiohttp
from agentmesh import AgentMeshClient

class OptimizedClient:
    def __init__(self):
        self.session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(
                limit=100,  # Max connections
                limit_per_host=10,  # Max connections per host
                ttl_dns_cache=300  # DNS cache TTL
            )
        )
        self.client = AgentMeshClient(
            base_url="...",
            session=self.session  # Reuse session
        )
    
    async def close(self):
        await self.session.close()
```

### 3. Implement Health Checks

**Regular health monitoring:**
```python
import asyncio
from datetime import datetime

class HealthMonitor:
    def __init__(self, client, check_interval=60):
        self.client = client
        self.check_interval = check_interval
        self.agent_health = {}
    
    async def start_monitoring(self):
        while True:
            await self._check_all_agents()
            await asyncio.sleep(self.check_interval)
    
    async def _check_all_agents(self):
        agents = await self.client.discover_agents()
        for agent in agents:
            health = await self.client.check_agent_health(agent.id)
            self.agent_health[agent.id] = {
                "status": health,
                "last_check": datetime.now()
            }
```

## 📊 Monitoring and Logging

### 1. Structured Logging

```python
import logging
import json
from pythonjsonlogger import jsonlogger

# Configure JSON logging
logger = logging.getLogger("agentmesh")
handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    '%(asctime)s %(levelname)s %(name)s %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

# Log with context
logger.info("Agent registered", extra={
    "agent_id": agent.id,
    "agent_name": agent.name,
    "skills": [s.name for s in agent.skills],
    "duration_ms": duration
})
```

### 2. Metrics Collection

```python
from prometheus_client import Counter, Histogram, start_http_server

# Define metrics
AGENT_REGISTRATIONS = Counter(
    'agentmesh_agent_registrations_total',
    'Total number of agent registrations',
    ['protocol', 'status']
)

REQUEST_DURATION = Histogram(
    'agentmesh_request_duration_seconds',
    'Request duration in seconds',
    ['endpoint', 'method']
)

# Use in handlers
@REQUEST_DURATION.labels(endpoint='/agents/register', method='POST').time()
async def register_agent_handler(request):
    AGENT_REGISTRATIONS.labels(
        protocol=request.agent_card.protocol,
        status='success'
    ).inc()
    # ... handler logic
```

### 3. Error Tracking

```python
import sentry_sdk
from sentry_sdk.integrations.asyncio import AsyncioIntegration

# Initialize error tracking
sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[AsyncioIntegration()],
    traces_sample_rate=1.0
)

# Capture errors
try:
    await agent.process(request)
except Exception as e:
    sentry_sdk.capture_exception(e)
    raise
```

## 🔄 Deployment Strategies

### 1. Blue-Green Deployment

```yaml
# docker-compose.yml
version: '3.8'

services:
  agentmesh-blue:
    image: agentmesh:1.0.0
    ports:
      - "8000:8000"
    environment:
      - STORAGE_BACKEND=redis
      - REDIS_URL=redis://redis:6379
  
  agentmesh-green:
    image: agentmesh:1.1.0
    ports:
      - "8001:8000"
    environment:
      - STORAGE_BACKEND=redis
      - REDIS_URL=redis://redis:6379
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

### 2. Horizontal Scaling

```python
# Load balancer configuration
from agentmesh.load_balancer import RoundRobinLoadBalancer

load_balancer = RoundRobinLoadBalancer([
    "http://agentmesh-1.example.com:8000",
    "http://agentmesh-2.example.com:8000",
    "http://agentmesh-3.example.com:8000"
])

client = AgentMeshClient(load_balancer=load_balancer)
```

### 3. Database Sharding

```python
from agentmesh.storage import ShardedStorage

storage = ShardedStorage(
    shards=[
        RedisStorage(url="redis://shard1:6379"),
        RedisStorage(url="redis://shard2:6379"),
        RedisStorage(url="redis://shard3:6379")
    ],
    shard_key="agent_id"  # Shard by agent ID
)
```

## 🧪 Testing Strategies

### 1. Unit Testing

```python
import pytest
from agentmesh.core.agent_card import AgentCard, Skill

def test_agent_card_validation():
    # Test valid agent
    agent = AgentCard(
        id="test-bot",
        name="TestBot",
        version="1.0.0",
        description="Test agent",
        skills=[Skill(name="test", description="Test skill")],
        endpoint="http://localhost:8000"
    )
    assert agent.id == "test-bot"
    
    # Test invalid agent
    with pytest.raises(ValidationError):
        AgentCard(
            id="",  # Empty ID should fail
            name="TestBot",
            version="1.0.0",
            description="Test agent",
            skills=[],
            endpoint="http://localhost:8000"
        )
```

### 2. Integration Testing

```python
import pytest
import asyncio
from agentmesh import AgentMeshClient, AgentMeshServer

@pytest.fixture
async def agentmesh_server():
    server = AgentMeshServer(storage="memory")
    await server.start()
    yield server
    await server.stop()

@pytest.fixture
async def client(agentmesh_server):
    return AgentMeshClient(base_url="http://localhost:8000")

@pytest.mark.asyncio
async def test_agent_registration(client):
    agent = AgentCard(
        id="test-bot",
        name="TestBot",
        version="1.0.0",
        description="Test agent",
        skills=[Skill(name="test", description="Test skill")],
        endpoint="http://localhost:8000"
    )
    
    response = await client.register_agent(agent)
    assert response["success"] == True
    assert response["data"]["agent_id"] == "test-bot"
```

### 3. Load Testing

```python
import asyncio
from locust import HttpUser, task, between

class AgentMeshUser(HttpUser):
    wait_time = between(1, 5)
    
    @task
    def register_agent(self):
        self.client.post("/api/v1/agents/register", json={
            "agent_card": {
                "id": f"test-{self.user_id}",
                "name": "TestBot",
                "version": "1.0.0",
                "description": "Test agent",
                "skills": [{"name": "test", "description": "Test skill"}],
                "endpoint": "http://localhost:8000",
                "protocol": "http",
                "tags": ["test"]
            }
        })
    
    @task
    def discover_agents(self):
        self.client.get("/api/v1/agents/discover?skill=test")
```

## 🔧 Maintenance and Operations

### 1. Backup Strategy

```python
import asyncio
from datetime import datetime
import json

class BackupManager:
    def __init__(self, storage, backup_dir="/backups"):
        self.storage = storage
        self.backup_dir = backup_dir
    
    async def create_backup(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{self.backup_dir}/backup_{timestamp}.json"
        
        # Export all agents
        agents = await self.storage.get_all_agents()
        backup_data = {
            "timestamp": timestamp,
            "total_agents": len(agents),
            "agents": [agent.dict() for agent in agents]
        }
        
        # Save to file
        with open(backup_file, "w") as f:
            json.dump(backup_data, f, indent=2)
        
        return backup_file
```

### 2. Database Migration

```python
from alembic import op
import sqlalchemy as sa

# Migration script example
def upgrade():
    op.create_table(
        'agents',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('agent_card', sa.JSON, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('last_seen', sa.DateTime, nullable=False),
        sa.Column('is_active', sa.Boolean, default=True)
    )
    
    op.create_index('idx_agents_created_at', 'agents', ['created_at'])
    op.create_index('idx_agents_is_active', 'agents', ['is_active'])
```

### 3. Disaster Recovery

```python
class DisasterRecovery:
    def __init__(self, primary_storage, backup_storage):
        self.primary = primary_storage
        self.backup = backup_storage
    
    async def failover(self):
        # Check primary health
        if not await self.primary.is_healthy():
            # Switch to backup
            print("Primary storage failed, switching to backup")
            return self.backup
        
        return self.primary
    
    async def restore_from_backup(self, backup_file):
        with open(backup_file, "r") as f:
            backup_data = json.load(f)
        
        # Restore agents
        for agent_data in backup_data["agents"]:
            agent = AgentCard(**agent_data)
            await self.primary.register_agent(agent)
        
        print(f"Restored {len(backup_data['agents'])} agents from backup")
```

## 📚 Additional Resources

### Recommended Reading
- [12-Factor App Methodology](https://12factor.net/)
- [Microservices Patterns](https://microservices.io/patterns/)
- [Site Reliability Engineering](https://sre.google/sre-book/table-of-contents/)

### Useful Tools
- **Monitoring**: Prometheus, Grafana, Datadog
- **Logging**: ELK Stack, Loki, CloudWatch
- **Testing**: Pytest, Locust, Tox
- **Deployment**: Docker, Kubernetes, Terraform

### Community Resources
- [AgentMesh GitHub](https://github.com/agentmesh/agentmesh)
- [Discord Community](https://discord.gg/agentmesh)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/agentmesh)

## 🆘 Getting Help

If you encounter issues or have questions:

1. **Check the documentation** - This guide and other docs
2. **Search GitHub Issues** - Someone may have had the same problem
3. **Ask in Discord** - Community support
4. **Create an issue** - For bugs or feature requests

Remember: The best practices evolve with the project. Stay updated with the latest releases and community discussions!