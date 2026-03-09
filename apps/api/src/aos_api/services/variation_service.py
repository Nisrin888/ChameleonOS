"""
Variation service: fetches and selects variations for a tenant + vibe combo.
For MVP, uses random selection. Phase 3 replaces this with Thompson Sampling.
"""
import json
import random

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aos_api.db.models import Slot, Variation
from aos_api.redis_keys import variation_cache_key, VARIATION_CACHE_TTL

# 10% of traffic is forced to control group
CONTROL_GROUP_RATE = 0.10


async def get_variations_for_vibe(
    db: AsyncSession,
    redis,
    tenant_id: str,
    vibe: str,
) -> tuple[list[dict], str, bool]:
    """
    Get slot variations for a tenant + vibe. Returns (slots, variation_group_id, is_control).

    Logic:
    1. Check Redis cache for this tenant+vibe combo
    2. On cache miss, query DB for all variations matching this vibe
    3. If no vibe-specific variations, fall back to control/default
    4. Apply 10% control group force
    """
    # Check cache
    cache_key = variation_cache_key(tenant_id, vibe)
    cached = await redis.get(cache_key)
    if cached:
        data = json.loads(cached) if isinstance(cached, str) else cached
        return data["slots"], data["variation_group_id"], data["is_control"]

    # Query DB: get all slots for this tenant
    slot_result = await db.execute(select(Slot).where(Slot.tenant_id == tenant_id))
    slots = slot_result.scalars().all()

    if not slots:
        return [], "none", False

    # For each slot, find variations matching the requested vibe
    all_slot_payloads = []
    is_control = False
    variation_group_id = ""

    # Determine if this visitor is in the control group
    force_control = random.random() < CONTROL_GROUP_RATE

    target_vibe = "default" if (force_control or vibe == "default") else vibe

    for slot in slots:
        var_result = await db.execute(
            select(Variation).where(
                Variation.slot_id == slot.id,
                Variation.vibe_segment == target_vibe,
            )
        )
        variations = var_result.scalars().all()

        if not variations:
            # Fall back to default/control for this slot
            fallback_result = await db.execute(
                select(Variation).where(
                    Variation.slot_id == slot.id,
                    Variation.vibe_segment == "default",
                )
            )
            variations = fallback_result.scalars().all()

        if variations:
            # For MVP: pick the first matching variation (Phase 3 adds MAB)
            var = variations[0]
            content = var.content_json
            all_slot_payloads.append({
                "slot_id": slot.slot_key,
                "selector": slot.selector,
                "action": content.get("action", "replace_text"),
                "value": content.get("value", ""),
            })
            is_control = var.is_control
            if not variation_group_id:
                variation_group_id = str(var.id)

    if force_control:
        is_control = True

    # Cache the result
    cache_data = {
        "slots": all_slot_payloads,
        "variation_group_id": variation_group_id,
        "is_control": is_control,
    }
    await redis.set(cache_key, json.dumps(cache_data), ex=VARIATION_CACHE_TTL)

    return all_slot_payloads, variation_group_id, is_control
