# AgentMesh Data Models

Complete reference for all data structures used in AgentMesh.

## 📋 Overview

This document describes all data models used in the AgentMesh protocol. All models are defined using Pydantic for automatic validation and serialization.

## 🎯 AgentCard

The core data structure representing an AI Agent in the network.

### Schema

```python
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl


class ProtocolType(str, Enum):
    """Supported communication protocols."""
    HTTP = "http"
    WEBSOCKET = "websocket"
    GRPC = "grpc"
    MCP = "mcp"
    CUSTOM = "custom"


class HealthStatus(str, Enum):
    """Agent health status."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class Skill(BaseModel):
    """Agent capability."""
    name: str = Field(..., min_length=1, max_length=100, description="Skill identifier")
    description: str = Field(..., min_length=1, max_length=500, description="Skill description")
    parameters: Optional[List[Dict[str, Any]]] = Field(default=None, description="Input parameters schema")
    returns: Optional[Dict[str, Any]] = Field(default=None, description="Return type schema")
    examples: Optional[List[Dict[str, Any]]] = Field(default=None, description="Usage examples")


class AgentCard(BaseModel):
    """Agent identity and capability card."""
    # Core identity
    id: str = Field(..., min_length=1, max_length=100, description="Unique agent identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Human-readable agent name")
    version: str = Field(..., regex=r'^\d+\.\d+\.\d+$', description="Semantic version (e.g., 1.0.0)")
    
    # Description
    description: str = Field(..., min_length=1, max_length=1000, description="Brief agent description")
    
    # Capabilities
    skills: List[Skill] = Field(..., min_items=1, description="List of agent skills")
    
    # Communication
    endpoint: HttpUrl = Field(..., description="Service endpoint URL")
    protocol: ProtocolType = Field(default=ProtocolType.HTTP, description="Communication protocol")
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    health_status: HealthStatus = Field(default=HealthStatus.UNKNOWN, description="Current health status")
    
    # Timestamps
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    
    # Security
    signature: Optional[str] = Field(default=None, description="Digital signature for verification")
    
    # Extensions
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
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
                "tags": ["weather", "forecast", "api"],
                "health_status": "healthy"
            }
        }
```

### Example

```json
{
  "id": "weather-bot-001",
  "name": "WeatherBot",
  "version": "1.0.0",
  "description": "Weather forecasting service with real-time updates",
  "skills": [
    {
      "name": "get_weather",
      "description": "Get current weather for a location",
      "parameters": [
        {
          "name": "city",
          "type": "string",
          "required": true,
          "description": "City name"
        },
        {
          "name": "country",
          "type": "string",
          "required": false,
          "description": "Country code (ISO 3166-1 alpha-2)"
        }
      ],
      "returns": {
        "type": "object",
        "properties": {
          "temperature": {"type": "number", "description": "Temperature in Celsius"},
          "condition": {"type": "string", "description": "Weather condition"},
          "humidity": {"type": "number", "description": "Humidity percentage"}
        }
      },
      "examples": [
        {
          "input": {"city": "Tokyo", "country": "JP"},
          "output": {
            "temperature": 22.5,
            "condition": "Partly Cloudy",
            "humidity": 65
          }
        }
      ]
    }
  ],
  "endpoint": "https://api.weatherbot.example.com/v1",
  "protocol": "http",
  "tags": ["weather", "forecast", "api", "real-time"],
  "health_status": "healthy",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z",
  "signature": "sha256=abc123...",
  "metadata": {
    "provider": "WeatherCorp",
    "rate_limit": 1000,
    "supported_languages": ["en", "ja", "zh"]
  }
}
```

## 📝 AgentCardUpdate

Model for updating an existing agent.

```python
class AgentCardUpdate(BaseModel):
    """Update model for AgentCard (partial updates allowed)."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    version: Optional[str] = Field(None, regex=r'^\d+\.\d+\.\d+$')
    description: Optional[str] = Field(None, min_length=1, max_length=1000)
    skills: Optional[List[Skill]] = Field(None, min_items=1)
    endpoint: Optional[HttpUrl] = Field(None)
    protocol: Optional[ProtocolType] = Field(None)
    tags: Optional[List[str]] = Field(None)
    health_status: Optional[HealthStatus] = Field(None)
    signature: Optional[str] = Field(None)
    metadata: Optional[Dict[str, Any]] = Field(None)
```

## 📊 API Response Models

