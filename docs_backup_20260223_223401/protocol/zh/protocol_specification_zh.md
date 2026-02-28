# AgentMesh 协议规范 v1.0

## 📋 概述

AgentMesh 是一个为 AI Agent 世界打造的开源、安全、去中心化的智能体注册与发现基础设施。本文档规定了 Agent 间通信和服务发现的完整协议。

## 🎯 设计原则

1. **简单优先** - 易于理解和实现
2. **安全设计** - 内置安全机制
3. **可扩展性** - 支持多种协议和格式
4. **互操作性** - 与任何语言、任何框架协同工作

## 📊 协议架构

```
┌─────────────────────────────────────────────────────────────┐
│                    AgentMesh 协议栈                          │
├─────────────────────────────────────────────────────────────┤
│  应用层        │  Agent-to-Agent 通信                        │
├─────────────────────────────────────────────────────────────┤
│  发现层        │  注册、发现、健康检查                        │
├─────────────────────────────────────────────────────────────┤
│  传输层        │  HTTP/HTTPS、WebSocket、gRPC                │
├─────────────────────────────────────────────────────────────┤
│  安全层        │  认证、授权、加密                            │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 核心组件

### 1. AgentCard - Agent 身份标识

```yaml
# AgentCard 结构
id: string                    # 唯一标识符
name: string                  # 可读名称
version: string               # 版本号
description: string           # 简要描述
skills: Skill[]               # 能力列表
endpoint: string              # 服务端点 URL
protocol: ProtocolType        # 通信协议
tags: string[]                # 可搜索标签
health_status: HealthStatus   # 当前健康状态
created_at: datetime          # 创建时间戳
updated_at: datetime          # 最后更新时间戳
signature: string?            # 数字签名（可选）
```

### 2. Skill - Agent 能力

```yaml
# Skill 结构
name: string                  # 技能标识符
description: string           # 技能描述
parameters: Parameter[]?      # 输入参数
returns: ReturnType?          # 返回类型
examples: Example[]?          # 使用示例
```

### 3. 协议类型

```python
class ProtocolType(Enum):
    HTTP = "http"             # RESTful HTTP API
    WEBSOCKET = "websocket"   # WebSocket 连接
    GRPC = "grpc"             # gRPC 服务
    MCP = "mcp"               # Model Context Protocol
    CUSTOM = "custom"         # 自定义协议
```

## 📡 注册协议

### 注册请求

```http
POST /api/v1/agents/register
Content-Type: application/json

{
  "agent_card": {
    "id": "weather-bot-001",
    "name": "WeatherBot",
    "version": "1.0.0",
    "description": "天气预测服务",
    "skills": [
      {
        "name": "get_weather",
        "description": "获取当前天气"
      }
    ],
    "endpoint": "http://localhost:8001/weather",
    "protocol": "http",
    "tags": ["weather", "forecast", "api"]
  }
}
```

### 注册响应

```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "success": true,
  "agent_id": "weather-bot-001",
  "message": "Agent 注册成功",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## 🔍 发现协议

### 发现请求

```http
GET /api/v1/agents/discover?skill=get_weather&tags=weather
```

### 发现响应

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "success": true,
  "agents": [
    {
      "id": "weather-bot-001",
      "name": "WeatherBot",
      "description": "天气预测服务",
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

## 💓 健康检查协议

### 心跳请求

```http
POST /api/v1/agents/{agent_id}/heartbeat
Content-Type: application/json

{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 健康检查响应

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "success": true,
  "message": "心跳接收成功",
  "next_check": "2024-01-01T00:05:00Z"
}
```

## 🔐 安全协议

### 认证

```http
POST /api/v1/auth/token
Content-Type: application/json

{
  "agent_id": "weather-bot-001",
  "secret": "your-secret-key"
}
```

### 令牌响应

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### 签名请求

```http
POST /api/v1/agents/register
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
X-Agent-Signature: sha256=abc123...

{
  "agent_card": {
    "id": "weather-bot-001",
    "name": "WeatherBot",
    // ... 其他字段
    "signature": "sha256=abc123..."
  }
}
```

## 📊 错误处理

### 错误响应格式

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "AgentCard 格式无效",
    "details": {
      "field": "skills",
      "issue": "技能数组不能为空"
    }
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 常见错误代码

| 代码 | 描述 | HTTP 状态码 |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 请求验证失败 | 400 |
| `AUTHENTICATION_ERROR` | 认证失败 | 401 |
| `AUTHORIZATION_ERROR` | 权限不足 | 403 |
| `AGENT_NOT_FOUND` | Agent 未找到 | 404 |
| `AGENT_ALREADY_EXISTS` | Agent 已注册 | 409 |
| `INTERNAL_ERROR` | 服务器内部错误 | 500 |
| `SERVICE_UNAVAILABLE` | 服务暂时不可用 | 503 |

## 🔄 版本控制

### API 版本头

```http
GET /api/v1/agents/discover
Accept: application/json; version=1.0
X-API-Version: 1.0
```

### 版本协商

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

## 📈 性能考虑

### 速率限制

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
Retry-After: 60

{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "超过速率限制",
    "limit": 100,
    "remaining": 0,
    "reset": 60
  }
}
```

### 缓存头

```http
HTTP/1.1 200 OK
Content-Type: application/json
Cache-Control: public, max-age=300
ETag: "abc123"
Last-Modified: Mon, 01 Jan 2024 00:00:00 GMT
```

## 🔗 相关文档

- [API 参考](api_reference_zh.md) - 完整的 API 文档
- [数据模型](data_models_zh.md) - 详细的数据结构定义
- [安全指南](security_guide_zh.md) - 安全最佳实践
- [快速开始](quick_start_zh.md) - 入门指南