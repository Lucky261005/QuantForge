# Deployment Guide

QuantForge is a standard four-service app (Postgres, Redis, FastAPI, Next.js) plus a Celery
worker and Nginx — any platform that runs Docker containers or has managed equivalents for
Postgres/Redis works. Three concrete paths below; pick based on budget and how much
infrastructure you want to manage yourself.

## Environment variables

Copy `.env.example` to `.env` and fill in for whichever path you choose. At minimum, always set:

- `SECRET_KEY` — a long random string (`openssl rand -hex 32`). Never use the example value in production.
- `ENVIRONMENT=production`
- `DATABASE_URL` — a Postgres URL (`postgresql://user:pass@host:5432/db`)
- `CORS_ORIGINS` — a JSON array containing your actual frontend origin(s)
- `NEXT_PUBLIC_API_URL` — the public URL the frontend should call (baked in at build time for Next.js)

## Option 1 — Docker Compose on a single VM (cheapest, most control)

Any VM with Docker installed (a $5–10/mo box on Hetzner, DigitalOcean, or an AWS Lightsail
instance all work):

```bash
git clone <your-fork> && cd QuantForge
cp .env.example .env && edit it
docker compose up -d --build
```

Point a domain at the VM's IP and put a reverse proxy with TLS (Caddy or an Nginx + certbot
sidecar) in front of the existing `nginx` service, or replace it with Caddy directly for
automatic HTTPS. Back up the `postgres_data` volume on a schedule.

## Option 2 — Render (managed, minimal ops)

Render can run every piece of this stack as separate managed services from one repo:

1. **Postgres** — create a Render Postgres instance; copy its internal connection string into
   `DATABASE_URL`.
2. **Redis** — create a Render Redis (Key Value) instance; use its URL for `REDIS_URL`,
   `CELERY_BROKER_URL` (db `/1`), and `CELERY_RESULT_BACKEND` (db `/2`) — Render Redis exposes one
   database index per instance, so either provision three instances or point all three at the
   same instance/db if you don't need queue isolation.
3. **Backend web service** — new Web Service, root directory `backend/`, Docker runtime
   (it will use `backend/Dockerfile`). Set the env vars above. Render sets `PORT` automatically —
   the Dockerfile's `CMD` already binds `0.0.0.0:8000`; add a `--port $PORT` override in the
   service's start command if Render's assigned port differs.
4. **Celery worker** — a second service from the same repo/Dockerfile, but as a **Background
   Worker** (not Web Service), with start command
   `celery -A app.core.celery_app worker --loglevel=info`.
5. **Frontend** — new Web Service, root directory `frontend/`, Docker runtime
   (`frontend/Dockerfile`), build arg `NEXT_PUBLIC_API_URL` set to the backend service's public
   URL + `/api/v1`.

Render's free/starter tiers sleep on idle — fine for a portfolio demo, not for a real research
desk.

## Option 3 — Railway (managed, fastest to stand up)

Railway can provision Postgres and Redis as one-click plugins and deploy each Dockerfile as its
own service within one project:

1. `railway init` in the repo root, then add the **PostgreSQL** and **Redis** plugins from
   Railway's marketplace — it injects `DATABASE_URL`/`REDIS_URL`-shaped variables automatically
   (map them to the names this app expects via Railway's variable references, e.g.
   `DATABASE_URL=${{Postgres.DATABASE_URL}}`).
2. Add a service pointed at `backend/` (Railway auto-detects the Dockerfile) for the API.
3. Add a second service, same repo/path, with a custom start command for the Celery worker
   (`celery -A app.core.celery_app worker --loglevel=info`) — Railway supports multiple services
   from one Dockerfile with different commands.
4. Add a third service pointed at `frontend/` for the Next.js app; set `NEXT_PUBLIC_API_URL`
   as a build-time variable pointing at the backend service's generated public domain.
5. Railway issues HTTPS domains for each service automatically — no separate Nginx needed unless
   you want to consolidate under one custom domain.

## Option 4 — AWS (most control, most setup)

For a team that already lives on AWS: RDS Postgres + ElastiCache Redis + ECS Fargate (one
task definition per service: `backend`, `celery-worker`, `frontend`) behind an Application Load
Balancer, with the existing Dockerfiles pushed to ECR. This repo doesn't include Terraform/CDK
for this path — it's the natural next step if you outgrow Compose/Render/Railway, not a
prerequisite for running the project.

## Database migrations in production

The backend's `entrypoint.sh` runs `alembic upgrade head` on every container start, before the
app process starts. This is safe to run concurrently from multiple replicas (Alembic's version
table serializes via the migration transaction), but for a large production deployment prefer
running migrations as a separate release step/job rather than relying on container-start races.

## Health checks

Two separate endpoints, matching liveness/readiness semantics rather than one endpoint doing
both jobs:

- `GET /api/v1/health` — liveness only, returns `{"message": "ok"}` unconditionally. Wire this
  as a Kubernetes `livenessProbe` (or equivalent) — it answers "is the process up," nothing more.
- `GET /api/v1/health/ready` — readiness, checks the database (`SELECT 1`, hard dependency — a
  failure here means "don't route traffic here") and Redis (`PING`, soft dependency — reported
  as `"degraded"` rather than failing readiness, since the app has a documented graceful
  fallback for both the market-data cache and Celery when Redis is unreachable). Returns HTTP
  503 when the database check fails, 200 otherwise. Wire this as a `readinessProbe`.

Both Dockerfiles also define a `HEALTHCHECK` for plain `docker run`/Compose, currently pointed
at the liveness endpoint — point it at `/health/ready` instead if you want Compose's
healthcheck-gated `depends_on` to actually wait for the database, not just the process.
