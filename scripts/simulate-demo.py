"""
Adaptive-OS Demo Simulator
===========================
Generates realistic traffic data to showcase the platform's value.

Simulates 500+ visitors from different traffic sources, each with different
conversion rates — proving that vibe-matched pages outperform the default.

Usage:
    cd apps/api
    .venv/Scripts/Activate.ps1   (Windows)
    python ../../scripts/simulate-demo.py --clean --fast

Requires: API running on localhost:8000 with seeded database.
"""

import argparse
import asyncio
import random
import time
import httpx

API_URL = "http://localhost:8000"

# --- Traffic source configs ---
# Each source has: utm_source, referrer, expected vibe, conversion rate, share of traffic
TRAFFIC_SOURCES = [
    {
        "name": "TikTok",
        "utm_source": "tiktok",
        "referrer": "https://tiktok.com/@creator/video/123",
        "expected_vibe": "casual",
        "conversion_rate": 0.045,  # 4.5% — high because vibe-matched
        "traffic_share": 0.30,     # 30% of total traffic
    },
    {
        "name": "Instagram",
        "utm_source": "ig",
        "referrer": "https://instagram.com/stories/brand/456",
        "expected_vibe": "bold",
        "conversion_rate": 0.038,  # 3.8%
        "traffic_share": 0.25,
    },
    {
        "name": "Pinterest",
        "utm_source": "pinterest",
        "referrer": "https://pinterest.com/pin/789",
        "expected_vibe": "minimalist",
        "conversion_rate": 0.042,  # 4.2%
        "traffic_share": 0.20,
    },
    {
        "name": "Direct / Organic",
        "utm_source": None,
        "referrer": "",
        "expected_vibe": "default",
        "conversion_rate": 0.018,  # 1.8% — control group, no vibe matching
        "traffic_share": 0.15,
    },
    {
        "name": "Google Ads",
        "utm_source": "google",
        "referrer": "https://www.google.com/search?q=supplements",
        "expected_vibe": "default",
        "conversion_rate": 0.022,  # 2.2%
        "traffic_share": 0.10,
    },
]

TOTAL_VISITORS = 600
PUBLIC_KEY = "pk_demo_001"
FAST_MODE = False


def print_header():
    print()
    print("=" * 60)
    print("  ChameleonOS — Demo Traffic Simulator")
    print("=" * 60)
    print()
    print(f"  Simulating {TOTAL_VISITORS} visitors across {len(TRAFFIC_SOURCES)} sources")
    print(f"  API: {API_URL}")
    print()


def print_source_plan():
    print("  Traffic Plan:")
    print("  " + "-" * 56)
    for src in TRAFFIC_SOURCES:
        count = int(TOTAL_VISITORS * src["traffic_share"])
        expected_conv = int(count * src["conversion_rate"])
        print(f"  {src['name']:20s} | {count:4d} visits | ~{src['conversion_rate']*100:.1f}% CVR | ~{expected_conv} conversions")
    print("  " + "-" * 56)
    print()


async def clean_old_events():
    """Delete all existing events so the dashboard shows only this simulation's data."""
    print("  Cleaning old events from database...")

    try:
        from aos_api.db.session import engine
        from sqlalchemy import text
        async with engine.begin() as conn:
            result = await conn.execute(text("DELETE FROM events"))
            print(f"  Deleted {result.rowcount} old events")
        print()
    except Exception as e:
        print(f"  Warning: Could not clean events ({e})")
        print("  Make sure you're running from apps/api with the venv active")
        print()


