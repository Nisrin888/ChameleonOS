"""
Node 3: Background Enricher

Runs ONLY when is_known_referrer is False.
Does NOT block the handshake response.
Pushes the referrer URL onto a Redis queue for async processing.

A separate worker (worker.py) pops from the queue, fetches the
referrer page, calls Claude Sonnet to analyze the "vibe", and
caches the result in Redis (aos:refvibe:{url_hash}).
"""
import hashlib
import json
from datetime import datetime, timezone

from aos_api.agent.state import VibeAgentState
from aos_api.redis_keys import ENRICHMENT_QUEUE_KEY, referrer_vibe_cache_key


async def enqueue_enrichment(state: VibeAgentState) -> dict:
    """Queue unknown referrer URLs for background AI analysis."""
    if state.get("is_known_referrer", True):
        return {}  # Nothing to do

    referrer = state.get("visitor_context", {}).get("referrer", "")
    if not referrer:
        return {}

    redis = state.get("redis")
    if not redis:
        return {}

    try:
        # Dedup: skip if the referrer vibe is already cached
        url_hash = hashlib.sha256(referrer.encode()).hexdigest()[:16]
        cache_key = referrer_vibe_cache_key(url_hash)
        cached = await redis.get(cache_key)
        if cached:
            return {}  # Already analyzed — skip

        await redis.lpush(
            ENRICHMENT_QUEUE_KEY,
            json.dumps({
                "referrer_url": referrer,
                "tenant_id": state.get("tenant_id", ""),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }),
        )
    except Exception:
        pass  # Best-effort — don't fail the handshake

    return {}
