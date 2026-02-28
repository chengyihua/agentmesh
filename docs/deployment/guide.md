# Deployment Guide

This guide documents deployment options supported by the current codebase.

## 1. Local process deployment

### Memory backend (default)

```bash
python -m agentmesh serve --storage memory --host 0.0.0.0 --port 8000
```

### Redis backend

```bash
python -m agentmesh serve \
  --storage redis \
  --redis-url redis://localhost:6379 \
  --host 0.0.0.0 \
  --port 8000
```

### PostgreSQL backend

```bash
python -m agentmesh serve \
  --storage postgres \
  --postgres-url postgresql://localhost:5432/agentmesh \
  --host 0.0.0.0 \
  --port 8000
```

## 2. Runtime flags

Server flags implemented in CLI:

- `--host`
- `--port`
- `--debug`
- `--storage memory|redis|postgres`
- `--redis-url`
- `--postgres-url`
- `--auth-secret`
- `--api-key`
- `--production`

Recommended production baseline:

```bash
python -m agentmesh serve \
  --storage postgres \
  --postgres-url postgresql://<user>:<pass>@<host>:5432/agentmesh \
  --api-key <strong-api-key> \
  --auth-secret <strong-auth-secret> \
  --host 0.0.0.0 \
  --port 8000
```

## 3. Docker

The repository includes `Dockerfile` with default command:

```bash
python -m agentmesh serve --storage memory --host 0.0.0.0 --port 8000
```

Build and run:

```bash
docker build -t agentmesh:local .
docker run --rm -p 8000:8000 agentmesh:local
```

Override command for Redis:

```bash
docker run --rm -p 8000:8000 agentmesh:local \
  python -m agentmesh serve --storage redis --redis-url redis://host.docker.internal:6379
```

## 4. Docker Compose

Repository root includes `docker-compose.yml` with services:

- `agentmesh-memory`
- `agentmesh-redis`
- `agentmesh-postgres`
- `redis`
- `postgres`

Run:

```bash
docker compose up --build
```

Ports in current compose file:

- `8000` -> memory mode
- `8001` -> redis mode (container port 8000)
- `8002` -> postgres mode (container port 8000)

## 5. Reverse proxy and TLS

For internet-facing deployments:

1. Place API behind HTTPS reverse proxy.
2. Restrict CORS and inbound origins at proxy layer.
3. Block public access to `/metrics` unless needed.

## 6. Health and readiness checks

Use:

- `GET /health`
- `GET /version`
- `GET /api/v1/stats`

Example:

```bash
curl -f http://localhost:8000/health
```

## 7. Operational checks

After deployment, verify:

1. register -> get -> discover -> delete cycle works
2. token issue/verify/refresh works with your configured `--auth-secret`
3. protected routes reject unauthorized writes when `--api-key` is set
4. storage backend reconnects after service restart
