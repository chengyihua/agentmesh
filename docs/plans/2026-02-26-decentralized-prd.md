# AgentMesh 去中心化演进产品需求文档 (PRD)

**版本**: 1.0  
**日期**: 2026-02-26  
**状态**: 草稿  
**作者**: AgentMesh Team  

## 1. 背景与目标

### 1.1 背景
AgentMesh 当前版本（v1）主要作为一个中心化的代理注册与发现网关运行。虽然提供了多协议支持和基础的注册发现功能，但存在单点依赖、身份验证依赖中心化 API Key、缺乏语义发现能力以及跨网段调用困难等问题。

### 1.2 目标
本 PRD 旨在定义 AgentMesh 向“去中心化代理互联层”演进的产品需求。核心目标是实现：
1.  **去中心化身份与注册**：消除对中心化 ID 分配的依赖，基于密码学公钥派生身份。
2.  **联邦与自治**：支持多节点间的元数据同步，消除单点故障。
3.  **语义化发现**：引入向量检索，支持基于自然语言的能力匹配。
4.  **可验证的安全调用**：基于签名的握手协议，确保调用链路可审计、可验证。

## 2. 用户故事

| 角色 | 故事 | 价值 |
| :--- | :--- | :--- |
| **Agent 开发者** | 我希望我的 Agent 能通过公钥自生成 ID 并注册，无需向管理员申请 | 降低接入由于，实现无许可准入 (Permissionless Entry) |
| **Agent 开发者** | 我希望在 Manifest 中声明我的计费规则和 QPS 预算 | 保护我的资源不被滥用，并明确服务成本 |
| **Agent 使用者** | 我希望通过自然语言描述（如“找一个能分析股票的代理”）来发现服务 | 降低发现成本，提高匹配精准度 |
| **运维人员** | 我希望部署多个 Registry 节点并让它们自动同步数据 | 提高系统的可用性和容灾能力 |
| **安全审计员** | 我希望能验证每一次调用的来源和授权范围，即使在跨网络的情况下 | 确保系统安全性，防止未授权访问 |

## 3. 功能需求

### 3.1 身份与注册模型升级 (Identity & Registration)

**当前痛点**：ID 由用户自选或系统分配，缺乏密码学绑定；Manifest 字段有限。

**需求变更**：
1.  **Agent ID 生成规则**：
    *   强制基于 `public_key` 生成：`agent_id = base58(sha256(public_key)[:20])` (示例算法)。
    *   注册时必须提交 `public_key` 和 `manifest_signature`（用私钥对 Manifest 核心字段的签名）。
2.  **Manifest 字段扩展** (`AgentCard`)：
    *   新增 `public_key` (String, Required): 代理公钥 (Ed25519/RSA)。
    *   新增 `manifest_signature` (String, Required): 自身签名。
    *   新增 `pricing` (Object): 计费模型 (e.g., `{"model": "token", "rate": 0.001, "currency": "USD"}`).
    *   新增 `qps_budget` (Int): 全局 QPS 限制声明。
    *   新增 `concurrency_limit` (Int): 并发限制声明。
    *   新增 `vector_desc` (String): 用于生成 Embedding 的详细能力描述。
    *   新增 `models` (List[String]): 支持的模型列表 (e.g., `["gpt-4", "claude-3"]`).
3.  **兼容性**：
    *   提供 `require_signed_registration` 配置开关。
    *   开启时，拒绝不符合签名规则的注册；关闭时，允许旧版注册但标记为 `trust_level=low`。

### 3.2 联邦与种子同步 (Federation & Sync)

**当前痛点**：单节点运行，无法感知其他节点的 Agent。

**需求变更**：
1.  **同步端点**：
    *   `GET /federation/pull?since=<timestamp>`: 返回指定时间后更新的 Agent 列表（增量同步）。
2.  **种子节点配置**：
    *   支持配置 `SEEDS` 列表 (e.g., `["https://registry-a.mesh", "https://registry-b.mesh"]`).
3.  **同步逻辑**：
    *   后台定时任务 (Interval 可配) 轮询种子节点。
    *   **冲突解决**：基于 `updated_at` (LWW - Last Write Wins)。
    *   **验证**：同步下来的 Agent 必须验证其 `manifest_signature`，验证失败则丢弃或标记为不可信。

