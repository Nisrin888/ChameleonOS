"""
Redis key patterns and TTLs for Adaptive-OS.

All keys are prefixed with 'aos:' to namespace within a shared Redis instance.
"""

# Session: stores the assigned variation(s) for a visitor
# Value: JSON {"tenant_id": "...", "variation_id": "...", "vibe": "...", "slots": [...]}
SESSION_KEY = "aos:session:{session_id}"
SESSION_TTL = 86400  # 24 hours

# Variation cache: full handshake response for a tenant+vibe combo
# Value: JSON (HandshakeResponse minus session_id)
VARIATION_CACHE_KEY = "aos:vcache:{tenant_id}:{vibe_segment}"
VARIATION_CACHE_TTL = 3600  # 1 hour

# Real-time event counters (for dashboard live view)
# Value: Integer (INCR)
EVENT_COUNTER_KEY = "aos:counter:{tenant_id}:{variation_id}:{event_type}"
EVENT_COUNTER_TTL = 86400  # Rolling 24hr window

# Background enrichment queue (referrer URLs to analyze)
# Value: List of JSON strings {"referrer_url": "...", "tenant_id": "..."}
ENRICHMENT_QUEUE_KEY = "aos:enrich:queue"

# Referrer vibe cache (result of AI analysis)
# Value: JSON {"vibe": "luxe", "confidence": 0.85, "analyzed_at": "..."}
REFERRER_VIBE_CACHE_KEY = "aos:refvibe:{url_hash}"
REFERRER_VIBE_CACHE_TTL = 604800  # 7 days


def session_key(session_id: str) -> str:
    return SESSION_KEY.format(session_id=session_id)


def variation_cache_key(tenant_id: str, vibe_segment: str) -> str:
    return VARIATION_CACHE_KEY.format(tenant_id=tenant_id, vibe_segment=vibe_segment)


def event_counter_key(tenant_id: str, variation_id: str, event_type: str) -> str:
    return EVENT_COUNTER_KEY.format(
        tenant_id=tenant_id, variation_id=variation_id, event_type=event_type
    )


def referrer_vibe_cache_key(url_hash: str) -> str:
    return REFERRER_VIBE_CACHE_KEY.format(url_hash=url_hash)
