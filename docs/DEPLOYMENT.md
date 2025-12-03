# Deployment

Environment setup and deployment with Docker Compose.

## Environments

- Production: `docker compose up -d`
- Development: `docker compose -f docker-compose.dev.yml up -d`

## Environment Variables

Use `.env` (copy from `.env.example`). Important keys:

- `OPENAI_API_KEY`
- `POSTGRES_PASSWORD`
- `DATABASE_URL` (for analytics when run standalone)
- `CHROMA_HOST`/`CHROMA_PORT`/`CHROMA_USERNAME`/`CHROMA_PASSWORD`
- `MINIO_ACCESS_KEY`/`MINIO_SECRET_KEY`/`MINIO_BUCKET_NAME`
- `GOVSTACK_API_KEY`/`GOVSTACK_ADMIN_API_KEY`
- `ANALYTICS_*` ports if analytics is enabled

## Health and Readiness

- API: `GET /health`
- Analytics: `GET /analytics/health`
- Compose healthchecks are configured for key services

## Optional Profiles

- Standalone analytics dashboard can be enabled via `profiles` in `docker-compose.yml`

## Updating Images

- Rebuild API (dev):
  - `docker compose -f docker-compose.dev.yml build api`
  - `docker compose -f docker-compose.dev.yml up -d api`

Refer to `README.md` for service URLs and to `docs/OPERATIONS.md` for ops tasks.
