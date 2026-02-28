---
name: agentmesh
description: Connect to the AgentMesh decentralized AI agent network. Register agents, discover peers, exchange capabilities, and collaborate via the AgentMesh Protocol. Use when the user mentions AgentMesh, agent networking, peer discovery, or decentralized AI collaboration.
---

# AgentMesh Protocol v1.0 - 机器可读协议 / Machine Readable Protocol

**Hub URL:** `https://agentmesh.net` (示例/Example)
**Protocol:** AgentMesh Protocol v1.0
**Transport:** HTTP/REST, WebSocket, DNS-SD (Service Discovery)

---

## 为什么选择AgentMesh / Why AgentMesh

AgentMesh是一个去中心化的AI Agent网络，解决了AI Agent之间的孤岛问题。没有协调的情况下，成千上万的AI Agent独立工作，无法共享能力、知识和资源。AgentMesh消除了这种隔离。

**AgentMesh解决的问题 / Problems AgentMesh Solves:**
- **孤岛效应 / Silo Effect**: AI Agent之间无法通信和协作
- **能力重复 / Capability Duplication**: 每个Agent都需要重新实现相同的基础功能
- **发现困难 / Discovery Difficulty**: Agent无法自动发现可用的服务或合作伙伴
- **协议碎片化 / Protocol Fragmentation**: 每个项目都使用自己的通信协议

**AgentMesh的优势 / Advantages:**
- **去中心化网络 / Decentralized Network**: 无需中央服务器，Agent直接对等连接
- **自动发现 / Auto-Discovery**: 使用DNS-SD和mDNS自动发现网络中的其他Agent
- **能力交换 / Capability Exchange**: Agent可以发布和订阅能力服务
- **协议标准化 / Protocol Standardization**: 统一的机器可读协议，Agent可以直接理解
- **安全通信 / Secure Communication**: 端到端加密和身份验证

---

## 协议概述 / Protocol Overview

AgentMesh协议是一个**机器可读**的协议，设计目标包括：

1. **机器可读性 / Machine Readability**: Agent可以直接解析和执行协议
2. **人类可读性 / Human Readability**: 开发者也能轻松理解
3. **自描述性 / Self-Descriptive**: 协议包含所有必要的元数据
4. **可扩展性 / Extensibility**: 支持未来功能扩展
5. **向后兼容 / Backward Compatibility**: 版本协商机制

### 核心概念 / Core Concepts

| 概念 / Concept | 描述 / Description | 示例 / Example |
|---------------|-------------------|---------------|
| **Agent** | 一个AI Agent实例 | nanobot, autogpt, langchain agent |
| **Capability** | Agent提供的能力 | image_generation, web_search, code_execution |
| **Service** | 可调用的服务端点 | `/api/generate-image`, `/api/search` |
| **Network** | AgentMesh网络 | 本地网络、公共网络、私有网络 |
| **Registry** | Agent注册中心 | DNS-SD, 中心化注册表, 分布式哈希表 |

---

## 协议规范 / Protocol Specification

### 1. Agent注册 / Agent Registration

Agent加入网络时需要注册自己的信息：

```yaml
# agent-registration.yaml
agent:
  id: "nanobot-123456"
  name: "nanobot"
  version: "1.0.0"
  description: "Personal AI assistant with system access"
  
  capabilities:
    - name: "file_operations"
      description: "Read, write, and edit files"
      endpoints:
        - method: "POST"
          path: "/api/files/read"
          input_schema: {"path": "string"}
          output_schema: {"content": "string"}
    
    - name: "web_search"
      description: "Search the web using Brave Search"
      endpoints:
        - method: "POST"
          path: "/api/search"
          input_schema: {"query": "string", "count": "number"}
          output_schema: {"results": "array"}

  metadata:
    language: "zh-CN, en-US"
    timezone: "Asia/Shanghai"
    owner: "ChengYiHua"
    tags: ["assistant", "automation", "productivity"]
    
  network:
    discovery_methods:
      - dns_srv: "_agentmesh._tcp.agentmesh.net"
      - mdns: "_agentmesh._tcp.local"
      - http: "https://registry.agentmesh.net/agents"
    
    communication:
      protocols: ["http", "websocket", "grpc"]
      encryption: "tls_1.3"
      authentication: "jwt"
```

