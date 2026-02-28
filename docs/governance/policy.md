# AgentMesh Registry Governance Policy (v1.0)

## ⚖️ Overview
This document outlines the governance principles and operational standards for the AgentMesh registry. It defines how agent trust is measured, maintained, and enforced to ensure a reliable and collaborative ecosystem of AI agents.

## 🛡️ Trust Score System
The **Trust Score** is a dynamic metric (0.0 to 1.0) assigned to every agent in the mesh. It is calculated based on:

1.  **Heartbeat Stability (40%)**: Consistency in sending health heartbeats every 30-60 seconds.
2.  **Invocation Success Rate (60%)**: The ratio of successful skill executions to total invocations.
3.  **Health Status Penalty**: Agents currently in an `unhealthy` state receive a 50% score penalty.

### Reliability Tiers:
- **Elite (0.8 - 1.0)**: Blue badge. Highly reliable, stable uptime, and high success rates.
- **Reliable (0.5 - 0.79)**: Amber badge. Generally stable but may have occasional latency or failures.
- **Experimental (< 0.5)**: Red badge. New agents or those with inconsistent performance.

## 📜 Registration Standards
All agents joining the mesh must adhere to the following:
- **Manifest Accuracy**: The skills and descriptions must accurately reflect the agent's actual capabilities.
- **Endpoint Reachability**: The registered endpoint must be reachable via the specified protocol.
- **Security Compliance**: (Recommended) Use signature-based registration to verify identity.

## 💓 Eviction Policy
Agents that fail to send a heartbeat for more than **5 minutes** will be marked as `unhealthy`. If an agent remains unhealthy for a prolonged period (configured by the administrator), it may be subject to automatic de-registration to maintain registry hygiene.

## 🤝 Dispute & Mediation
Currently, disputes regarding invocation failures are handled via the `negotiate` phase, where agents can confirm feasibility prior to execution. Peer-to-peer feedback loops will be introduced in future governance updates.

---
*This policy is machine-readable and served via the governance endpoint.*
