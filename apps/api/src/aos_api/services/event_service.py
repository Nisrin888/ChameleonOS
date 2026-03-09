"""
Event service: persists tracking events to PostgreSQL and increments Redis counters.
"""
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from aos_api.db.models import Event
from aos_api.redis_keys import event_counter_key, EVENT_COUNTER_TTL


async def record_event(
    db: AsyncSession,
    redis,
    tenant_id: str,
    session_id: str,
    variation_id: str | None,
    slot_id: str | None,
    event_type: str,
    event_name: str | None,
    referrer: str | None,
    utm_source: str | None,
    vibe_segment: str | None,
    metadata: dict | None,
) -> None:
    """Record a single event to DB and increment Redis counter."""

    # Persist to PostgreSQL
    event = Event(
        tenant_id=tenant_id,
        session_id=session_id,
        variation_id=variation_id,
        slot_id=slot_id,
        event_type=event_type,
        event_name=event_name,
        referrer=referrer,
        utm_source=utm_source,
        vibe_segment=vibe_segment,
        metadata_json=metadata,
        created_at=datetime.now(timezone.utc),
    )
    db.add(event)

    # Increment Redis counter (best-effort, don't fail if Redis is down)
    if variation_id:
        try:
            counter_key = event_counter_key(str(tenant_id), str(variation_id), event_type)
            await redis.incr(counter_key)
            await redis.expire(counter_key, EVENT_COUNTER_TTL)
        except Exception:
            pass  # Redis counter is nice-to-have, not critical


async def record_impressions(
    db: AsyncSession,
    redis,
    tenant_id: str,
    session_id: str,
    variation_id: str,
    slots: list[dict],
    referrer: str | None,
    utm_source: str | None,
    vibe: str,
) -> None:
    """Record impression events for all slots in a variation."""
    for slot in slots:
        await record_event(
            db=db,
            redis=redis,
            tenant_id=tenant_id,
            session_id=session_id,
            variation_id=variation_id,
            slot_id=slot.get("slot_id"),
            event_type="impression",
            event_name=None,
            referrer=referrer,
            utm_source=utm_source,
            vibe_segment=vibe,
            metadata=None,
        )
