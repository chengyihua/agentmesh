# Frontend-Backend Integration Spec

## Why
To ensure the end-to-end system works as expected for the user, verifying that backend events correctly trigger frontend updates via SSE.

## What Changes
- **Configuration**: Adjust Next.js proxy rules to handle SSE endpoints.
- **Tooling**: Add a simulation script to generate traffic.

## Impact
- **Affected specs**: None (Integration Testing).
- **Affected code**:
  - `web/next.config.mjs`
  - `scripts/simulate_agent.py` (New)

## ADDED Requirements
### Requirement: Proxy Configuration
The frontend development server SHALL proxy `/api/events` to the backend root `/events` endpoint, and `/api/*` to `/api/v1/*`.

### Requirement: Real-time UI Response
The UI SHALL reflect agent state changes within 2 seconds of the backend event being published.