async def simulate_visitor(client: httpx.AsyncClient, source: dict) -> dict:
    """Simulate a single visitor: handshake → maybe convert."""

    # 1. Handshake (each visitor gets a fresh session)
    context = {
        "referrer": source["referrer"],
        "url": "http://localhost:3000/",
        "timestamp": "2026-03-07T12:00:00Z",
    }
    if source["utm_source"]:
        context["utm_source"] = source["utm_source"]

    try:
        resp = await client.post(
            f"{API_URL}/v1/handshake",
            json={"public_key": PUBLIC_KEY, "context": context},
            timeout=10,
        )
        if resp.status_code != 200:
            return {"source": source["name"], "status": "handshake_failed", "converted": False}

        data = resp.json()
        session_id = data.get("session_id", "")
        variation_id = data.get("variation_id", "")
        vibe = data.get("vibe", "unknown")
    except Exception:
        return {"source": source["name"], "status": "error", "converted": False}

    # 2. Random delay (simulate browsing) — skip in fast mode
    if not FAST_MODE:
        await asyncio.sleep(random.uniform(0.01, 0.05))

    # 3. Maybe convert (based on source's conversion rate)
    converted = random.random() < source["conversion_rate"]

    if converted and session_id and variation_id:
        try:
            await client.post(
                f"{API_URL}/v1/track",
                json={
                    "public_key": PUBLIC_KEY,
                    "session_id": session_id,
                    "event_type": "conversion",
                    "variation_id": variation_id,
                    "slot_id": "hero-headline",
                    "timestamp": "2026-03-07T12:05:00Z",
                },
                timeout=10,
            )
        except Exception:
            pass

    return {
        "source": source["name"],
        "vibe": vibe,
        "status": "ok",
        "converted": converted,
        "session_id": session_id[:8] if session_id else "",
    }


