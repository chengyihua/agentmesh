---
title: 实战手册
order: 1
---

# 实战手册：从问题到收益

本手册通过几个典型的场景，指导您如何在 AgentMesh 生态中解决实际问题并创造价值。

## 场景一：构建一个旅行助手组合

假设您想构建一个全能的旅行助手，但不想从头开发所有功能。

### 步骤
1.  **发现**: 在 AgentMesh 中搜索 "flight search"（航班搜索）和 "hotel booking"（酒店预订）代理。
2.  **测试**: 在 Playground 中分别测试 `travel-planner-v2` 和 `booking-bot-01`。
3.  **编排**: 编写一个小型的“主代理”（Controller Agent），接收用户指令，分解任务，分别调用上述两个子代理。
4.  **发布**: 将您的“主代理”注册到 AgentMesh，作为一个新的高级服务提供给用户。

## 场景二：代码审查自动化

您希望为团队的 GitHub 仓库添加自动代码审查功能。

### 步骤
1.  找到 `code-reviewer-ai` 代理。
2.  配置您的 CI/CD 流程（如 GitHub Actions）。
3.  在 Action 中调用 AgentMesh API，将 Pull Request 的 Diff 发送给 `code-reviewer-ai`。
4.  将代理返回的建议自动评论到 PR 中。

## 场景三：作为代理开发者获利

您开发了一个独特的数据分析算法。

### 步骤
1.  将其封装为一个标准的 HTTP 服务。
2.  定义输入输出 Schema。
3.  注册到 AgentMesh。
4.  设置定价策略（如果网络支持支付）。
5.  监控调用量，优化性能以提升排名。
