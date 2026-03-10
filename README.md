# GovBot Prototype — Local Setup Guide

This guide walks you through spinning up the full GovBot Prototype stack on your local machine using Docker.

---

## Prerequisites

Make sure the following are installed before you begin:

| Tool | Version | Download |
|------|---------|----------|
| Docker Desktop | Latest | https://www.docker.com/products/docker-desktop/ |
| Node.js | 18 or higher (LTS) | https://nodejs.org/en/download/ |
| Git | Any | https://git-scm.com/downloads |

> **Note:** Docker Desktop includes Docker Compose. Open it at least once after installing to complete setup.

---

## Step 1 — Clone the Repository

Open a terminal and run:

```bash
git clone https://github.com/think-ke/GovBot-Prototype.git
cd GovBot-Prototype
```

---

## Step 2 — Project Structure

After cloning, your project root should look like this:

```
GovBot-Prototype/
├── agencies-admin-dashboard/     # Next.js admin dashboard (runs on port 3010)
├── chainlit/                     # Python chatbot - Chainlit (runs on port 8000)
├── docker-compose.demo.yml
├── .env                          # You will create this in Step 3
└── ...
```

---

## Step 3 — Create the `.env` File

In the project root, create a file named `.env` and populate it with the following:

```env
# Chainlit chatbot
CHAINLIT_HOST=0.0.0.0
CHAINLIT_PORT=8000
API_BASE_URL=https://govstack-api.think.ke
GOVSTACK_API_KEY=your-api-key-here

# Admin dashboard
NODE_ENV=production
NEXT_TELEMETRY_DISABLED=1
API_URL=https://govstack-api.think.ke
NEXT_PUBLIC_ANALYTICS_API_URL=https://govstack-analytics.think.ke
ADMIN_DASHBOARD_PORT=3010
```

> ⚠️ Never commit this file. Make sure `.env` is listed in your `.gitignore`.

---

## Step 4 — Create the Docker Network

The `docker-compose.demo.yml` uses an external network. Create it once before starting anything:

```bash
docker network create govstack-network
```

---

## Step 5 — Build and Start the Containers

From the project root, run:

```bash
docker compose -f docker-compose.demo.yml build
docker compose -f docker-compose.demo.yml up -d
```

This starts two services:

| Service | URL | Description |
|---------|-----|-------------|
| Chainlit Chatbot | http://localhost:8000 | GovBot AI chat interface |
| Agencies Admin Dashboard | http://localhost:3010 | Admin panel (Next.js) |

> The admin dashboard has a health check — it may take up to 30 seconds to become fully available after starting.

---

## Step 6 — Check Services are Running

```bash
docker compose -f docker-compose.demo.yml ps
```

Both services should show status `Up`. The `admin-dashboard` will show `healthy` once it passes its health check.

To follow logs:

```bash
# All services
docker compose -f docker-compose.demo.yml logs -f

# Chainlit only
docker compose -f docker-compose.demo.yml logs -f chainlit-demo

# Admin dashboard only
docker compose -f docker-compose.demo.yml logs -f admin-dashboard
```

---

## Step 7 — (Optional) Run the Admin Dashboard with Live Reload

If you want hot-reloading during frontend development, skip Docker for the dashboard and run it directly:

```bash
cd agencies-admin-dashboard
npm install
npm run dev
```

Access it at http://localhost:3000 (Next.js dev default).

> Keep your other terminal running the Docker containers for the chatbot.

---

## Step 8 — Stop the Stack

```bash
# Stop containers
docker compose -f docker-compose.demo.yml down

# Stop and remove volumes
docker compose -f docker-compose.demo.yml down -v
```

---

## External API Dependencies

Both services connect to the following external APIs:

| API | Used By |
|-----|---------|
| https://govstack-api.think.ke | Chainlit chatbot + Admin dashboard |
| https://govstack-analytics.think.ke | Admin dashboard analytics |

These must be reachable for full functionality. If running fully offline, you will need to mock these endpoints locally.

---

## Troubleshooting

**Docker build fails with `Cannot find module` error on admin-dashboard**

Make sure `agencies-admin-dashboard/.dockerignore` exists and contains:
```
node_modules
.next
.env*.local
*.log
```

**`govstack-network` not found error**

Re-run: `docker network create govstack-network`

**Port already in use**

Change `ADMIN_DASHBOARD_PORT` in your `.env` (e.g. to `3011`) and restart.

**Admin dashboard stuck on `starting` / not healthy**

Wait up to 30 seconds — it runs a health check at `/api/health` before marking itself healthy. Check logs with:
```bash
docker compose -f docker-compose.demo.yml logs -f admin-dashboard
```

**Permission denied on scripts**
```bash
chmod +x scripts/*.sh
```