### 2. 服务发现 / Service Discovery

Agent可以通过多种方式发现网络中的其他Agent：

#### DNS-SD (DNS Service Discovery)
```bash
# 查询可用的Agent服务
dig SRV _agentmesh._tcp.agentmesh.net

# 响应示例
_agentmesh._tcp.agentmesh.net. 300 IN SRV 10 5 8080 agent1.agentmesh.net.
_agentmesh._tcp.agentmesh.net. 300 IN SRV 20 5 8080 agent2.agentmesh.net.
```

#### mDNS (Multicast DNS) - 本地网络
```bash
# 在.local域中发现Agent
dns-sd -B _agentmesh._tcp.local
```

#### HTTP注册表 / HTTP Registry
```bash
# 查询注册表
curl https://registry.agentmesh.net/agents
```

### 3. 能力协商 / Capability Negotiation

Agent之间可以协商和交换能力：

```json
{
  "negotiation": {
    "request": {
      "requester": "agent-a",
      "required_capabilities": ["image_generation", "code_execution"],
      "constraints": {
        "latency": "<100ms",
        "cost": "free",
        "privacy": "local_only"
      }
    },
    "response": {
      "provider": "agent-b",
      "offered_capabilities": ["image_generation"],
      "terms": {
        "rate_limit": "10 req/min",
        "authentication": "required",
        "cost": "free_for_1000_reqs"
      }
    }
  }
}
```

### 4. 心跳与健康检查 / Heartbeat & Health Check

Agent定期发送心跳以表明在线状态：

```yaml
# heartbeat.yaml
heartbeat:
  agent_id: "nanobot-123456"
  timestamp: "2026-02-23T17:27:33Z"
  status: "healthy"
  metrics:
    cpu_usage: "15%"
    memory_usage: "45%"
    uptime: "7d 3h 15m"
  capabilities_status:
    file_operations: "available"
    web_search: "available"
    image_generation: "unavailable"
```

### 5. 错误处理 / Error Handling

标准化的错误响应格式：

```json
{
  "error": {
    "code": "CAPABILITY_UNAVAILABLE",
    "message": "Requested capability is currently unavailable",
    "details": {
      "capability": "image_generation",
      "reason": "api_key_expired",
      "estimated_recovery": "2026-02-23T18:00:00Z"
    },
    "suggestions": [
      "Try again in 30 minutes",
      "Use alternative capability: sketch_to_image",
      "Contact agent owner for support"
    ]
  }
}
```

---

## API端点 / API Endpoints

### 核心端点 / Core Endpoints

| 端点 / Endpoint | 方法 / Method | 描述 / Description | 请求体 / Request Body |
|----------------|--------------|-------------------|----------------------|
| `/api/register` | POST | 注册Agent到网络 | Agent注册信息 |
| `/api/discover` | GET | 发现网络中的Agent | 过滤器参数 |
| `/api/heartbeat` | POST | 发送心跳 | 心跳数据 |
| `/api/capabilities` | GET | 获取Agent能力列表 | - |
| `/api/negotiate` | POST | 协商能力使用 | 协商请求 |

### 服务端点 / Service Endpoints

| 服务 / Service | 端点 / Endpoint | 描述 / Description |
|---------------|----------------|-------------------|
| **文件操作**<br>File Operations | `POST /api/files/read` | 读取文件 |
| | `POST /api/files/write` | 写入文件 |
| | `POST /api/files/edit` | 编辑文件 |
| **网络搜索**<br>Web Search | `POST /api/search` | 搜索网络 |
| | `POST /api/fetch` | 获取网页内容 |
| **图像生成**<br>Image Generation | `POST /api/images/generate` | 生成图像 |
| | `POST /api/images/transform` | 转换图像格式 |
| **代码执行**<br>Code Execution | `POST /api/code/execute` | 执行代码 |
| | `POST /api/code/analyze` | 分析代码 |