### Base Response

```python
class BaseResponse(BaseModel):
    """Base response model for all API endpoints."""
    success: bool = Field(..., description="Whether the operation was successful")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    message: Optional[str] = Field(None, description="Human-readable message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
```

### Error Response

```python
class ErrorDetail(BaseModel):
    """Detailed error information."""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error description")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class ErrorResponse(BaseResponse):
    """Error response model."""
    error: ErrorDetail = Field(..., description="Error information")
    data: Optional[Dict[str, Any]] = Field(None)
```

### Registration Response

```python
class RegistrationResponse(BaseResponse):
    """Response for agent registration."""
    data: Dict[str, Any] = Field(
        ...,
        example={
            "agent_id": "weather-bot-001",
            "registered_at": "2024-01-01T00:00:00Z"
        }
    )
```

### Discovery Response

```python
class DiscoveryResponse(BaseResponse):
    """Response for agent discovery."""
    data: Dict[str, Any] = Field(
        ...,
        example={
            "agents": [
                {
                    "id": "weather-bot-001",
                    "name": "WeatherBot",
                    "description": "Weather forecasting service",
                    "skills": ["get_weather", "get_forecast"],
                    "endpoint": "http://localhost:8001/weather",
                    "protocol": "http",
                    "tags": ["weather", "forecast", "api"],
                    "health_status": "healthy",
                    "last_seen": "2024-01-01T00:00:00Z"
                }
            ],
            "total": 1,
            "limit": 10,
            "offset": 0
        }
    )
```

## 🔐 Authentication Models

### Token Request

```python
class TokenRequest(BaseModel):
    """Request model for obtaining an API token."""
    agent_id: str = Field(..., description="Agent identifier")
    secret: str = Field(..., description="Secret key for authentication")
    expires_in: Optional[int] = Field(3600, ge=60, le=86400, description="Token expiration in seconds")
```

### Token Response

```python
class TokenResponse(BaseResponse):
    """Response model for token requests."""
    data: Dict[str, Any] = Field(
        ...,
        example={
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "expires_in": 3600,
            "refresh_token": "def456..."
        }
    )
```

## 💓 Health Models

### Heartbeat Request

```python
class HeartbeatRequest(BaseModel):
    """Request model for sending heartbeat."""
    status: HealthStatus = Field(..., description="Current health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Heartbeat timestamp")
    metrics: Optional[Dict[str, Any]] = Field(None, description="Performance metrics")
```

### Health Check Response

```python
class HealthCheckResponse(BaseResponse):
    """Response model for health checks."""
    data: Dict[str, Any] = Field(
        ...,
        example={
            "agent_id": "weather-bot-001",
            "health_status": "healthy",
            "last_heartbeat": "2024-01-01T00:00:00Z",
            "next_check": "2024-01-01T00:05:00Z",
            "uptime": "24h 30m 15s"
        }
    )
```

## 📈 Statistics Models

### System Statistics

```python
class SystemStats(BaseModel):
    """System-wide statistics."""
    total_agents: int = Field(..., ge=0, description="Total number of registered agents")
    total_skills: int = Field(..., ge=0, description="Total number of unique skills")
    healthy_agents: int = Field(..., ge=0, description="Number of healthy agents")
    unhealthy_agents: int = Field(..., ge=0, description="Number of unhealthy agents")
    unknown_agents: int = Field(..., ge=0, description="Number of agents with unknown status")
    uptime: str = Field(..., description="System uptime in human-readable format")
    requests_per_minute: float = Field(..., ge=0, description="Average requests per minute")
    storage_backend: str = Field(..., description="Current storage backend")
    version: str = Field(..., description="AgentMesh version")
```

### Agent Statistics

```python
class AgentStats(BaseModel):
    """Agent-specific statistics."""
    agent_id: str = Field(..., description="Agent identifier")
    registered_at: datetime = Field(..., description="Registration timestamp")
    total_requests: int = Field(..., ge=0, description="Total number of requests")
    successful_requests: int = Field(..., ge=0, description="Number of successful requests")
    failed_requests: int = Field(..., ge=0, description="Number of failed requests")
    average_response_time: float = Field(..., ge=0, description="Average response time in milliseconds")
    availability: float = Field(..., ge=0, le=100, description="Availability percentage")
    last_30_days: List[Dict[str, Any]] = Field(default_factory=list, description="Daily statistics for last 30 days")
```

