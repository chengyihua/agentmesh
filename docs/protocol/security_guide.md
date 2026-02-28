# AgentMesh Security Guide

This guide documents the security features implemented in the current codebase.

## 1. Authentication Modes

### API key mode (optional)

When the server starts with `--api-key`, protected routes require either:

- `X-API-Key: <configured-key>`, or
- `Authorization: Bearer <access_token>`

Protected routes:

- `POST /api/v1/agents/register`
- `POST /api/v1/agents`
- `PUT /api/v1/agents/{agent_id}`
- `DELETE /api/v1/agents/{agent_id}`
- `POST /api/v1/agents/{agent_id}/invoke`
- `POST /api/v1/cache/clear`

Production hardening mode:

- Starting server with `--production` enforces:
  - non-empty `--api-key`
  - non-default `--auth-secret`

### Token mode

Token endpoints:

- `POST /api/v1/auth/token`
- `POST /api/v1/auth/refresh`
- `GET /api/v1/auth/verify`

Issue token request:

```json
{
  "agent_id": "weather-bot-001",
  "secret": "agentmesh-dev-secret"
}
```

Returned token fields:

- `access_token`
- `refresh_token` (on issue)
- `token_type` (`bearer`)
- `expires_in`

## 2. Agent Card Signature Utilities

Endpoints:

- `POST /api/v1/security/keypair?algorithm=ed25519|rsa`
- `POST /api/v1/security/sign`
- `POST /api/v1/security/verify`

Signing flow:

1. Generate key pair.
2. Sign an `agent_card` with private key.
3. Put `signature` and `public_key` in the card.
4. Verify before or during registration.

If an incoming registered card contains `signature`, server-side validation verifies it.

## 3. Transport and CORS

- API is HTTP by default; deploy behind HTTPS in production.
- CORS middleware is enabled with permissive defaults.
- For production, restrict origin/method/header policy at reverse proxy or forked server config.

## 4. Rate Limiting

- Registration/update/delete: `60/minute`
- Heartbeat: `120/minute`
- Invoke: `120/minute`

Rate limiting is provided by `slowapi`.

## 5. Production Hardening Recommendations

1. Set a non-default `--auth-secret`.
2. Always set `--api-key` in exposed environments.
3. Run behind TLS termination (Nginx, ALB, or similar).
4. Use Redis or PostgreSQL instead of memory storage.
5. Restrict network access to `/metrics` if exposed publicly.

## 6. Security-Relevant Error Patterns

- `401` on invalid API key or bearer token.
- `401` on invalid token secret/refresh token.
- `403` on signature verification failure.
- `400` on malformed payloads.