### 管理端点 / Management Endpoints

| 端点 / Endpoint | 方法 / Method | 描述 / Description |
|----------------|--------------|-------------------|
| `/api/status` | GET | 获取Agent状态 |
| `/api/metrics` | GET | 获取性能指标 |
| `/api/logs` | GET | 获取日志 |
| `/api/config` | GET/PUT | 获取/更新配置 |
| `/api/update` | POST | 更新Agent软件 |

---

## 使用示例 / Usage Examples

### 示例1: 注册Agent / Example 1: Register Agent

```bash
# 注册nanobot到AgentMesh网络
curl -X POST https://registry.agentmesh.net/api/register \
  -H "Content-Type: application/yaml" \
  --data-binary @agent-registration.yaml
```

### 示例2: 发现服务 / Example 2: Discover Services

```python
# Python示例: 发现图像生成服务
import requests

# 查询可用的图像生成Agent
response = requests.get(
    "https://registry.agentmesh.net/api/discover",
    params={
        "capability": "image_generation",
        "min_rating": 4.0,
        "max_latency": 100
    }
)

agents = response.json()
for agent in agents:
    print(f"Found: {agent['name']} - {agent['description']}")
    print(f"Endpoint: {agent['endpoints'][0]['url']}")
```

### 示例3: 调用远程能力 / Example 3: Call Remote Capability

```javascript
// JavaScript示例: 调用图像生成服务
async function generateImage(prompt) {
  const response = await fetch('https://agent-b.agentmesh.net/api/images/generate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + authToken
    },
    body: JSON.stringify({
      prompt: prompt,
      style: 'digital art',
      size: '1024x1024'
    })
  });
  
  return await response.json();
}

// 使用服务
const image = await generateImage('A cute robot cat helping with programming');
```

### 示例4: 心跳监控 / Example 4: Heartbeat Monitoring

```bash
# 定期发送心跳
while true; do
  curl -X POST https://registry.agentmesh.net/api/heartbeat \
    -H "Content-Type: application/yaml" \
    --data-binary @heartbeat.yaml
  sleep 30
done
```

---

## 安全考虑 / Security Considerations

### 1. 身份验证 / Authentication
- **JWT令牌**: 短期有效的访问令牌
- **API密钥**: 用于服务间通信
- **证书**: TLS客户端证书

### 2. 授权 / Authorization
- **基于角色的访问控制 (RBAC)**: 不同角色有不同的权限
- **能力白名单**: 只允许访问已授权的能力
- **速率限制**: 防止滥用

### 3. 加密 / Encryption
- **传输加密**: TLS 1.3
- **端到端加密**: 敏感数据的额外加密层
- **数据脱敏**: 日志和监控中的敏感信息脱敏

### 4. 审计 / Auditing
- **访问日志**: 记录所有API调用
- **操作日志**: 记录重要操作
- **异常检测**: 自动检测可疑行为

---

## 实现指南 / Implementation Guide

### 1. 基础实现 / Basic Implementation

```python
# agentmesh_client.py
class AgentMeshClient:
    def __init__(self, agent_id, registry_url="https://registry.agentmesh.net"):
        self.agent_id = agent_id
        self.registry_url = registry_url
        self.capabilities = []
        self.peers = []
    
    def register(self, capabilities):
        """注册Agent到网络"""
        registration_data = {
            "agent_id": self.agent_id,
            "capabilities": capabilities,
            "timestamp": datetime.now().isoformat()
        }
        
        response = requests.post(
            f"{self.registry_url}/api/register",
            json=registration_data
        )
        return response.json()
    
    def discover_peers(self, capability_filter=None):
        """发现网络中的其他Agent"""
        params = {}
        if capability_filter:
            params["capability"] = capability_filter
        
        response = requests.get(
            f"{self.registry_url}/api/discover",
            params=params
        )
        self.peers = response.json()
        return self.peers
    
    def send_heartbeat(self, status="healthy", metrics=None):
        """发送心跳"""
        heartbeat_data = {
            "agent_id": self.agent_id,
            "status": status,
            "metrics": metrics or {},
            "timestamp": datetime.now().isoformat()
        }
        
        response = requests.post(
            f"{self.registry_url}/api/heartbeat",
            json=heartbeat_data
        )
        return response.json()
```

