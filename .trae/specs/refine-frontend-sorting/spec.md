# Frontend Refinement & Sorting Integration Spec

## Why
The current agent list uses client-side sorting, which is inefficient for large datasets and disconnects from the backend's sorting capabilities. Additionally, the leaderboard widget lacks detailed metrics (like latency and uptime) that are available in the backend but not exposed or visualized, limiting the "Deep Observability" goal.

## What Changes
- **Frontend**:
  - Update `useAgents` hook to support `sort_by` and `order` parameters.
  - Refactor `AgentsPage` to use server-side sorting instead of client-side logic.
  - Replace simple `sortByTrust` toggle with a robust sort dropdown/control.
  - Update `LeaderboardWidget` to display "Invocations" and "Latency" (if available).
- **Backend**:
  - Update `get_leaderboard` API to return `latency_avg` and `uptime_percentage` in the `metrics` object.

## Impact
- **Affected specs**: Frontend Perfection and Backend Enhancement Design.
- **Affected code**:
  - `web/src/hooks/useRegistry.ts`
  - `web/src/app/agents/page.tsx`
  - `web/src/components/LeaderboardWidget.tsx`
  - `src/agentmesh/core/registry.py` (get_leaderboard)

## ADDED Requirements
### Requirement: Server-Side Sorting
The Agent List UI SHALL allow users to sort agents by:
- **Trust Score** (descending)
- **Last Updated** (descending)
- **Created Date** (descending)
- **Invocations** (descending) - *New sort option if supported by backend*

#### Scenario: User changes sort order
- **WHEN** user selects "Sort by Trust"
- **THEN** the frontend requests `/agents?sort_by=trust_score&order=desc`
- **AND** the list updates with server-returned data.

### Requirement: Enhanced Leaderboard Metrics
The Leaderboard API SHALL return:
- `latency_avg`: Average response time in ms.
- `uptime_percentage`: Percentage of successful health checks.

The Leaderboard Widget SHALL display:
- Heartbeats (existing)
- Invocations (new)
- Uptime (new, maybe as a small dot color or percentage)

## MODIFIED Requirements
### Requirement: Agent List Filtering
**Modified**: Filtering by health status can remain client-side for small lists, but ideally should pass `health_status` param to backend if supported. *For this spec, we will keep filtering client-side but sorting server-side, or move health filtering to server if easy.* (Backend `list_agents` doesn't seemingly support health filter yet, so we stick to client-side filtering + server-side sorting, or add health filter to backend. Let's add health filter to backend for completeness).

**Refined Plan**: Add `health_status` parameter to `list_agents` API to fully offload filtering.
