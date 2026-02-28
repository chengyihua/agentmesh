# AgentMesh 快速开始指南

5分钟上手 AgentMesh！

## 🚀 安装

### 从 PyPI 安装

```bash
pip install agentmesh-python
```

### 从源码安装

```bash
git clone https://github.com/agentmesh/agentmesh.git
cd agentmesh
pip install -e .
```

## 📦 基本用法

### 1. 启动 AgentMesh 服务器

```bash
# 使用内存存储启动（开发环境）
agentmesh serve --storage memory --port 8000

# 使用 Redis 存储启动（生产环境）
agentmesh serve --storage redis --redis-url redis://localhost:6379 --port 8000
```

### 2. 注册第一个 Agent

```python
import asyncio
from agentmesh import AgentMeshClient
from agentmesh.core.agent_card import AgentCard, Skill, ProtocolType, HealthStatus

async def register_agent():
    # 创建客户端
    client = AgentMeshClient(base_url="http://localhost:8000")
    
    # 创建 Agent 名片
    agent = AgentCard(
        id="weather-bot-001",
        name="WeatherBot",
        version="1.0.0",
        description="天气预测服务",
        skills=[
            Skill(name="get_weather", description="获取当前天气"),
            Skill(name="get_forecast", description="获取天气预报")
        ],
        endpoint="http://localhost:8001/weather",
        protocol=ProtocolType.HTTP,
        tags=["weather", "forecast", "api"],
        health_status=HealthStatus.HEALTHY
    )
    
    # 注册 Agent
    response = await client.register_agent(agent)
    print(f"Agent 已注册: {response['agent_id']}")
    
    # 发送心跳
    await client.send_heartbeat("weather-bot-001")

# 运行
asyncio.run(register_agent())
```

### 3. 发现 Agent

```python
import asyncio
from agentmesh import AgentMeshClient

async def discover_agents():
    client = AgentMeshClient(base_url="http://localhost:8000")
    
    # 按技能发现
    agents = await client.discover_agents(skill_name="get_weather")
    print(f"找到 {len(agents)} 个具有天气技能的 Agent:")
    for agent in agents:
        print(f"  - {agent.name}: {agent.description}")
    
    # 按标签发现
    agents = await client.discover_agents(tags=["api"])
    print(f"找到 {len(agents)} 个具有 API 标签的 Agent")

asyncio.run(discover_agents())
```

### 4. 调用 Agent 服务

```python
import asyncio
import aiohttp
from agentmesh import AgentMeshClient

async def call_agent_service():
    client = AgentMeshClient(base_url="http://localhost:8000")
    
    # 查找天气 Agent
    agents = await client.discover_agents(skill_name="get_weather")
    if not agents:
        print("未找到天气 Agent")
        return
    
    weather_agent = agents[0]
    
    # 调用 Agent 服务
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{weather_agent.endpoint}/current?city=Beijing"
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"北京天气: {data}")
            else:
                print(f"获取天气失败: {response.status}")

asyncio.run(call_agent_service())
```

## 🔧 高级用法

### 使用认证

```python
from agentmesh import AgentMeshClient

# 创建认证客户端
client = AgentMeshClient(
    base_url="http://localhost:8000",
    api_key="your-api-key"
)

# 或使用令牌认证
client = AgentMeshClient(
    base_url="http://localhost:8000",
    token="your-bearer-token"
)
```

### 自定义存储后端

```python
from agentmesh import AgentMeshServer
from agentmesh.storage import RedisStorage

# 创建自定义存储
storage = RedisStorage(
    url="redis://localhost:6379",
    prefix="agentmesh:"
)

# 使用自定义存储启动服务器
server = AgentMeshServer(storage=storage)
server.run(port=8000)
```

### 健康检查配置

```python
from agentmesh import AgentMeshClient

client = AgentMeshClient(
    base_url="http://localhost:8000",
    health_check_interval=60,  # 每60秒检查一次
    health_check_timeout=10    # 10秒后超时
)

# 手动检查 Agent 健康状态
health = await client.check_agent_health("weather-bot-001")
print(f"Agent 健康状态: {health}")
```

## 📚 示例

查看 `examples/` 目录获取更多完整示例：

```bash
# 运行基础示例
python examples/basic_example.py

# 运行认证示例
python examples/auth_example.py

# 运行多 Agent 示例
python examples/multi_agent_example.py
```

## 🔍 监控

### 检查服务器状态

```bash
# 检查服务器健康状态
curl http://localhost:8000/health

# 获取服务器统计信息
curl http://localhost:8000/api/v1/stats
```

### 查看已注册的 Agent

```bash
# 列出所有 Agent
curl http://localhost:8000/api/v1/agents

# 获取 Agent 详情
curl http://localhost:8000/api/v1/agents/weather-bot-001
```

## 🐛 故障排除

### 常见问题

1. **连接被拒绝**
   ```bash
   # 确保服务器正在运行
   agentmesh serve --storage memory --port 8000
   ```

2. **Agent 未找到**
   ```bash
   # 检查 Agent 是否已注册
   curl http://localhost:8000/api/v1/agents/weather-bot-001
   ```

3. **认证失败**
   ```python
   # 检查 API 密钥或令牌
   client = AgentMeshClient(base_url="...", api_key="correct-key")
   ```

### 启用调试日志

```python
import logging

# 启用调试日志
logging.basicConfig(level=logging.DEBUG)

# 或针对特定模块
logging.getLogger("agentmesh").setLevel(logging.DEBUG)
```

## 📖 下一步

1. 阅读 [协议规范](protocol_specification_zh.md) 了解细节
2. 查看 [API 参考](api_reference_zh.md) 获取所有可用端点
3. 探索 [最佳实践](best_practices_zh.md) 进行生产部署
4. 加入 [社区](https://github.com/agentmesh/agentmesh/discussions) 获取帮助和讨论

## 🆘 需要帮助？

- [GitHub Issues](https://github.com/agentmesh/agentmesh/issues) - 报告错误或请求功能
- [文档](https://agentmesh.io/docs) - 完整文档
- [Discord](https://discord.gg/agentmesh) - 社区支持（即将上线）