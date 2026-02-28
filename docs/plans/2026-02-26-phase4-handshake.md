# Phase 4: Verifiable Handshake & Security Implementation Plan

## Goal
Implement a secure, verifiable handshake mechanism for agent-to-agent communication. This ensures that:
1.  **Authentication:** The receiver knows who is calling (Caller ID).
2.  **Integrity:** The request has not been tampered with.
3.  **Non-repudiation:** The caller cannot deny making the request (via signature).
4.  **Replay Protection:** Requests cannot be captured and replayed later (via timestamp/nonce).

## Specification

### 1. Handshake Headers
Every authenticated request to `/agents/{agent_id}/invoke` MUST include:
- `X-Agent-ID`: The caller's Agent ID.
- `X-Agent-Timestamp`: ISO 8601 UTC timestamp of the request.
- `X-Agent-Signature`: Hex-encoded signature of the canonical request data.
- `X-Agent-Public-Key`: (Optional) The caller's public key, if not easily resolvable by the receiver.

### 2. Canonical Request Data
The signature is generated over a string constructed as:
```
{method}|{path}|{timestamp}|{body_hash}
```
- `method`: HTTP method (e.g., "POST").
- `path`: Request path (e.g., "/api/v1/agents/target-id/invoke").
- `timestamp`: Same as header.
- `body_hash`: SHA256 hash of the request body (JSON payload).

### 3. Verification Logic
1.  **Timestamp Check:** Reject if `abs(now - timestamp) > 60s`.
2.  **Identity Check:** 
    - If `X-Agent-Public-Key` is provided, verify `derive_agent_id(pub_key) == X-Agent-ID`.
    - If not, look up `X-Agent-ID` in the local Registry to get the public key.
    - If neither works, reject (Unknown Caller).
3.  **Signature Check:** Verify `X-Agent-Signature` against the canonical string using the public key (Ed25519).

## Implementation Tasks

### Task 1: Update SecurityManager
- [ ] Add `hash_body(payload: str) -> str`
- [ ] Add `sign_request(method, path, timestamp, body, private_key) -> str`
- [ ] Add `verify_request_signature(method, path, timestamp, body, signature, public_key) -> bool`

### Task 2: Update AgentMeshClient
- [ ] Allow initializing `AgentMeshClient` with `private_key` and `agent_id`.
- [ ] Implement `_sign_request` middleware/interceptor.
- [ ] Auto-inject headers for `invoke_agent`.

### Task 3: API Middleware/Dependency
- [ ] Create `verify_handshake` dependency in `src/agentmesh/api/dependencies.py` (or `routes.py`).
- [ ] Apply to `invoke_agent` endpoint.
- [ ] Handle `401 Unauthorized` for invalid signatures and `403 Forbidden` for identity mismatches.

### Task 4: Testing
- [ ] `tests/test_security_handshake.py`: Unit tests for signing/verification.
- [ ] `tests/test_api_handshake.py`: Integration tests with client and server.

## Dependencies
- `cryptography` (already installed)
- `httpx` (already installed)

## Notes
- We will prioritize Ed25519 for signatures.
- For this phase, we will assume the caller provides their public key in the header to simplify lookup in a distributed setting (or we rely on Federation sync having populated the registry). To be safe, we'll support both: lookup first, fallback to header (verified against ID).
