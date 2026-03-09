# ChameleonOS

**Turn one storefront into 10+ dynamic, vibe-matched landing pages with zero flicker.**

ChameleonOS is a platform for DTC brands and creators that dynamically swaps page content (hero images, headlines, testimonials, bundles) based on visitor context -- turning one website into multiple "Vibe-Matched" storefronts.

A visitor from TikTok sees an energetic, trend-driven page. A visitor from Pinterest sees a clean, minimalist layout. A visitor from Instagram sees a bold, grid-based design. All from the same URL.

> This repo is a **working demo** of the ChameleonOS platform -- a full-stack prototype with AI-powered routing, real-time optimization, and a merchant dashboard.

## Demo

### Agent-Driven Page Routing

Each visitor gets a page matched to their traffic source's "vibe":

| Traffic Source | Detected Vibe | Page Style |
|---------------|---------------|------------|
| TikTok | Casual | Energetic, urgency-driven, creator UGC |
| Instagram | Bold | Grid layout, aesthetic feed, community |
| Pinterest | Minimalist | Masonry pins, clean typography, save-to-board |
| Direct / Organic | Default | Standard product page |

### How It Works

```
Visitor clicks link on TikTok/IG/Pinterest
        |
        v
    SDK loads on merchant site
        |
        v
    POST /v1/handshake (referrer + UTMs)
        |
        v
    LangGraph Agent classifies "vibe"
    (Claude Haiku for known patterns,
     Claude Sonnet for unknown referrers)
        |
        v
    Returns variation payload
        |
        v
    Page redirects to vibe-matched design
        |
        v
    Thompson Sampling optimizes over time
```

## Architecture

```
chameleon-os/
├── apps/
│   ├── api/                # FastAPI + LangChain/LangGraph agent
│   ├── dashboard/          # Next.js merchant dashboard
│   └── demo-store/         # Static demo storefront (4 vibe pages)
├── packages/
│   ├── edge-middleware/    # Cloudflare Workers (V2)
│   ├── sdk/                # Platform-agnostic JS SDK (<script> tag)
│   └── shared/             # Shared TypeScript types
├── scripts/
│   └── simulate-demo.py   # Traffic simulator for demo data
├── turbo.json
└── docker-compose.yml
```

| Layer | Tech | Purpose |
|-------|------|---------|
| Edge | Cloudflare Workers | Request interception, session management |
| Backend | FastAPI + LangGraph | Vibe classification, MAB optimization, dashboard API |
| AI | Claude Sonnet + Haiku | Referrer analysis, vibe detection, insight generation |
| Storage | Upstash Redis + PostgreSQL | Sessions, cache, configs, conversion logs |
| Dashboard | Next.js | Performance metrics, Profit Pulse AI insights |
| SDK | Vanilla JS | Zero-flicker `<script>` tag for any site |

## Quick Start

### Prerequisites

- Node.js 20+
- Python 3.11+
- PostgreSQL 15+
- [Upstash Redis](https://upstash.com) account (free tier works)
- [Anthropic API key](https://console.anthropic.com)

### 1. Install dependencies

```bash
npm install
```

### 2. Set up the Python API

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate  # or .venv/Scripts/Activate.ps1 on Windows
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example apps/api/.env
# Edit apps/api/.env with your credentials:
#   DATABASE_URL, UPSTASH_REDIS_REST_URL, UPSTASH_REDIS_REST_TOKEN, ANTHROPIC_API_KEY
```

### 4. Set up the database

```bash
# Start PostgreSQL (via Docker or local install)
docker compose up -d postgres

# Seed the database
cd apps/api && python -m aos_api.db.seed
```

### 5. Run everything

```bash
# Terminal 1: API
cd apps/api && uvicorn aos_api.main:app --reload --port 8000

# Terminal 2: Demo store
cd apps/demo-store && npx serve . -l 3000

# Terminal 3: Dashboard
cd apps/dashboard && npm run dev
```

### 6. Try the demo

- `http://localhost:3000/?utm_source=tiktok` -- agent routes to casual (TikTok) page
- `http://localhost:3000/?utm_source=pinterest` -- agent routes to minimalist (Pinterest) page
- `http://localhost:3000/?utm_source=ig` -- agent routes to bold (Instagram) page
- `http://localhost:3000/` -- default page (no vibe matching)
- `http://localhost:3001` -- merchant dashboard

### 7. Populate demo data

```bash
cd apps/api
source .venv/bin/activate
python ../../scripts/simulate-demo.py --fast
```

This simulates 600 visitors with realistic conversion rates. Vibe-matched pages convert ~2-3x better than the default.

## Key Features

- **Agent-Driven Routing** -- LangGraph agent classifies visitor vibe and selects the best page variation
- **Zero-Flicker SDK** -- Critical CSS guard hides content during swap, no flash of unstyled content
- **Thompson Sampling (MAB)** -- Multi-armed bandit auto-optimizes which variation wins per traffic source
- **Profit Pulse** -- AI-generated performance insights via Claude Haiku
- **No Cookies, No PII** -- Privacy-first sessions stored in edge cache, fully ITP/Privacy Sandbox compliant
- **Platform Agnostic** -- Works with any site via a single `<script>` tag

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/handshake` | Classify visitor vibe, return variation |
| POST | `/v1/track` | Track events (clicks, conversions) |
| GET | `/v1/dashboard/performance` | Performance metrics by source |
| GET | `/v1/dashboard/insights` | AI-generated Profit Pulse summary |


