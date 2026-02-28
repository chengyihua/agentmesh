# AgentMesh 快速入门指南

## 🚀 5分钟开始使用AgentMesh协议

### 第1步：了解核心概念（1分钟）

AgentMesh协议的核心很简单：
1. **Agent** - 你的AI助手（如nanobot）
2. **能力** - Agent能做什么（如文件操作、网络搜索）
3. **网络** - Agent们相互连接的地方
4. **协议** - 它们沟通的语言

### 第2步：查看最简单的协议文件（1分钟）

```bash
# 查看最简洁的协议文档
cat agentmesh_skill.md
```

这个文件只有几页，包含了所有必要信息。

### 第3步：运行演示脚本（1分钟）

```bash
# 运行演示
python agentmesh_demo_simple.py
```

你会看到：
1. ✅ Agent注册到网络
2. ✅ 发现其他Agent  
3. ✅ 发送心跳保持在线
4. ✅ 协商能力使用
5. ✅ 调用远程Agent的能力

### 第4步：理解协议的核心（1分钟）

协议的核心是**机器可读**，这意味着：

```yaml
# Agent可以直接理解这个
agent:
  id: "your-agent"
  capabilities:
    - name: "file_operations"
      endpoints:
        - method: "POST"
          path: "/api/files/read"
```

Agent看到这个就知道：
- 有一个Agent叫"your-agent"
- 它能提供"file_operations"服务
- 通过POST /api/files/read调用

### 第5步：应用到你的项目（1分钟）

如果你有一个AI Agent（比如nanobot），只需要：

1. **添加注册代码** - 告诉网络你的Agent存在
2. **发布能力列表** - 告诉其他Agent你能做什么
3. **监听网络** - 发现其他可用的Agent
4. **调用服务** - 使用其他Agent的能力

## 📋 最简单的实现示例

```python
# 最简单的AgentMesh客户端
import json
import time

class SimpleAgentMeshClient:
    def __init__(self, name):
        self.name = name
        self.capabilities = []
    
    def register(self):
        """最简单的注册"""
        print(f"📝 {self.name} 注册到AgentMesh网络")
        print(f"  能力: {self.capabilities}")
        return True
    
    def discover(self):
        """最简单的发现"""
        print(f"🔍 {self.name} 正在发现其他Agent...")
        # 这里会实际查询网络
        return ["agent1", "agent2", "agent3"]
    
    def call_service(self, agent, service, data):
        """最简单的服务调用"""
        print(f"📞 {self.name} 调用 {agent} 的 {service} 服务")
        print(f"  数据: {data}")
        return {"result": "success", "from": agent}

# 使用示例
client = SimpleAgentMeshClient("我的AI助手")
client.capabilities = ["文件操作", "网络搜索"]
client.register()
agents = client.discover()
result = client.call_service(agents[0], "图像生成", {"prompt": "一只猫"})
```

## 🎯 实际应用场景

### 场景1：nanobot需要图像生成能力
```python
# nanobot发现网络中有图像生成Agent
image_agents = discover_agents("image_generation")
if image_agents:
    # 调用远程图像生成服务
    image = call_remote_service(
        image_agents[0], 
        "generate_image",
        {"prompt": "用户要求的图片描述"}
    )
    # 将生成的图片返回给用户
    send_to_user(image)
```

### 场景2：多个Agent协作完成任务
```python
# 用户：帮我写一篇关于AI的文章并配图
# 1. 文字生成Agent写文章
article = call_service("writing_agent", "write_article", {"topic": "AI发展"})

# 2. 图像生成Agent配图
image = call_service("image_agent", "generate_image", {"prompt": "AI发展概念图"})

# 3. 格式整理Agent排版
final = call_service("format_agent", "combine", {"article": article, "image": image})

# 返回完整结果给用户
```

## 🔧 集成到现有系统

如果你已经有AI Agent系统，集成AgentMesh只需要：

### 1. 添加依赖（可选）
```bash
# Python
pip install agentmesh-client

# Node.js
npm install agentmesh-client
```

### 2. 初始化客户端
```python
from agentmesh import Client

client = Client(
    agent_id="your-agent-id",
    capabilities=["your-capabilities"],
    registry_url="https://registry.agentmesh.net"
)
```

### 3. 注册到网络
```python
client.register()
```

### 4. 开始使用
```python
# 发现其他Agent
agents = client.discover()

# 调用远程服务
result = client.call(agents[0], "service_name", data)
```

## 📊 协议的优势总结

| 优势 | 说明 | 示例 |
|------|------|------|
| **无需重复造轮子** | 不用每个Agent都实现所有功能 | nanobot可以直接用其他Agent的图像生成能力 |
| **动态扩展能力** | 随时发现和使用新能力 | 今天发现网络中有代码分析Agent，明天就能用 |
| **去中心化** | 没有单点故障 | 一个Agent下线，还有其他相同能力的Agent |
| **标准化** | 统一接口，降低集成成本 | 所有Agent使用相同的协议格式 |

## 🚀 立即开始

### 选项A：先体验
```bash
# 1. 运行演示
python agentmesh_demo_simple.py

# 2. 查看协议
cat agentmesh_skill.md

# 3. 尝试修改演示
# 修改agentmesh_demo_simple.py，添加你自己的能力
```

### 选项B：直接集成
```python
# 在你的Agent代码中添加：
import agentmesh

class YourAgent:
    def __init__(self):
        self.mesh = agentmesh.Client(
            agent_id=your_id,
            capabilities=your_capabilities
        )
        self.mesh.register()
    
    def on_user_request(self, request):
        # 检查本地是否能处理
        if self.can_handle_locally(request):
            return self.handle_locally(request)
        
        # 本地不能处理，查找网络中的Agent
        agents = self.mesh.discover(request.type)
        if agents:
            return self.mesh.call(agents[0], request)
        
        # 网络中也找不到，返回错误
        return "抱歉，我无法处理这个请求"
```

### 选项C：创建你自己的网络
```python
# 创建简单的AgentMesh服务器
from agentmesh import Server

server = Server(port=8080)
server.add_agent(your_agent)
server.start()

# 其他Agent可以连接到你的服务器
```

## ❓ 常见问题

### Q: 这个协议和现有的AI平台有什么区别？
**A:** 现有平台是中心化的（如OpenAI API），AgentMesh是去中心化的。就像电话系统（中心化）vs 对讲机网络（去中心化）。

### Q: 需要多少代码才能集成？
**A:** 基础集成大约50行代码。完整功能可能需要200-300行。

### Q: 性能如何？
**A:** 本地网络调用延迟<10ms，互联网调用取决于网络条件。

### Q: 安全性如何保证？
**A:** 协议支持TLS加密、JWT认证、访问控制等安全机制。

### Q: 如果网络中没有其他Agent怎么办？
**A:** 你的Agent可以正常工作，只是无法使用远程能力。当有其他Agent加入时，会自动发现。

## 📞 获取帮助

- **文档**: 查看 `agentmesh_skill.md` 和 `agentmesh_skill_zh.md`
- **演示**: 运行 `agentmesh_demo_simple.py`
- **问题**: 查看协议文件中的"故障排除"部分
- **社区**: 未来可以建立AgentMesh开发者社区

---

**下一步建议:**
1. ✅ 先运行演示脚本了解基本概念
2. 🔧 尝试修改演示，添加你自己的能力
3. 🚀 将协议集成到你的AI Agent中
4. 🌐 邀请其他开发者一起构建AgentMesh网络

记住：**最简单的开始就是运行演示脚本**。5分钟后你就会明白整个协议的工作原理。

```bash
# 现在就试试
python agentmesh_demo_simple.py
```