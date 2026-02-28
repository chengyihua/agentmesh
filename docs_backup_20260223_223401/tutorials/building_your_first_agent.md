# Building Your First Agent

A step-by-step tutorial for creating and deploying your first AI Agent with AgentMesh.

## 🎯 What You'll Build

In this tutorial, you'll build a **WeatherBot** - an AI agent that provides weather information. By the end, you'll have:

1. ✅ A fully functional weather agent
2. ✅ Agent registered in AgentMesh network
3. ✅ Agent discoverable by other agents
4. ✅ Health monitoring enabled
5. ✅ Basic security implemented

## 📋 Prerequisites

Before you start, make sure you have:

- **Python 3.8+** installed
- **pip** package manager
- **AgentMesh server** running (or access to one)
- Basic knowledge of Python and REST APIs

## 🚀 Step 1: Set Up Your Environment

### Install Required Packages

```bash
# Create a virtual environment
python -m venv venv

# Activate it (macOS/Linux)
source venv/bin/activate

# Activate it (Windows)
venv\Scripts\activate

# Install AgentMesh SDK
pip install agentmesh

# Install additional dependencies
pip install fastapi uvicorn httpx pydantic
```

### Verify Installation

```python
import agentmesh
print(f"AgentMesh version: {agentmesh.__version__}")
```

## 🛠️ Step 2: Create Your Agent

### Project Structure

Create the following directory structure:

```
weatherbot/
├── weatherbot/
│   ├── __init__.py
│   ├── agent.py          # Agent definition
│   ├── api.py            # FastAPI server
│   └── weather_service.py # Weather logic
├── requirements.txt
├── Dockerfile
└── README.md
```

### Define Your Agent Card

Create `weatherbot/agent.py`:

```python
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime

class Skill(BaseModel):
    """A capability that the agent provides."""
    name: str
    description: str
    parameters: Optional[List[Dict[str, Any]]] = None
    returns: Optional[Dict[str, Any]] = None
    examples: Optional[List[Dict[str, Any]]] = None

class AgentCard(BaseModel):
    """The 'business card' of your AI Agent."""
    id: str = Field(
        default_factory=lambda: f"weatherbot-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        description="Unique identifier for the agent"
    )
    name: str = Field(
        default="WeatherBot",
        description="Human-readable name of the agent"
    )
    version: str = Field(
        default="1.0.0",
        description="Semantic version of the agent"
    )
    description: str = Field(
        default="Provides weather information for locations worldwide",
        description="Detailed description of what the agent does"
    )
    skills: List[Skill] = Field(
        default_factory=lambda: [
            Skill(
                name="get_current_weather",
                description="Get current weather for a location",
                parameters=[
                    {
                        "name": "location",
                        "type": "string",
                        "required": True,
                        "description": "City name or coordinates (lat,lon)"
                    },
                    {
                        "name": "units",
                        "type": "string",
                        "required": False,
                        "default": "metric",
                        "description": "Temperature units (metric/imperial)"
                    }
                ],
                returns={
                    "temperature": "float",
                    "conditions": "string",
                    "humidity": "float",
                    "wind_speed": "float"
                },
                examples=[
                    {
                        "input": {"location": "Tokyo", "units": "metric"},
                        "output": {
                            "temperature": 22.5,
                            "conditions": "Partly cloudy",
                            "humidity": 65,
                            "wind_speed": 12.3
                        }
                    }
                ]
            ),
            Skill(
                name="get_forecast",
                description="Get weather forecast for a location",
                parameters=[
                    {
                        "name": "location",
                        "type": "string",
                        "required": True,
                        "description": "City name or coordinates"
                    },
                    {
                        "name": "days",
                        "type": "integer",
                        "required": False,
                        "default": 3,
                        "description": "Number of days to forecast"
                    }
                ],
                returns={
                    "forecast": "list",
                    "location": "string",
                    "updated_at": "datetime"
                }
            )
        ],
        description="Capabilities provided by the agent"
    )
    endpoint: HttpUrl = Field(
        default="http://localhost:8001",
        description="URL where the agent's API is available"
    )
    protocol: str = Field(
        default="http",
        description="Communication protocol (http/grpc/websocket)"
    )
    tags: List[str] = Field(
        default_factory=lambda: ["weather", "forecast", "api", "demo"],
        description="Keywords for discovery"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=lambda: {
            "author": "Your Name",
            "license": "MIT",
            "repository": "https://github.com/yourusername/weatherbot"
        },
        description="Additional metadata about the agent"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "id": "weatherbot-20240223120000",
                "name": "WeatherBot",
                "version": "1.0.0",
                "description": "Provides weather information",
                "skills": [
                    {
                        "name": "get_current_weather",
                        "description": "Get current weather"
                    }
                ],
                "endpoint": "http://localhost:8001",
                "protocol": "http",
                "tags": ["weather", "demo"]
            }
        }

def create_weatherbot_agent() -> AgentCard:
    """Factory function to create a WeatherBot agent."""
    return AgentCard()
```