async def run_simulation():
    print_header()

    if CLEAN_MODE:
        await clean_old_events()

    print_source_plan()

    # Build visitor queue
    visitors = []
    for source in TRAFFIC_SOURCES:
        count = int(TOTAL_VISITORS * source["traffic_share"])
        visitors.extend([source] * count)
    random.shuffle(visitors)

    # Stats tracking
    stats = {}
    for src in TRAFFIC_SOURCES:
        stats[src["name"]] = {"impressions": 0, "conversions": 0, "vibe": src["expected_vibe"]}

    print(f"  Sending {len(visitors)} requests...")
    print()

    start_time = time.time()

    # Process in batches to avoid overwhelming the API
    BATCH_SIZE = 20
    completed = 0

    async with httpx.AsyncClient() as client:
        for i in range(0, len(visitors), BATCH_SIZE):
            batch = visitors[i:i + BATCH_SIZE]
            tasks = [simulate_visitor(client, src) for src in batch]
            results = await asyncio.gather(*tasks)

            for result in results:
                name = result["source"]
                if result["status"] == "ok":
                    stats[name]["impressions"] += 1
                    if result["converted"]:
                        stats[name]["conversions"] += 1

            completed += len(batch)
            pct = (completed / len(visitors)) * 100
            bar = "█" * int(pct / 2) + "░" * (50 - int(pct / 2))
            print(f"\r  [{bar}] {pct:.0f}% ({completed}/{len(visitors)})", end="", flush=True)

    elapsed = time.time() - start_time
    print(f"\n\n  Done in {elapsed:.1f}s")
    print()

    # --- Print results ---
    print("=" * 60)
    print("  SIMULATION RESULTS")
    print("=" * 60)
    print()
    print(f"  {'Source':<20s} {'Vibe':<12s} {'Views':>6s} {'Conv':>6s} {'CVR':>8s}")
    print("  " + "-" * 56)

    total_impressions = 0
    total_conversions = 0

    for name, data in stats.items():
        imp = data["impressions"]
        conv = data["conversions"]
        cvr = (conv / imp * 100) if imp > 0 else 0
        total_impressions += imp
        total_conversions += conv

        cvr_str = f"{cvr:.1f}%"
        print(f"  {name:<20s} {data['vibe']:<12s} {imp:>6d} {conv:>6d} {cvr_str:>8s}")

    print("  " + "-" * 56)

    overall_cvr = (total_conversions / total_impressions * 100) if total_impressions > 0 else 0
    print(f"  {'TOTAL':<20s} {'':12s} {total_impressions:>6d} {total_conversions:>6d} {overall_cvr:.1f}%")
    print()

    # Calculate lift — combine ALL default sources for control CVR
    control_sources = [s for s in stats.values() if s["vibe"] == "default"]
    control_imp = sum(s["impressions"] for s in control_sources)
    control_conv = sum(s["conversions"] for s in control_sources)
    control_cvr = (control_conv / control_imp * 100) if control_imp > 0 else 0

    vibe_matched = [s for s in stats.values() if s["vibe"] != "default" and s["impressions"] > 0]
    if vibe_matched and control_imp > 0:
        vibe_imp = sum(s["impressions"] for s in vibe_matched)
        vibe_conv = sum(s["conversions"] for s in vibe_matched)
        vibe_cvr = (vibe_conv / vibe_imp * 100) if vibe_imp > 0 else 0

        if control_cvr > 0:
            lift = ((vibe_cvr - control_cvr) / control_cvr) * 100
        else:
            lift = 100  # Control got 0 conversions — infinite lift

        print(f"  ┌──────────────────────────────────────────────────┐")
        print(f"  │  VIBE-MATCHED CVR:  {vibe_cvr:>5.1f}%  ({vibe_conv}/{vibe_imp}){'':<13}│")
        print(f"  │  CONTROL CVR:       {control_cvr:>5.1f}%  ({control_conv}/{control_imp}){'':<14}│")
        if control_cvr > 0:
            print(f"  │  LIFT:              +{lift:>4.0f}%{'':<27}│")
        else:
            print(f"  │  LIFT:              ∞  (control got 0 conversions) │")
        print(f"  │                                                  │")
        print(f"  │  Vibe-matched pages convert significantly        │")
        print(f"  │  better than generic default pages.              │")
        print(f"  └──────────────────────────────────────────────────┘")
    print()

    # Fetch live dashboard summary from API
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{API_URL}/v1/dashboard/performance?public_key={PUBLIC_KEY}",
                timeout=5,
            )
            if resp.status_code == 200:
                perf = resp.json()
                summary = perf.get("summary", {})
                print("  ┌──────────────────────────────────────────────────┐")
                print(f"  │  DASHBOARD SUMMARY (Live from API)               │")
                print(f"  │  Total Impressions:  {summary.get('total_impressions', 0):<28}│")
                print(f"  │  Total Conversions:  {summary.get('total_conversions', 0):<28}│")
                print(f"  │  Overall CVR:        {summary.get('overall_cvr', 0)*100:.2f}%{'':<23}│")
                print(f"  │  Lift vs Control:    {summary.get('lift_vs_control', 0):+.1f}%{'':<23}│")
                print(f"  └──────────────────────────────────────────────────┘")
                print()
    except Exception:
        pass

    print("  ╔══════════════════════════════════════════════════╗")
    print("  ║  Dashboard:  http://localhost:3001               ║")
    print("  ║  Demo Store: http://localhost:3000               ║")
    print("  ║  API:        http://localhost:8000/docs          ║")
    print("  ╚══════════════════════════════════════════════════╝")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ChameleonOS Demo Traffic Simulator")
    parser.add_argument("--fast", action="store_true", help="Skip delays for quick data population")
    parser.add_argument("--clean", action="store_true", help="Delete old events before simulating (recommended)")
    parser.add_argument("--visitors", type=int, default=600, help="Number of visitors to simulate")
    args = parser.parse_args()

    FAST_MODE = args.fast
    CLEAN_MODE = args.clean
    TOTAL_VISITORS = args.visitors

    if FAST_MODE:
        print("  [FAST MODE] Skipping browse delays")
    if CLEAN_MODE:
        print("  [CLEAN MODE] Will delete old events first")

    asyncio.run(run_simulation())
