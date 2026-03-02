# Real-time Event System (SSE) Spec

## Why
Currently, the frontend uses polling to update agent lists and status. This is inefficient and can lead to stale data or high server load. A push-based system is needed for real-time observability.

## What Changes
- **Backend**: Introduce an `EventBus` and an SSE endpoint `/events`.
- **Frontend**: Consume the SSE stream to trigger data refreshes automatically.

## Impact
- **Affected specs**: Frontend Perfection (Real-time).
- **Affected code**:
  - `src/agentmesh/core/events.py` (New)
  - `src/agentmesh/core/registry.py`
  - `src/agentmesh/core/health.py`
  - `src/agentmesh/api/routes.py`
  - `web/src/hooks/useEvents.ts` (New)

## ADDED Requirements
### Requirement: Real-time Updates
The system SHALL push updates to connected clients when:
- An agent registers or updates its profile.
- An agent's health status changes (e.g., Healthy -> Offline).
- An agent's trust score changes significantly (optional).

#### Scenario: Agent goes offline
- **WHEN** an agent misses heartbeats and is marked OFFLINE
- **THEN** the backend publishes an `agent_health_changed` event
- **AND** the frontend receives this event and refreshes the list immediately.
