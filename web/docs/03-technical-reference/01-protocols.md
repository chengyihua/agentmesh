---
title: 协议技术参考
order: 1
---

# 协议技术参考

AgentMesh 基于一系列开放协议构建，确保不同技术栈的代理能够无缝协作。

## 核心协议栈

### 1. Agent Identity Protocol (AIP)
定义了代理的身份标识格式。
*   **DID (Decentralized Identifier)**: 每个代理拥有唯一的 DID。
*   **Public Key Infrastructure**: 使用公钥/私钥对进行签名和验证，确保身份不可伪造。

### 2. Agent Discovery Protocol (ADP)
定义了代理如何广播自己的存在以及如何查询其他代理。
*   **Metadata Schema**: 包含名称、描述、版本、图标等。
*   **Capability Schema**: 使用 JSON Schema 定义输入输出格式。

### 3. Agent Invocation Protocol (AInP)
定义了代理之间的调用标准。
*   **Transport Agnostic**: 支持 HTTP, WebSocket, gRPC 等传输层。
*   **Standardized Error Codes**: 统一的错误处理机制。
*   **Context Propagation**: 支持分布式追踪（Trace ID）。

## 接口定义

```typescript
interface AgentCard {
  id: string;
  name: string;
  version: string;
  description: string;
  skills: Skill[];
  endpoint: string;
  protocol: 'http' | 'websocket' | 'grpc';
}

interface Skill {
  name: string;
  description: string;
  schema: JsonSchema; // Input parameters definition
}
```
