# Adaptive-OS — Windows Setup Guide

## Prerequisites

- **Node.js 20+** — [nodejs.org](https://nodejs.org)
- **Python 3.12+** — [python.org](https://python.org) (check "Add to PATH" during install)
- **Docker Desktop** — [docker.com](https://docker.com/products/docker-desktop)
- **Git** — [git-scm.com](https://git-scm.com)

All commands below are for **PowerShell**. Open it from the project folder:
```
cd C:\Users\nisch\OneDrive\Desktop\evolving-OS
```

---

## Step 1: Install Node Dependencies

```powershell
npm install
```

## Step 2: Build the SDK

```powershell
npm run build --workspace=@aos/sdk
```

You should see: `dist/aos.js  4.5kb`

## Step 3: Set Up Python Virtual Environment

```powershell
cd apps\api
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
cd ..\..
```

If you get an execution policy error on `.venv\Scripts\Activate.ps1`, run this first:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Step 4: Start PostgreSQL

Open **Docker Desktop** and wait until it's fully running, then:

```powershell
docker compose up -d postgres
```

Verify it's healthy:
```powershell
docker compose ps
```

You should see `postgres` with status `running` or `healthy`.

## Step 5: Run Database Migrations & Seed

```powershell
cd apps\api
.venv\Scripts\Activate.ps1
alembic upgrade head
python -m aos_api.db.seed
cd ..\..
```

Expected output:
```
Demo tenant seeded successfully!
  Public Key: pk_demo_001
  Secret Key: sk_demo_001
  Slots: hero-headline, hero-subheadline, hero-cta, hero-image
  Vibes: default (control), casual, minimalist, bold
```

---

## Starting the Services

You need **3 separate PowerShell windows**. Open each one and run:

### Window 1 — FastAPI Backend

```powershell
cd C:\Users\nisch\OneDrive\Desktop\evolving-OS\apps\api
.venv\Scripts\Activate.ps1
uvicorn aos_api.main:app --reload --port 8000
```

Expected output:
```
[AOS] Starting Adaptive-OS API...
[AOS] Using in-memory mock Redis (no Upstash credentials)
[AOS] API ready.
Uvicorn running on http://127.0.0.1:8000
```

### Window 2 — Demo Store

```powershell
cd C:\Users\nisch\OneDrive\Desktop\evolving-OS\apps\demo-store
npx serve . -l 3000
```

### Window 3 — Dashboard

```powershell
cd C:\Users\nisch\OneDrive\Desktop\evolving-OS\apps\dashboard
npm run dev
```

---

## Testing in the Browser

Once all 3 services are running, open these URLs:

| URL | Expected Result |
|-----|----------------|
| http://localhost:8000/docs | FastAPI Swagger documentation |
| http://localhost:8000/health | `{"status":"ok","service":"aos-api"}` |
| http://localhost:3000 | Demo store with default hero |
| http://localhost:3000?utm_source=tiktok | Hero changes to "Your Glow-Up Starts Here" (casual) |
| http://localhost:3000?utm_source=pinterest | Hero changes to "Elevate Your Daily Ritual" (minimalist) |
| http://localhost:3000?utm_source=ig | Hero changes to "OWN YOUR EDGE" (bold) |
| http://localhost:3001 | Dashboard with performance table |

### Testing Conversions

1. Visit `http://localhost:3000?utm_source=tiktok`
2. Scroll to the bottom "Demo Controls" section
3. Click **"Simulate Conversion"**
4. Open `http://localhost:3001` — you should see the data in the dashboard

---

## Manual API Tests (PowerShell)

### Test Handshake — TikTok Traffic

```powershell
$body = '{"public_key":"pk_demo_001","context":{"referrer":"https://tiktok.com/@user","url":"http://localhost:3000/","timestamp":"2026-02-27T12:00:00Z"}}'
Invoke-RestMethod -Uri http://localhost:8000/v1/handshake -Method Post -Body $body -ContentType "application/json"
```

Should return `vibe: casual` with slot variations.

### Test Handshake — Pinterest Traffic

```powershell
$body = '{"public_key":"pk_demo_001","context":{"referrer":"","url":"http://localhost:3000/","utm_source":"pinterest","timestamp":"2026-02-27T12:00:00Z"}}'
Invoke-RestMethod -Uri http://localhost:8000/v1/handshake -Method Post -Body $body -ContentType "application/json"
```

Should return `vibe: minimalist`.

### Test Handshake — Instagram Traffic

```powershell
$body = '{"public_key":"pk_demo_001","context":{"referrer":"","url":"http://localhost:3000/","utm_source":"ig","timestamp":"2026-02-27T12:00:00Z"}}'
Invoke-RestMethod -Uri http://localhost:8000/v1/handshake -Method Post -Body $body -ContentType "application/json"
```

Should return `vibe: bold`.

### Test Conversion Tracking

Replace `SESSION_ID` and `VARIATION_ID` with values from a handshake response:

```powershell
$body = '{"public_key":"pk_demo_001","session_id":"SESSION_ID","event_type":"conversion","variation_id":"VARIATION_ID","slot_id":"hero-headline","timestamp":"2026-02-27T12:02:00Z"}'
Invoke-RestMethod -Uri http://localhost:8000/v1/track -Method Post -Body $body -ContentType "application/json"
```

Should return `status: ok`.

### Test Dashboard API

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/v1/dashboard/performance?public_key=pk_demo_001"
```

Should return `summary` + `rows` with impression/conversion data.

### Test Invalid Key (should fail)

```powershell
$body = '{"public_key":"pk_invalid","context":{"referrer":"","url":"","timestamp":""}}'
Invoke-RestMethod -Uri http://localhost:8000/v1/handshake -Method Post -Body $body -ContentType "application/json"
```

Should return a 404 error.

---

## Troubleshooting

### "Docker not found"
Make sure Docker Desktop is open and fully started before running `docker compose`.

### "alembic: command not found"
Make sure you activated the venv first: `.venv\Scripts\Activate.ps1`

### "Port already in use"
Kill the process using the port:
```powershell
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F
```

### Demo store shows default content (no swap)
- Check the API is running on port 8000
- Open browser dev tools (F12) → Console tab — look for `[AOS]` messages
- Make sure you have `?utm_source=tiktok` (or similar) in the URL

### Dashboard shows "Could not load dashboard data"
- Make sure the API is running on port 8000
- Make sure you've seeded the database (Step 5)
- Visit the demo store first to generate some impression data

---

## Running the Demo Simulator

Once all 3 services are running, open a **4th PowerShell window** and run:

```powershell
cd C:\Users\nisch\OneDrive\Desktop\evolving-OS\apps\api
.venv\Scripts\Activate.ps1
python ..\..\scripts\simulate-demo.py
```

This simulates **600 visitors** from 5 traffic sources (TikTok, Instagram, Pinterest, Google, Direct), each converting at different rates. Vibe-matched pages convert ~2-3x better than generic default pages.

After the simulation completes, open the dashboard at `http://localhost:3001` to see:
- Total impressions, conversions, CVR
- Per-source performance breakdown
- Lift vs control group

---

## Stopping Everything

- Close each PowerShell window (Ctrl+C then close)
- Stop PostgreSQL: `docker compose down`
