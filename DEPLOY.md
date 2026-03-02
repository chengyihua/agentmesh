# AgentMesh Production Deployment Guide

This guide explains how to deploy AgentMesh in a production environment using Docker Compose.

## Prerequisites

- Docker Engine (v20.10+)
- Docker Compose (v2.0+)
- Git

## Deployment Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/chengyihua/agentmesh.git
   cd agentmesh
   ```

2. **Configure Environment Variables:**
   Create a `.env` file in the root directory or set these variables in your environment:
   ```bash
   # Security Secrets (CHANGE THESE IN PRODUCTION!)
   AGENTMESH_AUTH_SECRET=your-secure-random-secret-key-at-least-32-chars
   AGENTMESH_API_KEY=your-secure-api-key-for-admin-access
   
   # Database Credentials
   POSTGRES_USER=agentmesh
   POSTGRES_PASSWORD=secure_db_password
   POSTGRES_DB=agentmesh
   
   # Frontend API URL (Public URL of your server)
   NEXT_PUBLIC_API_URL=http://your-server-domain-or-ip/api
   ```

3. **Build and Start Services:**
   Run the following command to build the images and start the containers in detached mode:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d --build
   ```

4. **Verify Deployment:**
   - **Frontend:** Access `http://your-server-domain-or-ip`
   - **API Health:** Access `http://your-server-domain-or-ip/api/health`
   - **Logs:** Check logs with `docker-compose -f docker-compose.prod.yml logs -f`

## Architecture

The production setup includes:
- **Nginx:** Reverse proxy handling traffic on port 80, routing `/api` to the backend and `/` to the frontend.
- **Web (Next.js):** Frontend application running in standalone mode for performance.
- **API (FastAPI):** Backend service running with Gunicorn/Uvicorn workers (via `agentmesh serve --production`).
- **Postgres:** Primary database for persistent storage.
- **Redis:** High-performance cache and message broker.

## Security Notes

- The API is protected by `AGENTMESH_AUTH_SECRET` for JWT signing.
- Admin routes require `AGENTMESH_API_KEY` when running in production mode.
- Database ports are not exposed to the host machine, only accessible within the Docker network.
- Run `docker-compose.prod.yml` instead of `docker-compose.yml` to enable production safeguards.
