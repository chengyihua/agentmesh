# Frontend Perfection and Backend Enhancement Design

## Overview
This document outlines the plan to perfect the AgentMesh frontend and enhance backend capabilities to support a robust, production-ready user experience. The focus is on implementing secure agent registration with Proof of Work (PoW), improving list/search functionality with server-side sorting, and ensuring type safety across the stack.

## Goals
1.  **Secure Registration**: Replace simulated frontend registration with a real PoW-backed flow.
2.  **Enhanced Discovery**: Add server-side sorting (e.g., by Trust Score) to `list_agents` and `discover_agents`.
3.  **Type Safety**: Ensure frontend types match backend API responses.
4.  **UX Improvements**: Add real loading states, error handling, and responsive feedback.

## Architecture

### 1. Proof of Work (PoW) Flow
To prevent Sybil attacks, unauthenticated agent registration requires solving a cryptographic puzzle.

**Sequence:**
1.  **Client**: GET `/auth/challenge`
    - Response: `{ nonce: string, difficulty: number, ttl_seconds: number }`
2.  **Client**: Solve Puzzle locally
    - Find `solution` such that `SHA256(nonce + solution)` has `difficulty` leading zeros.
    - This is a CPU-bound task, should be run in a Web Worker or async loop to avoid blocking UI.
3.  **Client**: POST `/agents/register`
    - Headers:
        - `X-PoW-Nonce`: `<nonce>`
        - `X-PoW-Solution`: `<solution>`
    - Body: Agent Metadata

### 2. Backend Enhancements
The `AgentRegistry` and API routes need to support flexible sorting to power the "Leaderboard" and "Trust-based Sorting" features efficiently.

**Changes:**
- `AgentRegistry.list_agents` and `discover_agents`:
    - Add `sort_by: str` (default="updated_at", options=["trust_score", "created_at", "updated_at"])
    - Add `order: str` (default="desc", options=["asc", "desc"])
- `api/routes.py`:
    - Expose `sort_by` and `order` query parameters in `/agents` and `/agents/discover`.

### 3. Frontend Architecture
- **Utilities**: `src/utils/pow.ts` for the solver logic.
- **Hooks**: Update `useRegistry.ts` to support new sorting params.
- **Components**:
    - `RegisterPage`: Integrate `solvePoW` with progress feedback.
    - `AgentsPage`: Use server-side sorting via `useAgents` hook.

## Implementation Plan

### Step 1: Backend - Sorting Logic
- Modify `src/agentmesh/core/registry.py` to implement sorting.
- Modify `src/agentmesh/api/routes.py` to accept query params.

### Step 2: Frontend - PoW Utility
- Create `web/src/utils/pow.ts` with a `solvePoW(nonce, difficulty)` function.
- Use `crypto.subtle` for fast hashing in browser.

### Step 3: Frontend - Registration Flow
- Update `web/src/app/register/page.tsx`:
    - Fetch challenge on "Register" click.
    - Show "Mining..." state.
    - Submit with headers.
    - Handle success/error.

### Step 4: Frontend - Agent List & Sorting
- Update `web/src/hooks/useRegistry.ts` to accept `sortBy` and `order`.
- Update `web/src/app/agents/page.tsx` to toggle sort order via API, removing client-side sort if server-side is sufficient (or keeping both for responsiveness).

## Testing
- Verify PoW flow manually by registering a new agent.
- Verify sorting by creating agents with different trust scores (mocked or real) and checking order.