### Implement Weather Service

Create `weatherbot/weather_service.py`:

```python
import httpx
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import random

class WeatherService:
    """Mock weather service for demonstration purposes.
    
    In a real implementation, you would integrate with:
    - OpenWeatherMap API
    - Weather.com API
    - AccuWeather API
    - Or any other weather service
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes in seconds
        
    async def get_current_weather(self, location: str, units: str = "metric") -> Dict[str, Any]:
        """Get current weather for a location."""
        cache_key = f"current_{location}_{units}"
        
        # Check cache
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                return cached_data
        
        # Mock implementation - replace with real API call
        weather_data = await self._mock_weather_api(location, units)
        
        # Cache the result
        self.cache[cache_key] = (weather_data, datetime.now())
        
        return weather_data
    
    async def get_forecast(self, location: str, days: int = 3) -> Dict[str, Any]:
        """Get weather forecast for a location."""
        cache_key = f"forecast_{location}_{days}"
        
        # Check cache
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                return cached_data
        
        # Mock implementation
        forecast_data = await self._mock_forecast_api(location, days)
        
        # Cache the result
        self.cache[cache_key] = (forecast_data, datetime.now())
        
        return forecast_data
    
    async def _mock_weather_api(self, location: str, units: str) -> Dict[str, Any]:
        """Mock weather API response."""
        await asyncio.sleep(0.1)  # Simulate API delay
        
        # Generate realistic mock data
        if units == "metric":
            temp_range = (-10, 35)
            wind_unit = "km/h"
        else:
            temp_range = (14, 95)
            wind_unit = "mph"
        
        conditions = ["Sunny", "Partly cloudy", "Cloudy", "Rainy", "Snowy", "Stormy"]
        
        return {
            "location": location,
            "temperature": round(random.uniform(*temp_range), 1),
            "feels_like": round(random.uniform(*temp_range), 1),
            "conditions": random.choice(conditions),
            "humidity": random.randint(30, 90),
            "wind_speed": round(random.uniform(0, 30), 1),
            "wind_direction": random.choice(["N", "NE", "E", "SE", "S", "SW", "W", "NW"]),
            "pressure": random.randint(980, 1030),
            "visibility": random.randint(1, 20),
            "units": units,
            "wind_unit": wind_unit,
            "timestamp": datetime.now().isoformat(),
            "source": "mock"
        }
    
    async def _mock_forecast_api(self, location: str, days: int) -> Dict[str, Any]:
        """Mock forecast API response."""
        await asyncio.sleep(0.2)  # Simulate API delay
        
        forecast = []
        for i in range(days):
            date = datetime.now() + timedelta(days=i)
            forecast.append({
                "date": date.strftime("%Y-%m-%d"),
                "high_temp": round(random.uniform(15, 30), 1),
                "low_temp": round(random.uniform(5, 20), 1),
                "conditions": random.choice(["Sunny", "Partly cloudy", "Cloudy", "Rainy"]),
                "precipitation_chance": random.randint(0, 80),
                "wind_speed": round(random.uniform(5, 25), 1)
            })
        
        return {
            "location": location,
            "forecast": forecast,
            "days": days,
            "updated_at": datetime.now().isoformat(),
            "source": "mock"
        }
    
    def clear_cache(self):
        """Clear the weather cache."""
        self.cache.clear()

# Singleton instance
weather_service = WeatherService()
```

