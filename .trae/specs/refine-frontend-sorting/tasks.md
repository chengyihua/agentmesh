# Tasks

- [x] Task 1: Update Backend `list_agents` and `get_leaderboard`
  - [x] SubTask 1.1: Modify `AgentRegistry.list_agents` to accept `health_status` filter.
  - [x] SubTask 1.2: Update `AgentRegistry.get_leaderboard` to include `latency_avg` (from `latency_sum / latency_count`) and `uptime_percentage` in metrics.
  - [x] SubTask 1.3: Update `api/routes.py` to expose `health_status` query param in `list_agents`.

- [x] Task 2: Update Frontend Hooks
  - [x] SubTask 2.1: Update `useAgents` in `web/src/hooks/useRegistry.ts` to accept `sortBy`, `order`, and `healthStatus`.
  - [x] SubTask 2.2: Update TypeScript interfaces for `Agent` and `LeaderboardAgent` to match new API response fields.

- [x] Task 3: Refactor `AgentsPage`
  - [x] SubTask 3.1: Replace client-side sorting/filtering logic with API parameters.
  - [x] SubTask 3.2: Implement a Sort Control (Dropdown or Button Group) for Trust, Updated, Created.
  - [x] SubTask 3.3: Ensure "Load More" or Pagination works with sorting (current implementation seems to be infinite scroll or simple list, we will stick to current pagination style).

- [x] Task 4: Enhance `LeaderboardWidget`
  - [x] SubTask 4.1: Update UI to show Invocations count and Latency/Uptime.
  - [x] SubTask 4.2: Add tooltips for new metrics.