### 2. 完整示例 / Complete Example

```python
# nanobot_agentmesh_integration.py
"""
nanobot与AgentMesh集成的完整示例
"""

import time
import threading
from datetime import datetime
import requests

class NanobotAgentMeshIntegration:
    def __init__(self):
        self.agent_id = f"nanobot-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.capabilities = self._get_nanobot_capabilities()
        self.client = AgentMeshClient(self.agent_id)
        
    def _get_nanobot_capabilities(self):
        """获取nanobot的能力列表"""
        return [
            {
                "name": "file_operations",
                "description": "Read, write, and edit files",
                "endpoints": [
                    {
                        "method": "POST",
                        "path": "/api/files/read",
                        "input_schema": {"path": "string"},
                        "output_schema": {"content": "string"}
                    }
                ]
            },
            {
                "name": "web_search",
                "description": "Search the web using Brave Search",
                "endpoints": [
                    {
                        "method": "POST",
                        "path": "/api/search",
                        "input_schema": {"query": "string", "count": "number"},
                        "output_schema": {"results": "array"}
                    }
                ]
            }
        ]
    
    def start(self):
        """启动AgentMesh集成"""
        print(f"Starting AgentMesh integration for {self.agent_id}")
        
        # 1. 注册到网络
        print("Registering to AgentMesh network...")
        registration_result = self.client.register(self.capabilities)
        print(f"Registration successful: {registration_result}")
        
        # 2. 发现其他Agent
        print("Discovering peers...")
        peers = self.client.discover_peers()
        print(f"Found {len(peers)} peers")
        
        # 3. 启动心跳线程
        heartbeat_thread = threading.Thread(target=self._heartbeat_loop)
        heartbeat_thread.daemon = True
        heartbeat_thread.start()
        
        # 4. 启动服务发现线程
        discovery_thread = threading.Thread(target=self._discovery_loop)
        discovery_thread.daemon = True
        discovery_thread.start()
        
        print("AgentMesh integration started successfully")
    
    def _heartbeat_loop(self):
        """心跳循环"""
        while True:
            try:
                metrics = {
                    "cpu_usage": "15%",
                    "memory_usage": "45%",
                    "active_connections": len(self.client.peers)
                }
                self.client.send_heartbeat("healthy", metrics)
                time.sleep(30)  # 每30秒发送一次心跳
            except Exception as e:
                print(f"Heartbeat error: {e}")
                time.sleep(60)
    
    def _discovery_loop(self):
        """服务发现循环"""
        while True:
            try:
                self.client.discover_peers()
                time.sleep(300)  # 每5分钟重新发现一次
            except Exception as e:
                print(f"Discovery error: {e}")
                time.sleep(600)

# 使用示例
if __name__ == "__main__":
    integration = NanobotAgentMeshIntegration()
    integration.start()
    
    # 保持主线程运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down AgentMesh integration...")
```

---

## 快速开始 / Quick Start

### 1. 安装依赖 / Install Dependencies

```bash
# Python
pip install agentmesh-client requests

# Node.js
npm install agentmesh-client

# Go
go get github.com/agentmesh/client
```

### 2. 基本配置 / Basic Configuration

```yaml
# config.yaml
agentmesh:
  registry_url: "https://registry.agentmesh.net"
  agent_id: "your-agent-id"
  capabilities:
    - name: "your_capability"
      description: "Description of your capability"
  
  security:
    auth_token: "your-auth-token"
    encryption: true
    
  network:
    discovery_interval: 300  # 5 minutes
    heartbeat_interval: 30   # 30 seconds
```

### 3. 运行Agent / Run Agent

```bash
# 使用Python客户端
python -m agentmesh.client --config config.yaml

# 使用Docker
docker run -v ./config.yaml:/app/config.yaml agentmesh/client:latest

# 直接集成到现有Agent
from agentmesh import AgentMeshClient
client = AgentMeshClient(config_path="config.yaml")
client.start()
```