### Create the API Server

Create `weatherbot/api.py`:

```python
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from typing import Optional, Dict, Any
import asyncio
from datetime import datetime

from .agent import AgentCard, create_weatherbot_agent
from .weather_service import weather_service

app = FastAPI(
    title="WeatherBot API",
    description="Weather information agent",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create agent instance
agent = create_weatherbot_agent()

@app.get("/")
async def root():
    """Root endpoint with agent information."""
    return {
        "message": f"Welcome to {agent.name} v{agent.version}",
        "description": agent.description,
        "endpoints": {
            "health": "/health",
            "skills": "/skills",
            "weather": "/weather/current",
            "forecast": "/weather/forecast",
            "agent_info": "/agent"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agent_id": agent.id,
        "uptime": "0:00:00"  # In real implementation, calculate actual uptime
    }

@app.get("/skills")
async def list_skills():
    """List all skills provided by this agent."""
    return {
        "skills": [skill.dict() for skill in agent.skills],
        "count": len(agent.skills)
    }

@app.get("/weather/current")
async def get_current_weather(
    location: str = Query(..., description="City name or coordinates"),
    units: str = Query("metric", description="Temperature units (metric/imperial)")
):
    """Get current weather for a location."""
    try:
        weather_data = await weather_service.get_current_weather(location, units)
        return {
            "success": True,
            "data": weather_data,
            "timestamp": datetime.now().isoformat(),
            "skill": "get_current_weather"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get weather data: {str(e)}"
        )

@app.get("/weather/forecast")
async def get_forecast(
    location: str = Query(..., description="City name or coordinates"),
    days: int = Query(3, ge=1, le=7, description="Number of days to forecast (1-7)")
):
    """Get weather forecast for a location."""
    try:
        forecast_data = await weather_service.get_forecast(location, days)
        return {
            "success": True,
            "data": forecast_data,
            "timestamp": datetime.now().isoformat(),
            "skill": "get_forecast"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get forecast: {str(e)}"
        )

@app.get("/agent")
async def get_agent_info():
    """Get agent information in AgentCard format."""
    return agent.dict()

@app.post("/heartbeat")
async def heartbeat():
    """Heartbeat endpoint for health monitoring."""
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "agent_id": agent.id
    }

def run_server(host: str = "0.0.0.0", port: int = 8001):
    """Run the API server."""
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    run_server()
```

## 🔗 Step 3: Register with AgentMesh

### Create Registration Script

Create `register_agent.py`:

