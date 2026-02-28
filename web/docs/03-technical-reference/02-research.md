---
title: 研究背景
order: 2
---

# 研究背景：Test-Time Training 与 AgentMesh

## Test-Time Training (TTT)

Test-Time Training 是指在模型推理阶段（Test Time）进行临时的、针对特定输入的微调或优化，而不是仅依赖于预训练的权重。

### AgentMesh 的关联

AgentMesh 的生态系统天然支持 TTT 的理念：
1.  **动态组合**: 代理不是静态的模型，而是可以根据任务动态调用其他工具或代理的“动态图”。
2.  **上下文学习**: 代理可以通过检索生态系统中的知识库（RAG）来在运行时提升性能。
3.  **反馈循环**: 用户的反馈（Feedback）可以实时更新代理的信任评分，甚至触发代理的自我修正。

## 理论基础

AgentMesh 的设计深受复杂适应系统（Complex Adaptive Systems）理论的影响。我们认为，智能不仅仅通过单个巨大的模型涌现，也可以通过大量小型、专业的智能体通过高效的网络协作涌现。

> "The whole is greater than the sum of its parts."
