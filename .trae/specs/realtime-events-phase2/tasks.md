- [x] Task 1: Create EventBus
  - [x] SubTask 1.1: Create `src/agentmesh/core/events.py`
  - [x] SubTask 1.2: Create `tests/test_event_bus.py`

- [x] Task 2: Integrate EventBus into Registry
  - [x] SubTask 2.1: Modify `src/agentmesh/core/health.py` to publish health events
  - [x] SubTask 2.2: Modify `src/agentmesh/core/registry.py` to publish registration events

- [x] Task 3: Implement SSE Endpoint
  - [x] SubTask 3.1: Add `/events` route to `src/agentmesh/api/routes.py`

- [x] Task 4: Frontend Integration
  - [x] SubTask 4.1: Create `web/src/hooks/useEvents.ts`
  - [x] SubTask 4.2: Integrate `useEvents` into `web/src/app/agents/page.tsx`