```python
#!/usr/bin/env python3
"""
Register WeatherBot with AgentMesh
"""

import asyncio
import httpx
import sys
from typing import Optional
from weatherbot.agent import create_weatherbot_agent

async def register_with_agentmesh(
    agentmesh_url: str = "http://localhost:8000",
    agent_endpoint: str = "http://localhost:8001",
    api_key: Optional[str] = None
) -> bool:
    """Register the agent with AgentMesh."""
    
    # Create agent instance
    agent = create_weatherbot_agent()
    
    # Update endpoint if provided
    if agent_endpoint:
        agent.endpoint = agent_endpoint
    
    # Prepare headers
    headers = {
        "Content-Type": "application/json"
    }
    if api_key:
        headers["X-API-Key"] = api_key
    
    # Register agent
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{agentmesh_url}/api/v1/agents/register",
                json={"agent_card": agent.dict()},
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code == 201:
                data = response.json()
                print(f"✅ Successfully registered {agent.name}!")
                print(f"   Agent ID: {data['data']['agent_id']}")
                print(f"   Registered at: {data['data']['registered_at']}")
                print(f"   Skills: {[s.name for s in agent.skills]}")
                return True
            else:
                print(f"❌ Registration failed with status {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except httpx.ConnectError:
            print(f"❌ Cannot connect to AgentMesh at {agentmesh_url}")
            print("   Make sure the AgentMesh server is running")
            return False
        except Exception as e:
            print(f"❌ Registration error: {str(e)}")
            return False

async def verify_registration(
    agentmesh_url: str = "http://localhost:8000",
    agent_id: Optional[str] = None
) -> bool:
    """Verify that the agent is registered and discoverable."""
    
    async with httpx.AsyncClient() as client:
        try:
            # Try to discover weather agents
            response = await client.get(
                f"{agentmesh_url}/api/v1/agents/discover",
                params={"skill": "get_current_weather"},
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                agents = data.get("data", {}).get("agents", [])
                
                if agents:
                    print(f"✅ Found {len(agents)} weather agents:")
                    for agent in agents:
                        print(f"   - {agent['name']} ({agent['id']})")
                    
                    # Check if our agent is in the list
                    if agent_id:
                        our_agent = next((a for a in agents if a["id"] == agent_id), None)
                        if our_agent:
                            print(f"✅ Our agent is discoverable!")
                            return True
                        else:
                            print(f"⚠️  Our agent not found in discovery results")
                            return False
                    return True
                else:
                    print("⚠️  No weather agents found")
                    return False
            else:
                print(f"❌ Discovery failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Verification error: {str(e)}")
            return False

async def main():
    """Main registration flow."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Register WeatherBot with AgentMesh")
    parser.add_argument("--agentmesh-url", default="http://localhost:8000",
                       help="URL of AgentMesh server")
    parser.add_argument("--agent-endpoint", default="http://localhost:8001",
                       help="URL where this agent is running")
    parser.add_argument("--api-key", help="API key for authentication")
    parser.add_argument("--verify-only", action="store_true",
                       help="Only verify registration, don't register")
    
    args = parser.parse_args()
    
    if not args.verify_only:
        print("🚀 Registering WeatherBot with AgentMesh...")
        success = await register_with_agentmesh(
            agentmesh_url=args.agentmesh_url,
            agent_endpoint=args.agent_endpoint,
            api_key=args.api_key
        )
        
        if not success:
            sys.exit(1)
    
    print("\n🔍 Verifying registration...")
    # In a real scenario, you'd get the agent ID from registration response
    await verify_registration(
        agentmesh_url=args.agentmesh_url,
        agent_id=None  # Would be actual agent ID
    )

if __name__ == "__main__":
    asyncio.run(main())
```

### Create Requirements File

Create `requirements.txt`:

```
agentmesh>=0.1.0
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
httpx>=0.25.0
pydantic>=2.0.0
python-multipart>=0.0.6
```

## 🚀 Step 4: Run Your Agent

### Start the WeatherBot Server

```bash
# In one terminal, start the WeatherBot API
cd weatherbot
python -m weatherbot.api
```

You should see output like:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
```

### Test the API

```bash
# Test the health endpoint
curl http://localhost:8001/health

# Test weather endpoint
curl "http://localhost:8001/weather/current?location=Tokyo"

# Test forecast endpoint
curl "http://localhost:8001/weather/forecast?location=New+York&days=3"
```

### Register with AgentMesh

Make sure AgentMesh server is running, then:

```bash
# Register the agent
python register_agent.py --agentmesh-url http://localhost:8000

# Or with API key if required
python register_agent.py --agentmesh-url http://localhost:8000 --api-key your-api-key
```

## 🔍 Step 5: Verify Your Agent

### Check Agent Registration

```bash
# Direct API call to AgentMesh
curl "http://localhost:8000/api/v1/agents/discover?skill=get_current_weather"

# Or use the AgentMesh CLI if available
agentmesh agents discover --skill get_current_weather
```

### Test Discovery from Another Agent

Create a test script `test_discovery.py`:

```python
import asyncio
import httpx