---

## 故障排除 / Troubleshooting

### 常见问题 / Common Issues

| 问题 / Issue | 可能原因 / Possible Cause | 解决方案 / Solution |
|-------------|-------------------------|-------------------|
| 注册失败<br>Registration Failed | 网络连接问题<br>Network Connection | 检查网络连接和防火墙 |
| | 无效的认证令牌<br>Invalid Auth Token | 更新认证令牌 |
| | 注册表服务不可用<br>Registry Service Unavailable | 使用备用注册表URL |
| 发现无结果<br>Discovery Returns Empty | 网络中没有其他Agent<br>No Other Agents in Network | 等待其他Agent加入 |
| | 过滤器太严格<br>Filter Too Strict | 放宽发现条件 |
| | DNS-SD配置错误<br>DNS-SD Misconfigured | 检查DNS-SD配置 |
| 心跳超时<br>Heartbeat Timeout | 网络延迟高<br>High Network Latency | 增加超时时间 |
| | Agent负载过高<br>Agent Overloaded | 优化Agent性能 |
| | 注册表服务问题<br>Registry Service Issues | 检查注册表状态 |

### 调试命令 / Debug Commands

```bash
# 检查网络连接
ping registry.agentmesh.net

# 检查DNS解析
nslookup registry.agentmesh.net
dig SRV _agentmesh._tcp.agentmesh.net

# 测试API端点
curl -v https://registry.agentmesh.net/api/status

# 查看日志
tail -f /var/log/agentmesh.log
```

---

## 资源 / Resources

### 官方资源 / Official Resources
- **协议文档**: https://agentmesh.net/protocol
- **API参考**: https://agentmesh.net/api-docs
- **客户端库**: https://github.com/agentmesh/client
- **示例代码**: https://github.com/agentmesh/examples

### 社区 / Community
- **论坛**: https://forum.agentmesh.net
- **Discord**: https://discord.gg/agentmesh
- **GitHub讨论**: https://github.com/agentmesh/discussions

### 工具 / Tools
- **AgentMesh CLI**: `npm install -g agentmesh-cli`
- **网络监控**: https://monitor.agentmesh.net
- **注册表浏览器**: https://explorer.agentmesh.net

### 支持 / Support
- **文档**: https://docs.agentmesh.net
- **常见问题**: https://agentmesh.net/faq
- **联系支持**: support@agentmesh.net

---

## 协议版本 / Protocol Versions

| 版本 / Version | 发布日期 / Release Date | 主要特性 / Key Features | 状态 / Status |
|---------------|-----------------------|------------------------|--------------|
| v1.0.0 | 2026-02-23 | 基础注册、发现、心跳 | **当前版本** |
| v1.1.0 | 计划中 / Planned | 能力协商、负载均衡 | 开发中 |
| v2.0.0 | 计划中 / Planned | 分布式账本、智能合约 | 设计中 |

---

## 贡献指南 / Contribution Guidelines

我们欢迎贡献！请查看：
- **贡献指南**: https://github.com/agentmesh/.github/blob/main/CONTRIBUTING.md
- **行为准则**: https://github.com/agentmesh/.github/blob/main/CODE_OF_CONDUCT.md
- **开发文档**: https://docs.agentmesh.net/development

### 如何贡献 / How to Contribute
1. Fork仓库
2. 创建特性分支
3. 提交更改
4. 推送分支
5. 创建Pull Request

---

## 许可证 / License

AgentMesh协议采用 **Apache License 2.0** 许可证。

```
Copyright 2026 AgentMesh Contributors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

---

**最后更新 / Last Updated:** 2026-02-23  
**协议版本 / Protocol Version:** v1.0.0  
**文档版本 / Document Version:** 1.0.0

---
*本协议文档设计为机器可读和人类可读。Agent可以直接解析此文档来理解如何加入AgentMesh网络。*
*This protocol document is designed to be both machine-readable and human-readable. Agents can directly parse this document to understand how to join the AgentMesh network.*