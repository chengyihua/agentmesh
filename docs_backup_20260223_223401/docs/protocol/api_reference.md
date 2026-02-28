# AgentMesh API Reference

Complete reference for all AgentMesh API endpoints.

## 📋 Base URL

All API endpoints are relative to the base URL:

```
http://localhost:8000/api/v1
```

## 🔐 Authentication

### API Key Authentication

```http
GET /agents
X-API-Key: your-api-key
```

### Bearer Token Authentication

```http
GET /agents
Authorization: Bearer your-bearer-token
```

## 📊 Response Format

All API responses follow this format:

```json
{
  "success": true,
  "data": { /* response data */ },
  "message": "Operation successful",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

Error responses:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error description",
    "details": { /* additional details */ }
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## 📡 Agent Management

### Register an Agent

Register a new agent in the AgentMesh network.

```http
POST /agents/register
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
    "tags": ["weather", "forecast", "api"],
    "health_status": "healthy"
  }
}
```

**Response:**

```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "success": true,
  "data": {
    "agent_id": "weather-bot-001",
    "registered_at": "2024-01-01T00:00:00Z"
  },
  "message": "Agent registered successfully"
}
```

### Get Agent Details

Get detailed information about a specific agent.

```http
GET /agents/{agent_id}
```

**Response:**

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "success": true,
  "data": {
    "agent": {
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
      "tags": ["weather", "forecast", "api"],
      "health_status": "healthy",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "last_seen": "2024-01-01T00:00:00Z"
    }
  }
}
```

### Update Agent Information

Update an existing agent's information.

```http
PUT /agents/{agent_id}
Content-Type: application/json

{
  "update": {
    "description": "Updated weather service with 7-day forecast",
    "skills": [
      {
        "name": "get_weather",
        "description": "Get current weather"
      },
      {
        "name": "get_forecast",
        "description": "Get 7-day weather forecast"
      }
    ],
    "tags": ["weather", "forecast", "api", "extended"]
  }
}
```

**Response:**

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "success": true,
  "data": {
    "agent_id": "weather-bot-001",
    "updated_at": "2024-01-01T00:01:00Z"
  },
  "message": "Agent updated successfully"
}
```

### Deregister an Agent

Remove an agent from the AgentMesh network.

```http
DELETE /agents/{agent_id}
```

**Response:**

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "success": true,
  "data": {
    "agent_id": "weather-bot-001",
    "deregistered_at": "2024-01-01T00:02:00Z"
  },
  "message": "Agent deregistered successfully"
}
```

## 🔍 Discovery

### Discover Agents

Discover agents based on various criteria.

```http
GET /agents/discover
```

**Query Parameters:**

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `skill` | string | Filter by skill name | `skill=get_weather` |
| `tags` | string[] | Filter by tags | `tags=weather&tags=api` |
| `protocol` | string | Filter by protocol | `protocol=http` |
| `health_status` | string | Filter by health status | `health_status=healthy` |
| `limit` | integer | Maximum number of results | `limit=10` |
| `offset` | integer | Pagination offset | `offset=0` |

**Example Request:**

```http
GET /agents/discover?skill=get_weather&tags=weather&limit=5
```

**Response:**

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "success": true,
  "data": {
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
    "limit": 5,
    "offset": 0
  }
}
```

### Search Agents

Full-text search across agent names, descriptions, and skills.

```http
GET /agents/search?q={query}
```

**Example Request:**

```http
GET /agents/search?q=weather+forecast
```

**Response:**

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "success": true,
  "data": {
    "results": [
      {
        "id": "weather-bot-001",
        "name": "WeatherBot",
        "description": "Weather forecasting service",
        "score": 0.95,
        "matched_fields": ["name", "description"]
      }
    ],
    "total": 1
  }
}
```

## 💓 Health Management

### Send Heartbeat

Update agent's health status and last seen timestamp.

```http
POST /agents/{agent_id}/heartbeat
Content-Type: application/json

{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

**Response:**

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "success": true,
  "data": {
    "agent_id": "weather-bot-001",
    "next_check": "2024-01-01T00:05:00Z"
  },
  "message": "Heartbeat received"
}
```

### Check Agent Health

Get current health status of an agent.

```http
GET /agents/{agent_id}/health
```