async def test_discovery():
    async with httpx.AsyncClient() as client:
        # Discover weather agents
        response = await client.get(
            "http://localhost:8000/api/v1/agents/discover",
            params={"skill": "get_current_weather"}
        )
        
        if response.status_code == 200:
            data = response.json()
            agents = data["data"]["agents"]
            
            print(f"Found {len(agents)} weather agents:")
            for agent in agents:
                print(f"\n📋 {agent['name']} ({agent['id']})")
                print(f"   Description: {agent['description']}")
                print(f"   Endpoint: {agent['endpoint']}")
                print(f"   Skills: {[s['name'] for s in agent['skills']]}")
                
                # Test calling the agent
                try:
                    weather_response = await client.get(
                        f"{agent['endpoint']}/weather/current",
                        params={"location": "London"}
                    )
                    if weather_response.status_code == 200:
                        weather_data = weather_response.json()
                        print(f"   ✅ Weather in London: {weather_data['data']['temperature']}°C")
                    else:
                        print(f"   ❌ Weather API error: {weather_response.status_code}")
                except Exception as e:
                    print(f"   ❌ Failed to call agent: {str(e)}")

asyncio.run(test_discovery())
```

## 🛡️ Step 6: Add Security

### Add API Key Authentication

Update `weatherbot/api.py` to add authentication:

```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN

# API key configuration (in production, use environment variables)
API_KEYS = {
    "test-key-123": {"name": "Test Client", "permissions": ["read"]},
    "admin-key-456": {"name": "Admin", "permissions": ["read", "write"]}
}

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(api_key: str = Security(api_key_header)):
    """Validate API key."""
    if api_key in API_KEYS:
        return api_key
    raise HTTPException(
        status_code=HTTP_403_FORBIDDEN,
        detail="Invalid or missing API Key"
    )

# Update endpoints to require authentication
@app.get("/weather/current")
async def get_current_weather(
    location: str = Query(...),
    units: str = Query("metric"),
    api_key: str = Security(get_api_key)
):
    # ... existing code ...
```

### Add Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/weather/current")
@limiter.limit("10/minute")
async def get_current_weather(
    location: str = Query(...),
    units: str = Query("metric"),
    request: Request
):
    # ... existing code ...
```

## 📦 Step 7: Package Your Agent

### Create Dockerfile

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY weatherbot/ ./weatherbot/
COPY register_agent.py .

# Create non-root user
RUN useradd -m -u 1000 agentuser && chown -R agentuser:agentuser /app
USER agentuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')"

# Expose port
EXPOSE 8001

# Run the application
CMD ["python", "-m", "weatherbot.api"]
```

### Create docker-compose.yml

Create `docker-compose.yml` for easy deployment:

```yaml
version: '3.8'

services:
  weatherbot:
    build: .
    ports:
      - "8001:8001"
    environment:
      - AGENTMESH_URL=http://agentmesh:8000
      - API_KEY=${API_KEY:-test-key-123}
      - LOG_LEVEL=INFO
    depends_on:
      - agentmesh
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  agentmesh:
    image: agentmesh/agentmesh:latest
    ports:
      - "8000:8000"
    environment:
      - STORAGE_BACKEND=memory
      - JWT_SECRET=${JWT_SECRET:-change-me-in-production}
    restart: unless-stopped
```

### Build and Run with Docker

```bash
# Build the image
docker build -t weatherbot:latest .

# Run with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f weatherbot

# Test the service
curl http://localhost:8001/health
```

## 📊 Step 8: Monitor Your Agent

### Add Metrics Endpoint

Add to `weatherbot/api.py`:

```python
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Define metrics
weather_requests = Counter(
    'weatherbot_requests_total',
    'Total weather requests',
    ['endpoint', 'status']
)

weather_response_time = Histogram(
    'weatherbot_response_time_seconds',
    'Response time for weather requests',
    ['endpoint']
)

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

