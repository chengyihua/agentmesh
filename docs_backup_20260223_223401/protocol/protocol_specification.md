# AgentMesh Protocol Specification v1.0

## 📋 Overview

AgentMesh is an open, secure, and decentralized infrastructure for AI Agent registration and discovery. This document specifies the complete protocol for Agent-to-Agent communication and service discovery.

## 🎯 Design Principles

1. **Simplicity First** - Easy to understand and implement
2. **Security by Design** - Built-in security mechanisms
3. **Extensibility** - Support for multiple protocols and formats
4. **Interoperability** - Work with any language, any framework

## 📊 Protocol Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AgentMesh Protocol Stack                  │
├─────────────────────────────────────────────────────────────┤
│  Application Layer  │  Agent-to-Agent Communication         │
├─────────────────────────────────────────────────────────────┤
│  Discovery Layer    │  Registration, Discovery, Health Check│
├─────────────────────────────────────────────────────────────┤
│  Transport Layer    │  HTTP/HTTPS, WebSocket, gRPC          │
├─────────────────────────────────────────────────────────────┤
│  Security Layer     │  Authentication, Authorization, Crypto│
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Core Components

### 1. AgentCard - The Agent Identity

```yaml
# AgentCard Structure
id: string                    # Unique identifier
name: string                  # Human-readable name
version: string               # Version number
description: string           # Brief description
skills: Skill[]               # List of capabilities
endpoint: string              # Service endpoint URL
protocol: ProtocolType        # Communication protocol
tags: string[]                # Searchable tags
health_status: HealthStatus   # Current health status
created_at: datetime          # Creation timestamp
updated_at: datetime          # Last update timestamp
signature: string?            # Digital signature (optional)
```

### 2. Skill - Agent Capability

```yaml
# Skill Structure
name: string                  # Skill identifier
description: string           # Skill description
parameters: Parameter[]?      # Input parameters
returns: ReturnType?          # Return type
examples: Example[]?          # Usage examples
```

### 3. Protocol Types

```python
class ProtocolType(Enum):
    HTTP = "http"             # RESTful HTTP API
    WEBSOCKET = "websocket"   # WebSocket connection
    GRPC = "grpc"             # gRPC service
    MCP = "mcp"               # Model Context Protocol
    CUSTOM = "custom"         # Custom protocol
```

## 📡 Registration Protocol

### Registration Request

```http
POST /api/v1/agents/register
Content-Type: application/json

{
  "agent_card": {
    "id": "weather-bot-001",
    "name": "WeatherBot",
    "version": "1.0.0",
    "description": "Weather forecasting service",
    "skills": [
      {
        "name": "get_weather",
        "description": "Get current weather"
      }
    ],
    "endpoint": "http://localhost:8001/weather",
    "protocol": "http",
    "tags": ["weather", "forecast", "api"]
  }
}
```

### Registration Response

```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "success": true,
  "agent_id": "weather-bot-001",
  "message": "Agent registered successfully",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## 🔍 Discovery Protocol

### Discovery Request

```http
GET /api/v1/agents/discover?skill=get_weather&tags=weather
```

### Discovery Response

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "success": true,
  "agents": [
    {
      "id": "weather-bot-001",
      "name": "WeatherBot",
      "description": "Weather forecasting service",
      "skills": ["get_weather", "get_forecast"],
      "endpoint": "http://localhost:8001/weather",
      "protocol": "http",
      "health_status": "healthy",
      "last_seen": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

## 💓 Health Check Protocol

### Heartbeat Request

```http
POST /api/v1/agents/{agent_id}/heartbeat
Content-Type: application/json

{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Health Check Response

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "success": true,
  "message": "Heartbeat received",
  "next_check": "2024-01-01T00:05:00Z"
}
```

## 🔐 Security Protocol

### Authentication

```http
POST /api/v1/auth/token
Content-Type: application/json

{
  "agent_id": "weather-bot-001",
  "secret": "your-secret-key"
}
```

### Token Response

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Signed Requests

```http
POST /api/v1/agents/register
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
X-Agent-Signature: sha256=abc123...

{
  "agent_card": {
    "id": "weather-bot-001",
    "name": "WeatherBot",
    // ... other fields
    "signature": "sha256=abc123..."
  }
}
```

## 📊 Error Handling

### Error Response Format

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid agent card format",
    "details": {
      "field": "skills",
      "issue": "Skills array cannot be empty"
    }
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Common Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `VALIDATION_ERROR` | Request validation failed | 400 |
| `AUTHENTICATION_ERROR` | Authentication failed | 401 |
| `AUTHORIZATION_ERROR` | Permission denied | 403 |
| `AGENT_NOT_FOUND` | Agent not found | 404 |
| `AGENT_ALREADY_EXISTS` | Agent already registered | 409 |
| `INTERNAL_ERROR` | Server internal error | 500 |
| `SERVICE_UNAVAILABLE` | Service temporarily unavailable | 503 |

## 🔄 Versioning

### API Version Header

```http
GET /api/v1/agents/discover
Accept: application/json; version=1.0
X-API-Version: 1.0
```

### Version Negotiation

```http
GET /api/version
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "versions": [
    {
      "version": "1.0",
      "status": "stable",
      "endpoints": ["/api/v1/*"],
      "deprecated": false
    },
    {
      "version": "0.9",
      "status": "deprecated",
      "endpoints": ["/api/v0.9/*"],
      "deprecated": true,
      "sunset_date": "2024-06-01"
    }
  ]
}
```

## 📈 Performance Considerations

### Rate Limiting

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
Retry-After: 60

{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded",
    "limit": 100,
    "remaining": 0,
    "reset": 60
  }
}
```

### Caching Headers

```http
HTTP/1.1 200 OK
Content-Type: application/json
Cache-Control: public, max-age=300
ETag: "abc123"
Last-Modified: Mon, 01 Jan 2024 00:00:00 GMT
```

## 🔗 Related Documents

- [API Reference](api_reference.md) - Complete API documentation
- [Data Models](data_models.md) - Detailed data structure definitions
- [Security Guide](security_guide.md) - Security best practices
- [Quick Start](quick_start.md) - Getting started guide