## 🔄 Webhook Models

### Webhook Subscription

```python
class WebhookSubscription(BaseModel):
    """Webhook subscription for event notifications."""
    url: HttpUrl = Field(..., description="Webhook endpoint URL")
    events: List[str] = Field(..., min_items=1, description="List of events to subscribe to")
    secret: Optional[str] = Field(None, description="Secret for signature verification")
    enabled: bool = Field(default=True, description="Whether the subscription is active")
```

### Webhook Event

```python
class WebhookEvent(BaseModel):
    """Webhook event payload."""
    event_type: str = Field(..., description="Event type (agent.registered, agent.updated, etc.)")
    agent_id: str = Field(..., description="Agent identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    data: Dict[str, Any] = Field(..., description="Event data")
    signature: Optional[str] = Field(None, description="Event signature for verification")
```

## 📝 Validation Rules

### AgentCard Validation

1. **ID**: Must be unique, 1-100 characters, alphanumeric with hyphens and underscores
2. **Name**: 1-100 characters, human-readable
3. **Version**: Must follow semantic versioning (X.Y.Z)
4. **Skills**: At least one skill required
5. **Endpoint**: Valid HTTP/HTTPS URL
6. **Tags**: Optional, each tag 1-50 characters

### Skill Validation

1. **Name**: 1-100 characters, alphanumeric with hyphens and underscores
2. **Description**: 1-500 characters
3. **Parameters**: Optional, must be valid JSON Schema if provided
4. **Returns**: Optional, must be valid JSON Schema if provided

## 🔗 Related Models

### Rate Limit Info

```python
class RateLimitInfo(BaseModel):
    """Rate limit information."""
    limit: int = Field(..., ge=0, description="Maximum requests allowed")
    remaining: int = Field(..., ge=0, description="Remaining requests")
    reset: int = Field(..., ge=0, description="Seconds until reset")
```

### Pagination

```python
class PaginationParams(BaseModel):
    """Pagination parameters."""
    limit: int = Field(10, ge=1, le=100, description="Maximum results per page")
    offset: int = Field(0, ge=0, description="Pagination offset")
```

### Search Parameters

```python
class SearchParams(BaseModel):
    """Search parameters."""
    query: str = Field(..., min_length=1, max_length=200, description="Search query")
    fields: Optional[List[str]] = Field(None, description="Fields to search in")
    fuzzy: bool = Field(default=False, description="Enable fuzzy search")
```

## 📊 Database Models

### Agent Record

```python
class AgentRecord(BaseModel):
    """Database record for an agent."""
    id: str = Field(..., description="Primary key")
    agent_card: AgentCard = Field(..., description="Complete agent card")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_seen: datetime = Field(..., description="Last heartbeat timestamp")
    is_active: bool = Field(default=True, description="Whether the agent is active")
    
    class Config:
        from_attributes = True
```

### Skill Index

```python
class SkillIndex(BaseModel):
    """Index for skill-based search."""
    skill_name: str = Field(..., description="Skill name")
    agent_ids: List[str] = Field(default_factory=list, description="Agent IDs with this skill")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Index creation time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
```

## 🎯 Usage Examples

### Creating an AgentCard

```python
from agentmesh.core.agent_card import AgentCard, Skill, ProtocolType, HealthStatus
from datetime import datetime

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
    endpoint="https://api.translationbot.example.com/v1",
    protocol=ProtocolType.HTTP,
    tags=["translation", "nlp", "multilingual"],
    health_status=HealthStatus.HEALTHY,
    created_at=datetime.utcnow(),
    metadata={
        "supported_languages": ["en", "zh", "ja", "ko", "fr", "es"],
        "max_text_length": 5000
    }
)
```

### Validating Input

```python
from agentmesh.core.agent_card import AgentCard
from pydantic import ValidationError

try:
    agent = AgentCard(**input_data)
    print("Validation passed")
except ValidationError as e:
    print(f"Validation failed: {e}")
```

### Serializing to JSON

```python
import json

# Convert to dict
agent_dict = agent.dict()

# Convert to JSON
agent_json = agent.json()

# Pretty print
agent_json_pretty = agent.json(indent=2)
```

## 🔗 Related Documents

- [API Reference](api_reference.md) - Complete API documentation
- [Protocol Specification](protocol_specification.md) - Protocol details
- [Quick Start Guide](quick_start.md) - Getting started guide