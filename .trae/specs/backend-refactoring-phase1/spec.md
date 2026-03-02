# Backend Refactoring Phase 1 Spec

## Why
The `AgentRegistry` class has become a "God Object," handling too many responsibilities (storage, health checks, search indexing, trust scoring). This makes the code difficult to maintain, test, and extend.

## What Changes
- **Extract Health Logic**: Move heartbeat and health check logic to a new `HealthMonitor` class.
- **Extract Discovery Logic**: Move search indexing and query logic to a new `DiscoveryService` class.
- **Refactor Registry**: `AgentRegistry` will delegate these tasks to the new services instead of implementing them directly.

## Impact
- **Affected specs**: None (internal refactoring).
- **Affected code**:
  - `src/agentmesh/core/registry.py` (Major cleanup)
  - `src/agentmesh/core/health.py` (New)
  - `src/agentmesh/core/discovery.py` (New)

## ADDED Requirements
### Requirement: HealthMonitor
The system SHALL use `HealthMonitor` to manage agent health status and periodic checks.

### Requirement: DiscoveryService
The system SHALL use `DiscoveryService` to maintain search indexes and execute search queries.

## MODIFIED Requirements
### Requirement: AgentRegistry Responsibilities
`AgentRegistry` SHALL focus on Agent CRUD operations and coordination, delegating domain-specific logic to helper services.
