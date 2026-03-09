"""
Node 1: Vibe Classifier

Strategy:
1. Run rule-based classifier first (fast path, <1ms)
2. If confidence is high (known domain + UTM), return immediately
3. If referrer is unknown, check Redis referrer vibe cache
4. If cache miss, flag for background enrichment and return "default"

The hot path stays LLM-free. Claude only runs in background enrichment.
"""
import hashlib
import json

from aos_api.agent.state import VibeAgentState
from aos_api.schemas.handshake import VisitorContext
from aos_api.services.vibe_classifier import classify
from aos_api.redis_keys import referrer_vibe_cache_key


async def classify_vibe(state: VibeAgentState) -> dict:
    """Classify the visitor's vibe from context signals."""
    context = state["visitor_context"]
    redis = state.get("redis")

    # Build a VisitorContext for the rule-based classifier
    visitor_ctx = VisitorContext(
        referrer=context.get("referrer", ""),
        url=context.get("url", ""),
        utm_source=context.get("utm_source"),
        utm_medium=context.get("utm_medium"),
        utm_campaign=context.get("utm_campaign"),
        utm_content=context.get("utm_content"),
        utm_term=context.get("utm_term"),
        timestamp=context.get("timestamp", ""),
        viewport_width=context.get("viewport_width"),
        geo_country=context.get("geo_country"),
    )

    # Fast path: rule-based classification
    vibe = classify(visitor_ctx)

    if vibe != "default":
        return {
            "vibe_segment": vibe,
            "vibe_confidence": 0.9,
            "is_known_referrer": True,
        }

    # Check Redis referrer vibe cache (from previous background enrichment)
    referrer = context.get("referrer", "")
    if referrer and redis:
        url_hash = hashlib.sha256(referrer.encode()).hexdigest()[:16]
        cache_key = referrer_vibe_cache_key(url_hash)
        cached = await redis.get(cache_key)
        if cached:
            data = json.loads(cached) if isinstance(cached, str) else cached
            return {
                "vibe_segment": data.get("vibe", "default"),
                "vibe_confidence": data.get("confidence", 0.7),
                "is_known_referrer": True,
            }

    # Unknown referrer — will be enriched in background
    return {
        "vibe_segment": "default",
        "vibe_confidence": 0.3,
        "is_known_referrer": False,
    }
