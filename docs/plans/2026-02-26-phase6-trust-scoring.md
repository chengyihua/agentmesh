# Phase 6: Trust Scoring v2 Implementation Plan

## Goal
Implement a dynamic trust scoring system to evaluate agent reliability and security. The score (0.0 to 1.0) influences discovery ranking and federation sync priority.

## Specification

### 1. Scoring Factors
The trust score is a weighted moving average or event-based accumulator.
- **Base Score:** 0.5 (New agents).
- **Positive Events (+):**
  - Successful invocation (acknowledged): +0.01
  - Valid heartbeat (continuous): +0.001
  - Verified handshake: +0.005
- **Negative Events (-):**
  - Invocation timeout/error: -0.05
  - Signature verification failure: -0.2 (Security risk)
  - Rate limit exceeded (abusive): -0.02
  - Unreachable (connection refused): -0.05
- **Decay:**
  - Scores decay over time toward 0.5 (neutral) if inactive, ensuring only active agents maintain high scores.
  - Or simply: Decay the *impact* of old events.

### 2. TrustManager
A new component `src/agentmesh/core/trust.py`:
- `TrustManager` class.
- Methods: `record_event(agent_id, event_type)`, `get_score(agent_id)`.
- Background task: `decay_loop()` to normalize scores.

### 3. Integration Points
- **Registry:** `register_agent` initializes score.
- **Routes:** `invoke_agent` records success/failure. `verify_handshake` records failures.
- **Federation:** Sync trust scores from peers (trusted peers' opinion matters).
- **Discovery:** Already uses `trust_score` in ranking.

### 4. API
- `GET /api/v1/agents/{agent_id}/trust`: Get detailed trust report.

## Implementation Tasks

### Task 1: TrustManager Core
- [ ] Create `src/agentmesh/core/trust.py`.
- [ ] Implement `TrustManager` with in-memory storage (persisted via `AgentRegistry` update).
- [ ] Define event weights.

### Task 2: Event Hooks
- [ ] In `routes.py`, call `trust_manager.record_success/failure` around `invoke_agent`.
- [ ] In `security.py` or `routes.py`, record signature failures.

### Task 3: API Endpoint
- [ ] Add `GET /agents/{agent_id}/trust`.

### Task 4: Testing
- [ ] Unit tests for score updates and decay.
- [ ] Integration test: Invoke agent -> score increases. Fail -> score decreases.

## Dependencies
- None.
