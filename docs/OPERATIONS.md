# Operations Guide

This guide covers common ops tasks: starting/stopping services, health checks, logs, backups, environment, and troubleshooting.

## Start/Stop Services

- Production (default):
  - Start: `docker compose up -d`
  - Stop: `docker compose down`
- Development:
  - Start: `docker compose -f docker-compose.dev.yml up -d`
  - Stop: `docker compose -f docker-compose.dev.yml down`

## Health Checks (default ports)

- API server: http://localhost:5000/health
- Analytics service: http://localhost:8005/analytics/health
- Postgres: container health in compose
- ChromaDB: http://localhost:8050 (prod) or 8001 (dev)
- MinIO: http://localhost:9000 (API), http://localhost:9001 (Console)
- Dashboards (optional): Admin 3010/3011, Analytics 3001/3002

See docker-compose files for exact port mappings and healthchecks.

## Logs

- Production: `docker compose logs -f <service>`
- Development: `docker compose -f docker-compose.dev.yml logs -f <service>`

Common services: api, postgres, chroma, minio, analytics, analytics-dashboard, backup.

## Backups and Restore

- Automated backups are handled by backup services in compose files.
- Details: `../README_DATABASE_BACKUPS.md`

## Environment

- Copy `.env.example` → `.env` and set:
  - `POSTGRES_PASSWORD`, `OPENAI_API_KEY`
  - `CHROMA_USERNAME`/`CHROMA_PASSWORD` (and `server.htpasswd`)
  - `MINIO_ACCESS_KEY`/`MINIO_SECRET_KEY`, `MINIO_*` ports
  - `GOVSTACK_API_KEY`/`GOVSTACK_ADMIN_API_KEY`
  - `ANALYTICS_*` ports if using analytics

## Troubleshooting

- Check `docker compose ps` and service health endpoints
- Verify `DATABASE_URL` for API and analytics connectivity
- Ensure Chroma auth matches `server.htpasswd`
- Confirm MinIO credentials and bucket existence (`MINIO_BUCKET_NAME`)
- API 401/403: check `X-API-Key` header and configured keys
