"""
Background Enrichment Worker

Pops referrer URLs from the Redis queue, fetches the page,
calls Claude Sonnet to analyze the "vibe", and caches the result.

Run as: python -m aos_api.agent.worker
"""
import asyncio
import hashlib
import json
from datetime import datetime, timezone

from aos_api.agent.tools.referrer_fetcher import fetch_referrer_page
from aos_api.redis_client import init_redis, get_redis
from aos_api.redis_keys import ENRICHMENT_QUEUE_KEY, referrer_vibe_cache_key, REFERRER_VIBE_CACHE_TTL
from aos_api.config import settings

VIBE_ANALYSIS_PROMPT = """You are a brand aesthetics classifier. Given the content of a web page,
classify its overall "vibe" or aesthetic into exactly ONE of these categories:

- minimalist: Clean, simple, muted, Scandinavian, quiet luxury
- bold: Loud, colorful, energetic, graphic, statement pieces
- luxe: Premium, elegant, sophisticated, high-end, aspirational
- casual: Relaxed, fun, everyday, approachable, trendy
- professional: Corporate, business, formal, authoritative, data-driven
- wellness: Health, zen, natural, holistic, self-care
- athletic: Sports, fitness, performance, active lifestyle
- edgy: Punk, streetwear, underground, rebellious, avant-garde
- default: Cannot determine or mixed signals

Respond with ONLY a JSON object like: {"vibe": "minimalist", "confidence": 0.85}
The confidence should be between 0.0 and 1.0.

Page content:
{content}"""


async def process_one(redis) -> bool:
    """Process one item from the enrichment queue. Returns True if an item was processed."""
    raw = await redis.rpop(ENRICHMENT_QUEUE_KEY)
    if not raw:
        return False

    data = json.loads(raw) if isinstance(raw, str) else raw
    referrer_url = data.get("referrer_url", "")

    if not referrer_url:
        return True  # Skip invalid entries

    # Check if we already have a cached result for this URL
    url_hash = hashlib.sha256(referrer_url.encode()).hexdigest()[:16]
    cache_key = referrer_vibe_cache_key(url_hash)
    existing = await redis.get(cache_key)
    if existing:
        return True  # Already enriched

    print(f"[Enricher] Fetching: {referrer_url}")

    # Fetch the page content
    content = await fetch_referrer_page(referrer_url)
    if not content:
        print(f"[Enricher] Failed to fetch: {referrer_url}")
        # Cache a default result to avoid re-fetching
        vibe_data = {
            "vibe": "default",
            "confidence": 0.0,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "error": "fetch_failed",
        }
        await redis.set(cache_key, json.dumps(vibe_data), ex=REFERRER_VIBE_CACHE_TTL)
        return True

    # Call Claude Sonnet for vibe analysis
    try:
        from langchain_anthropic import ChatAnthropic

        llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            api_key=settings.anthropic_api_key,
        )
        prompt = VIBE_ANALYSIS_PROMPT.format(content=content[:3000])
        result = await llm.ainvoke(prompt)

        # Parse the JSON response
        response_text = result.content.strip()
        # Handle case where model wraps in markdown code blocks
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        vibe_result = json.loads(response_text)
        vibe_data = {
            "vibe": vibe_result.get("vibe", "default"),
            "confidence": vibe_result.get("confidence", 0.5),
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }
        print(f"[Enricher] {referrer_url} -> {vibe_data['vibe']} ({vibe_data['confidence']})")

    except Exception as e:
        print(f"[Enricher] AI analysis failed for {referrer_url}: {e}")
        vibe_data = {
            "vibe": "default",
            "confidence": 0.0,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
        }

    # Cache the result (7 days TTL)
    await redis.set(cache_key, json.dumps(vibe_data), ex=REFERRER_VIBE_CACHE_TTL)
    return True


async def run_worker():
    """Main worker loop. Polls the enrichment queue."""
    print("[Enricher] Starting background enrichment worker...")
    await init_redis()
    redis = get_redis()

    while True:
        try:
            processed = await process_one(redis)
            if not processed:
                # Queue is empty, wait before polling again
                await asyncio.sleep(5)
        except Exception as e:
            print(f"[Enricher] Error: {e}")
            await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(run_worker())
