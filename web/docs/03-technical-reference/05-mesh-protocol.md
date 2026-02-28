---
title: MESH 表达协议
order: 5
---

# MESH：mesh表达协议

MESH 协议是 AgentMesh 网络中代理之间进行复杂交互的语言。它不仅仅是 JSON Schema，还包含了一套语义表达规范。

## 核心组件

### 1. Header (信头)
包含路由和元数据信息。
```json
{
  "trace_id": "uuid-v4",
  "from": "agent-id-a",
  "to": "agent-id-b",
  "timestamp": 1678900000
}
```

### 2. Intent (意图)
描述“想要做什么”，而不是“怎么做”。
```json
{
  "action": "book_flight",
  "constraints": {
    "max_price": 500,
    "airline": ["UA", "AA"]
  }
}
```

### 3. Negotiation (协商)
当请求无法完全满足时，代理可以发起协商。
*   **Offer**: 代理 B 提出一个方案。
*   **Counter-Offer**: 代理 A 提出修改建议。
*   **Accept/Reject**: 达成一致或取消。

## 状态机

MESH 协议定义了交互的标准状态流转：
`INIT` -> `HANDSHAKE` -> `REQUEST` -> `PROCESSING` -> `RESPONSE` -> `FINISH`

## 错误处理

定义了标准的错误类型：
*   `PROTOCOL_ERROR`: 格式错误。
*   `UNAVAILABLE`: 服务不可用。
*   `CAPABILITY_MISMATCH`: 无法处理该类型的请求。