# Update weather endpoints to track metrics
@app.get("/weather/current")
@weather_response_time.labels("current").time()
async def get_current_weather(location: str, units: str = "metric"):
    try:
        # ... existing code ...
        weather_requests.labels("current", "success").inc()
        return result
    except Exception as e:
        weather_requests.labels("current", "error").inc()
        raise
```

### Create Monitoring Dashboard

Create `monitoring/dashboard.json` for Grafana:

```json
{
  "dashboard": {
    "title": "WeatherBot Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(weatherbot_requests_total[5m])",
            "legendFormat": "{{endpoint}} - {{status}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(weatherbot_response_time_seconds_bucket[5m]))",
            "legendFormat": "{{endpoint}} - p95"
          }
        ]
      }
    ]
  }
}
```

## 🚀 Step 9: Deploy to Production

### Create Deployment Script

Create `deploy.sh`:

```bash
#!/bin/bash

# Deployment script for WeatherBot

set -e  # Exit on error

# Configuration
APP_NAME="weatherbot"
VERSION="1.0.0"
REGISTRY="your-registry.io"
NAMESPACE="agents"

echo "🚀 Deploying $APP_NAME v$VERSION..."

# Build and push Docker image
echo "📦 Building Docker image..."
docker build -t $REGISTRY/$APP_NAME:$VERSION .
docker push $REGISTRY/$APP_NAME:$VERSION

# Update Kubernetes deployment
echo "⚙️  Updating Kubernetes deployment..."
kubectl -n $NAMESPACE set image deployment/$APP_NAME $APP_NAME=$REGISTRY/$APP_NAME:$VERSION

# Wait for rollout
echo "⏳ Waiting for rollout..."
kubectl -n $NAMESPACE rollout status deployment/$APP_NAME --timeout=300s

# Verify deployment
echo "🔍 Verifying deployment..."
kubectl -n $NAMESPACE get pods -l app=$APP_NAME

echo "✅ Deployment complete!"
```

### Create Kubernetes Manifest

Create `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: weatherbot
  namespace: agents
spec:
  replicas: 3
  selector:
    matchLabels:
      app: weatherbot
  template:
    metadata:
      labels:
        app: weatherbot
    spec:
      containers:
      - name: weatherbot
        image: your-registry.io/weatherbot:1.0.0
        ports:
        - containerPort: 8001
        env:
        - name: AGENTMESH_URL
          value: "http://agentmesh.agents.svc.cluster.local:8000"
        - name: API_KEY
          valueFrom:
            secretKeyRef:
              name: weatherbot-secrets
              key: api-key
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: weatherbot
  namespace: agents
spec:
  selector:
    app: weatherbot
  ports:
  - port: 8001
    targetPort: 8001
  type: ClusterIP
```

## 🎉 Congratulations!

You've successfully built and deployed your first AI Agent with AgentMesh! Here's what you've accomplished:

### ✅ Completed Tasks
1. **Created a WeatherBot agent** with weather forecasting capabilities
2. **Implemented a REST API** using FastAPI
3. **Registered with AgentMesh** for discovery
4. **Added security features** including API key authentication
5. **Packaged with Docker** for easy deployment
6. **Added monitoring** with Prometheus metrics
7. **Prepared for production** with Kubernetes manifests

### 🚀 Next Steps

Now that you have a working agent, consider:

1. **Replace mock data** with real weather API integration
2. **Add more skills** like historical weather, alerts, etc.
3. **Implement caching** for better performance
4. **Add authentication** with OAuth or JWT
5. **Create a frontend** for your weather service
6. **Set up CI/CD** for automated deployments
7. **Join the AgentMesh community** to share your agent

### 📚 Resources

- [AgentMesh Documentation](https://agentmesh.io/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)

### 🆘 Need Help?

- Check the [AgentMesh Troubleshooting Guide](../resources/troubleshooting.md)
- Join the [AgentMesh Discord Community](https://discord.gg/agentmesh)
- Open an issue on [GitHub](https://github.com/agentmesh/agentmesh/issues)

---

*Tutorial last updated: February 23, 2026*