### 3.3 语义发现 (Semantic Discovery)

**当前痛点**：仅支持精确匹配和简单的文本包含搜索。

**需求变更**：
1.  **向量索引**：
    *   集成向量数据库/库 (如 FAISS, Annoy, 或轻量级纯 Python 实现)。
    *   在注册/更新时，对 `vector_desc` (或 `description` + `skills`) 进行 Embedding 处理。
2.  **混合检索 API**：
    *   升级 `/agents/discover` 或新增 `/agents/semantic-search`。
    *   支持参数 `q` (自然语言查询)。
    *   **排序算法**：`Score = w1 * VectorSimilarity + w2 * TrustScore + w3 * Uptime`。

### 3.4 握手与安全调用 (Handshake & Security)

**当前痛点**：依赖静态 Token/API Key，缺乏防重放和防篡改机制。

**需求变更**：
1.  **握手协议**：
    *   调用方发起调用前，需生成 `InvocationToken`。
    *   Token 内容：`{ caller_id, target_id, nonce, timestamp, purpose, budget_limit }`。
    *   Token 签名：使用 Caller 私钥对 Token 内容签名。
2.  **网关验证**：
    *   接收方网关验证 Token 签名（使用 Caller 公钥，需先发现 Caller Manifest）。
    *   验证 `timestamp` (防重放)。
    *   验证 `budget_limit` (是否超支)。
3.  **mTLS 支持** (可选)：
    *   支持配置双向 TLS 认证，作为传输层安全增强。

### 3.5 信任与资源治理 (Trust & Governance)

**当前痛点**：信任评分仅为占位符；限流仅在网关层简单实现，未与 Manifest 联动。

**需求变更**：
1.  **动态信任评分 (Trust Score v2)**：
    *   基于事件的评分模型：
        *   注册签名验证成功 (+Score)
        *   心跳正常 (+Score)
        *   调用成功 (+Score)
        *   调用失败/超时 (-Score)
        *   签名伪造 (直接拉黑/重置为 0)
    *   引入衰减机制：长期无活跃，分数自然衰减。
2.  **预算执行**：
    *   网关根据被调方 Manifest 中的 `qps_budget` 和 `concurrency_limit` 执行本地限流。
    *   超限返回 `429 Too Many Requests`，并记录审计日志。

## 4. 数据模型变更

### AgentCard (Update)
```python
class AgentCard(BaseModel):
    # ... existing fields ...
    public_key: str  # New
    manifest_signature: str # New
    pricing: Optional[Dict[str, Any]] # New
    qps_budget: Optional[int] # New
    concurrency_limit: Optional[int] # New
    vector_desc: Optional[str] # New
    models: Optional[List[str]] # New
    trust_score: float # Existing, but calculation logic changes
    # ...
```

## 5. 接口规范 (API Spec Changes)

*   `POST /agents/register`: 增加签名校验逻辑。
*   `GET /federation/pull`: 新增接口。
*   `GET /agents/discover`: 增强查询参数，支持语义搜索。
*   `POST /agents/{id}/invoke`: Header 中增加 `X-Agent-Signature` 和 `X-Invocation-Token`。

## 6. 非功能需求

*   **性能**：
    *   同步延迟 < 1分钟 (在默认配置下)。
    *   语义检索 P95 延迟 < 200ms。
*   **兼容性**：
    *   保证 v1 客户端在 `require_signed_registration=False` 模式下仍可工作。
*   **可扩展性**：
    *   向量索引需支持插件化替换 (Memory -> FAISS -> VectorDB)。

## 7. 实施路线图 (Phasing)

参考设计文档的 "PR 级拆分"：
*   **Phase 1 (Identity)**: Manifest 扩展, 公钥 ID, 注册签名校验.
*   **Phase 2 (Federation)**: 联邦同步端点, 定时任务.
*   **Phase 3 (Discovery)**: 向量检索集成.
*   **Phase 4 (Security)**: 握手协议, Token 验证.
*   **Phase 5 (Governance)**: 信任评分 v2, 预算执行.

