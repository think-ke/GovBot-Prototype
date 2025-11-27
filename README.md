# How to Run the GovBot Prototype Locally (Full Stack Setup Guide)

## Prerequisites
Before spinning up the project, make sure your machine has the following installed:

- **Docker Desktop (includes Docker Compose)**  
  → Download: https://www.docker.com/products/docker-desktop/  
  (Install it, open it once, and let it finish setup)

- **Node.js (version 18 or higher)**  
  → Download: https://nodejs.org/en/download/ (choose the “LTS” version)

- **Git (only if you don’t already have it)**  
  → Download: https://git-scm.com/downloads

The external APIs must be reachable:  
- https://govstack-api.think.ke  
- https://govstack-analytics.think.ke  
(or you must mock them locally)

## Step 1: Clone the project
* Open a terminal / command prompt
  - Windows: search for “Terminal” or “PowerShell”
  - Mac: search for “Terminal”
  - Linux: open your terminal

* Clone the project (copy-paste this exact line and press Enter)
git clone --branch staging --single-branch https://github.com/think-ke/govstack.git
text* After cloning finishes, run these two commands:
cd govstack
text(This takes you inside the project folder)

## Step 2: Project folder structure
Your project root should contain these main folders (create any that are missing):
gov-bot-prototype/
├── agencies-admin-dashboard/           (Next.js admin dashboard)
├── chainlit/                           (Chainlit Python chatbot)
├── analytics/                          (if you have an analytics service)
├── docker-compose.demo.yml
├── .env                                (you will create this)
└── other files (.gitignore, README.md, scripts, etc.)
text## Step 3: Create the .env file
In the project root, create a file named `.env` and add the following content (adjust values for your local setup):
CHAINLIT_HOST=0.0.0.0
CHAINLIT_PORT=8000
API_BASE_URL=https://govstack-api.think.ke
GOVSTACK_API_KEY=your-own-generated-key
NODE_ENV=development
NEXT_TELEMETRY_DISABLED=1
API_URL=https://govstack-api.think.ke
NEXT_PUBLIC_ANALYTICS_API_URL=https://govstack-analytics.think.ke
ADMIN_DASHBOARD_PORT=3010
textNever commit this `.env` file with real keys - make sure it is listed in `.gitignore`.

## Step 4: Create the Docker network
Your `docker-compose.demo.yml` uses an external network, so create it first:
docker network create govstack-network
text(run this once)

## Step 5: Build and start the containers
Open a terminal in the project root folder and run:
docker-compose -f docker-compose.demo.yml build chainlit-demo
docker-compose -f docker-compose.demo.yml up -d chainlit-demo
textThis will start two services:
- Chainlit chatbot demo on http://localhost:8000 (same experience as https://gov-bot-prototype.vercel.app/)
- Agencies Admin Dashboard on http://localhost:3010 (or whatever port you set in .env)

## Step 6: Start the Admin Dashboard (easiest way – with live reload)
* Open a new terminal window (keep the first one running) and run:
cd govstack-1/agencies-admin-dashboard
npm install
npm run dev
text## Step 7: Check everything is running
docker-compose ps
text(You should see both services with status "Up" and the admin-dashboard should eventually show "healthy")

To follow logs:
docker-compose logs -f
textor for a specific service:
docker-compose logs -f chainlit-demo
text## Step 8: Access the applications
- Chatbot (same as your Vercel prototype): http://localhost:8000
- Admin dashboard: http://localhost:3010
- Or simply use this to access both : https://gov-bot-prototype.vercel.app/

## Step 9: Stop and clean up
To stop everything:
docker-compose down
textTo stop and also remove volumes (if you added any):
docker-compose down -v