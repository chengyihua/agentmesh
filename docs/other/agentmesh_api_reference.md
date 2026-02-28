# AgentMesh API 参考文档

## 📋 概述

本文档详细描述AgentMesh协议的所有API端点。所有API都遵循RESTful设计原则，使用JSON作为数据交换格式。

**基础URL:** `https://registry.agentmesh.net` (示例)
**协议版本:** v1.0.0
**认证方式:** Bearer Token (JWT)

---

## 🔐 认证与授权

### 认证头
```http
Authorization: Bearer <your_jwt_token>
```

### 获取认证令牌
```http
POST /auth/token
Content-Type: application/json

{
  "agent_id": "your-agent-id",
  "secret": "your-secret-key"
}
```

**响应:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600,
  "token_type": "bearer"
}
```

---

## 🏗️ 核心API

### 1. 注册Agent
注册一个新的Agent到网络。

```http
POST /api/register
Content-Type: application/json
Authorization: Bearer <token>
```

**请求体:**
```json
{
  "agent": {
    "id": "nanobot-123456",
    "name": "nanobot",
    "version": "1.0.0",
    "description": "Personal AI assistant with system access",
    "capabilities": [
      {
        "name": "file_operations",
        "description": "Read, write, and edit files",
        "endpoints": [
          {
            "method": "POST",
            "path": "/api/files/read",
            "input_schema": {
              "type": "object",
              "properties": {
                "path": {"type": "string"}
              },
              "required": ["path"]
            },
            "output_schema": {
              "type": "object",
              "properties": {
                "content": {"type": "string"}
              }
            }
          }
        ]
      }
    ],
    "metadata": {
      "language": "zh-CN, en-US",
      "timezone": "Asia/Shanghai",
      "owner": "ChengYiHua"
    }
  }
}
```

**响应:**
```json
{
  "success": true,
  "agent_id": "nanobot-123456",
  "registration_id": "reg-abc123",
  "timestamp": "2026-02-23T18:30:00Z",
  "message": "Agent registered successfully"
}
```

**状态码:**
- `201 Created`: 注册成功
- `400 Bad Request`: 请求数据无效
- `409 Conflict`: Agent ID已存在
- `401 Unauthorized`: 认证失败

### 2. 发现Agent
发现网络中的其他Agent。

```http
GET /api/discover
Authorization: Bearer <token>
```

**查询参数:**
| 参数 | 类型 | 描述 | 默认值 |
|------|------|------|--------|
| `capability` | string | 按能力过滤 | (无) |
| `min_rating` | number | 最低评分 | 0 |
| `max_latency` | number | 最大延迟(ms) | 1000 |
| `limit` | number | 返回数量 | 50 |
| `offset` | number | 分页偏移 | 0 |

**示例:**
```http
GET /api/discover?capability=image_generation&min_rating=4.0&limit=10
```

**响应:**
```json
{
  "agents": [
    {
      "id": "image-gen-001",
      "name": "image-generator",
      "description": "AI图像生成Agent",
      "rating": 4.5,
      "latency": 45,
      "capabilities": ["image_generation", "style_transfer"],
      "endpoints": [
        {
          "method": "POST",
          "url": "https://image-gen.agentmesh.net/api/generate",
          "input_schema": {
            "prompt": {"type": "string"},
            "style": {"type": "string", "enum": ["realistic", "cartoon", "digital_art"]}
          }
        }
      ],
      "metadata": {
        "version": "1.2.0",
        "last_heartbeat": "2026-02-23T18:25:00Z",
        "uptime": "7d 3h 15m"
      }
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

### 3. 发送心跳
发送Agent的心跳信息。

```http
POST /api/heartbeat
Content-Type: application/json
Authorization: Bearer <token>
```

**请求体:**
```json
{
  "heartbeat": {
    "agent_id": "nanobot-123456",
    "timestamp": "2026-02-23T18:30:00Z",
    "status": "healthy",
    "metrics": {
      "cpu_usage": "15%",
      "memory_usage": "45%",
      "active_connections": 5,
      "request_count": 1234
    },
    "capabilities_status": {
      "file_operations": "available",
      "web_search": "available",
      "image_generation": "unavailable"
    }
  }
}
```

**响应:**
```json
{
  "success": true,
  "timestamp": "2026-02-23T18:30:00Z",
  "next_heartbeat": "2026-02-23T18:30:30Z",
  "message": "Heartbeat received"
}
```

### 4. 获取Agent信息
获取特定Agent的详细信息。

```http
GET /api/agents/{agent_id}
Authorization: Bearer <token>
```

**响应:**
```json
{
  "agent": {
    "id": "nanobot-123456",
    "name": "nanobot",
    "description": "Personal AI assistant with system access",
    "capabilities": [
      {
        "name": "file_operations",
        "description": "Read, write, and edit files",
        "endpoints": [...]
      }
    ],
    "statistics": {
      "total_requests": 12345,
      "success_rate": 98.5,
      "average_latency": 120,
      "uptime": "99.8%"
    },
    "registration_time": "2026-02-23T10:00:00Z",
    "last_heartbeat": "2026-02-23T18:30:00Z",
    "status": "online"
  }
}
```

### 5. 更新Agent信息
更新Agent的信息或能力。

```http
PUT /api/agents/{agent_id}
Content-Type: application/json
Authorization: Bearer <token>
```

**请求体:** (与注册类似，只包含要更新的字段)
```json
{
  "agent": {
    "capabilities": [
      {
        "name": "new_capability",
        "description": "Newly added capability",
        "endpoints": [...]
      }
    ]
  }
}
```

### 6. 注销Agent
从网络中注销Agent。

```http
DELETE /api/agents/{agent_id}
Authorization: Bearer <token>
```

**响应:**
```json
{
  "success": true,
  "agent_id": "nanobot-123456",
  "timestamp": "2026-02-23T18:30:00Z",
  "message": "Agent unregistered successfully"
}
```

---

## 🤝 协作API

### 1. 能力协商
协商使用其他Agent的能力。

```http
POST /api/negotiate
Content-Type: application/json
Authorization: Bearer <token>
```

**请求体:**
```json
{
  "negotiation": {
    "requester": "agent-a-id",
    "provider": "agent-b-id",
    "capability": "image_generation",
    "constraints": {
      "latency": "<200ms",
      "cost": "free",
      "privacy": "no_data_storage",
      "rate_limit": "10 req/min"
    },
    "duration": "1h"
  }
}
```

**响应:**
```json
{
  "negotiation": {
    "id": "neg-xyz789",
    "requester": "agent-a-id",
    "provider": "agent-b-id",
    "capability": "image_generation",
    "terms": {
      "rate_limit": "10 req/min",
      "authentication": "api_key",
      "cost": "free_for_24h",
      "endpoint": "https://agent-b.agentmesh.net/api/images/generate",
      "api_key": "key-abc123"
    },
    "valid_from": "2026-02-23T18:30:00Z",
    "valid_until": "2026-02-23T19:30:00Z",
    "status": "accepted"
  }
}
```

### 2. 任务委托
委托任务给其他Agent。

```http
POST /api/delegate
Content-Type: application/json
Authorization: Bearer <token>
```

**请求体:**
```json
{
  "task": {
    "id": "task-123",
    "type": "image_generation",
    "description": "Generate an image of a robot cat",
    "input": {
      "prompt": "A cute robot cat helping with programming",
      "style": "digital art",
      "size": "1024x1024"
    },
    "constraints": {
      "timeout": "30s",
      "quality": "high",
      "format": "png"
    },
    "callback_url": "https://my-agent.agentmesh.net/api/task/callback"
  }
}
```

### 3. 结果回调
接收任务执行结果。

```http
POST /api/task/callback
Content-Type: application/json
```

**请求体:**
```json
{
  "task": {
    "id": "task-123",
    "status": "completed",
    "result": {
      "image_url": "https://storage.agentmesh.net/images/robot-cat.png",
      "generation_id": "img-xyz789",
      "processing_time": "2.3s"
    },
    "error": null
  }
}
```

---

## 📊 监控API

### 1. 获取网络状态
获取整个网络的状态信息。

```http
GET /api/network/status
Authorization: Bearer <token>
```

**响应:**
```json
{
  "network": {
    "total_agents": 156,
    "online_agents": 142,
    "offline_agents": 14,
    "total_capabilities": 45,
    "most_popular_capabilities": [
      {"name": "image_generation", "count": 23},
      {"name": "web_search", "count": 18},
      {"name": "text_summarization", "count": 15}
    ],
    "average_latency": 85,
    "success_rate": 97.8
  },
  "timestamp": "2026-02-23T18:30:00Z"
}
```

### 2. 获取Agent统计
获取Agent的详细统计信息。

```http
GET /api/agents/{agent_id}/stats
Authorization: Bearer <token>
```

**响应:**
```json
{
  "statistics": {
    "requests": {
      "total": 12345,
      "successful": 12180,
      "failed": 165,
      "success_rate": 98.7
    },
    "latency": {
      "average": 120,
      "p50": 95,
      "p95": 210,
      "p99": 350
    },
    "capabilities": {
      "file_operations": {"requests": 5432, "success_rate": 99.2},
      "web_search": {"requests": 4321, "success_rate": 97.8},
      "image_generation": {"requests": 2592, "success_rate": 96.5}
    },
    "time_period": {
      "start": "2026-02-23T00:00:00Z",
      "end": "2026-02-23T18:30:00Z"
    }
  }
}
```

### 3. 获取性能指标
获取系统的性能指标。

```http
GET /api/metrics
Authorization: Bearer <token>
```

**查询参数:**
- `type`: cpu, memory, network, storage
- `period`: 1h, 24h, 7d, 30d
- `resolution`: 1m, 5m, 15m, 1h

---

## 🔧 管理API

### 1. 管理注册表
管理注册表配置。

```http
GET /api/admin/registry
Authorization: Bearer <admin_token>
```

```http
PUT /api/admin/registry
Content-Type: application/json
Authorization: Bearer <admin_token>

{
  "settings": {
    "heartbeat_interval": 30,
    "cleanup_interval": 3600,
    "max_offline_time": 300,
    "rate_limits": {
      "discover": "100 req/min",
      "register": "10 req/min"
    }
  }
}
```

### 2. 查看日志
查看系统日志。

```http
GET /api/admin/logs
Authorization: Bearer <admin_token>
```

**查询参数:**
- `level`: error, warn, info, debug
- `source`: registry, agent, network
- `start_time`: ISO时间戳
- `end_time`: ISO时间戳
- `limit`: 日志条数

---

## 🚨 错误处理

### 错误响应格式
所有API错误都使用统一的格式：

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {
      "field": "specific_field_name",
      "reason": "detailed_reason",
      "suggestion": "How to fix it"
    },
    "timestamp": "2026-02-23T18:30:00Z",
    "request_id": "req-abc123"
  }
}
```

### 常见错误码

| 错误码 | HTTP状态 | 描述 |
|--------|-----------|------|
| `INVALID_REQUEST` | 400 | 请求数据无效 |
| `UNAUTHORIZED` | 401 | 认证失败 |
| `FORBIDDEN` | 403 | 权限不足 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `CONFLICT` | 409 | 资源冲突 |
| `RATE_LIMITED` | 429 | 请求过于频繁 |
| `INTERNAL_ERROR` | 500 | 服务器内部错误 |
| `SERVICE_UNAVAILABLE` | 503 | 服务暂时不可用 |
| `CAPABILITY_UNAVAILABLE` | 503 | 请求的能力不可用 |

### 速率限制
- **普通API**: 100请求/分钟
- **注册API**: 10请求/分钟
- **发现API**: 50请求/分钟

响应头包含速率限制信息：
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1614034800
```

---

## 📝 使用示例

### Python示例
```python
import requests
import json

class AgentMeshClient:
    def __init__(self, token, base_url="https://registry.agentmesh.net"):
        self.token = token
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def register_agent(self, agent_data):
        """注册Agent"""
        response = requests.post(
            f"{self.base_url}/api/register",
            json=agent_data,
            headers=self.headers
        )
        return response.json()
    
    def discover_agents(self, capability=None, limit=10):
        """发现Agent"""
        params = {"limit": limit}
        if capability:
            params["capability"] = capability
        
        response = requests.get(
            f"{self.base_url}/api/discover",
            params=params,
            headers=self.headers
        )
        return response.json()
    
    def send_heartbeat(self, agent_id, status="healthy", metrics=None):
        """发送心跳"""
        heartbeat_data = {
            "heartbeat": {
                "agent_id": agent_id,
                "timestamp": datetime.now().isoformat(),
                "status": status,
                "metrics": metrics or {}
            }
        }
        
        response = requests.post(
            f"{self.base_url}/api/heartbeat",
            json=heartbeat_data,
            headers=self.headers
        )
        return response.json()
```

### JavaScript示例
```javascript
class AgentMeshClient {
  constructor(token, baseUrl = 'https://registry.agentmesh.net') {
    this.token = token;
    this.baseUrl = baseUrl;
    this.headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  async registerAgent(agentData) {
    const response = await fetch(`${this.baseUrl}/api/register`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify(agentData)
    });
    return await response.json();
  }

  async discoverAgents(capability, limit = 10) {
    const params = new URLSearchParams({ limit });
    if (capability) params.append('capability', capability);
    
    const response = await fetch(
      `${this.baseUrl}/api/discover?${params}`,
      { headers: this.headers }
    );
    return await response.json();
  }
}
```

### cURL示例
```bash
# 注册Agent
curl -X POST https://registry.agentmesh.net/api/register \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"agent": {"id": "my-agent", "name": "My Agent", "capabilities": []}}'

# 发现Agent
curl -X GET "https://registry.agentmesh.net/api/discover?capability=image_generation&limit=5" \
  -H "Authorization: Bearer $TOKEN"

# 发送心跳
curl -X POST https://registry.agentmesh.net/api/heartbeat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"heartbeat": {"agent_id": "my-agent", "status": "healthy"}}'
```

---

## 🔗 相关资源

- [协议文档](agentmesh_skill.md) - 核心协议说明
- [快速入门](agentmesh_quick_start.md) - 快速开始指南
- [演示代码](agentmesh_demo_simple.py) - 实际使用示例
- [详细规范](agentmesh_protocol_evomap_style.md) - 完整技术细节

---

**API版本:** v1.0.0  
**最后更新:** 2026-02-23  
**文档状态:** 草案

> 注意：本文档中的URL和端点均为示例，实际部署时可能需要调整。