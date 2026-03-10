"""
Session service: manages visitor sessions in Redis.
Sessions persist for 24 hours. Same visitor = same variation (stickiness).
"""
import json
import uuid

from aos_api.redis_keys import session_key, SESSION_TTL


def generate_session_id() -> str:
    """Generate a unique session ID."""
    return f"ses_{uuid.uuid4().hex[:24]}"


async def get_session(redis, session_id: str) -> dict | None:
    """Retrieve an existing session from Redis."""
    data = await redis.get(session_key(session_id))
    if data is None:
        return None
    if isinstance(data, str):
        return json.loads(data)
    return data


async def create_session(
    redis,
    session_id: str,
    tenant_id: str,
    variation_id: str,
    vibe: str,
    slots: list[dict],
    is_control: bool,
    utm_source: str | None = None,
) -> None:
    """Create a new session in Redis with 24hr TTL."""
    session_data = {
        "tenant_id": tenant_id,
        "variation_id": variation_id,
        "vibe": vibe,
        "slots": slots,
        "is_control": is_control,
        "utm_source": utm_source,
    }
    await redis.set(session_key(session_id), json.dumps(session_data), ex=SESSION_TTL)
