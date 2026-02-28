# AgentMesh Frontend Improvement Plan (Phase 1-4)

## Overview
This plan outlines a phased approach to elevate the AgentMesh Web UI to support the full capabilities of the backend (especially Relay Network, Trust Management, and Federation).

## Phase 1: Infrastructure & Configuration (基础架构与配置) - [High Priority]
**Goal**: Make the application robust and configurable for different environments.
- [x] **Environment Variables**: Extract `http://localhost:8000/api/v1` to `NEXT_PUBLIC_API_URL`.
- [x] **API Client**: Create a dedicated Axios instance with interceptors for error handling (Toast notifications).
- [x] **Type Definitions**: Sync TypeScript interfaces with backend `AgentCard` and `TrustScore` models (especially `RELAY` protocol enum).

## Phase 2: Protocol & Relay Support (协议与中继支持) - [High Priority]
**Goal**: Visualize the newly implemented Relay Network capabilities.
- [x] **Agent Card Update**:
    - Add `RELAY` protocol badge (distinct color/icon).
    - Display `endpoint` intelligently (hide `relay://` complexity or show it as a "Tunnel").
- [x] **Network Status**: Visual indicator for Relay connection status (if available via API).

## Phase 3: Deep Observability (深度可观测性) - [Medium Priority]
**Goal**: Provide transparency into Trust Scores and Federation status.
- [x] **Trust Details Page**:
    - Charts for Trust Score history (if backend supports history api, or just current breakdown).
    - Event log visualization (Success/Fail/Decay counts).
- [ ] **Leaderboard Enhancement**: More metrics (QPS, Latency) if available.

## Phase 4: Interactive Playground (交互式控制台) - [Low Priority]
**Goal**: Improve Developer Experience (DX) by allowing in-browser testing.
- [x] **Invoke UI**: A "Try it out" button on Agent details page.
    - JSON payload editor.
    - Protocol selection (auto-detect).
    - Response viewer.

## Execution Strategy
We will execute these phases sequentially, starting with Phase 1 immediately to ensure a solid foundation.