**Response:**

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "success": true,
  "data": {
    "agent_id": "weather-bot-001",
    "health_status": "healthy",
    "last_heartbeat": "2024-01-01T00:00:00Z",
    "next_check": "2024-01-01T00:05:00Z",
    "uptime": "24h 30m 15s"
  }
}
```

### Bulk Health Check

Check health status of multiple agents.

```http
POST /agents/health/check
Content-Type: application/json

{
  "agent_ids": ["weather-bot-001", "translation-bot-001"]
}
```

**Response:**

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "success": true,
  "data": {
    "results": [
      {
        "agent_id": "weather-bot-001",
        "health_status": "healthy",
        "last_seen": "2024-01-01T00:00:00Z"
      },
      {
        "agent_id": "translation-bot-001",
        "health_status": "unhealthy",
        "last_seen": "2024-01-01T23:55:00Z",
        "reason": "No heartbeat for 5 minutes"
      }
    ]
  }
}
```

## 📊 Statistics

### Get System Statistics

Get overall system statistics.

```http
GET /stats
```

**Response:**

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "success": true,
  "data": {
    "total_agents": 42,
    "total_skills": 156,
    "healthy_agents": 38,
    "unhealthy_agents": 3,
    "unknown_agents": 1,
    "uptime": "7d 12h 30m",
    "requests_per_minute": 125.5,
    "storage_backend": "redis",
    "version": "1.0.0"
  }
}
```

### Get Agent Statistics

Get statistics for a specific agent.

```http
GET /agents/{agent_id}/stats
```

**Response:**

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "success": true,
  "data": {
    "agent_id": "weather-bot-001",
    "registered_at": "2024-01-01T00:00:00Z",
    "total_requests": 1250,
    "successful_requests": 1240,
    "failed_requests": 10,
    "average_response_time": 125.5,
    "availability": 99.2,
    "last_30_days": [
      {
        "date": "2024-01-01",
        "requests": 42,
        "success_rate": 100.0
      }
    ]
  }
}
```

## 🔐 Authentication & Authorization

### Get API Token

```http
POST /auth/token
Content-Type: application/json

{
  "agent_id": "weather-bot-001",
  "secret": "your-secret-key"
}
```

**Response:**

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600,
    "refresh_token": "def456..."
  }
}
```

### Refresh Token

```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "def456..."
}
```

**Response:**

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

### Verify Token

```http
GET /auth/verify
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "success": true,
  "data": {
    "valid": true,
    "agent_id": "weather-bot-001",
    "expires_at": "2024-01-01T01:00:00Z"
  }
}
```

## 🛠️ System Management

### Health Check

Check if the AgentMesh server is healthy.

```http
GET /health
```

**Response:**

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2024-01-01T00:00:00Z",
    "version": "1.0.0",
    "uptime": "7d 12h 30m"
  }
}
```

### Get Version Information

```http
GET /version
```

**Response:**

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "success": true,
  "data": {
    "version": "1.0.0",
    "build_date": "2024-01-01T00:00:00Z",
    "git_commit": "abc123def456",
    "api_version": "v1",
    "supported_protocols": ["http", "websocket", "grpc", "mcp"]
  }
}
```

### Clear Cache

Clear the agent discovery cache.

```http
POST /cache/clear
Authorization: Bearer admin-token
```

**Response:**

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "success": true,
  "data": {
    "cleared_at": "2024-01-01T00:00:00Z",
    "cache_size": "15.2MB"
  },
  "message": "Cache cleared successfully"
}
```

## 📝 Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `VALIDATION_ERROR` | Request validation failed |
| 401 | `AUTHENTICATION_ERROR` | Authentication failed |
| 403 | `AUTHORIZATION_ERROR` | Permission denied |
| 404 | `AGENT_NOT_FOUND` | Agent not found |
| 409 | `AGENT_ALREADY_EXISTS` | Agent already registered |
| 429 | `RATE_LIMIT_EXCEEDED` | Rate limit exceeded |
| 500 | `INTERNAL_ERROR` | Server internal error |
| 503 | `SERVICE_UNAVAILABLE` | Service temporarily unavailable |

## 🔗 Related Documents

- [Protocol Specification](protocol_specification.md) - Complete protocol details
- [Quick Start Guide](quick_start.md) - Getting started guide
- [Data Models](data_models.md) - Data structure definitions