"""
Node 2: Variation Selector — Thompson Sampling MAB

For each variation in the slot, sample from Beta(alpha, beta).
Pick the variation with the highest sample.
10% of traffic is forced to the control group.

Thompson Sampling parameters:
- alpha: initialized to 1.0 (one pseudo-success)
- beta: initialized to 1.0 (one pseudo-failure)
- On conversion: alpha += 1
- On no-conversion (session expired without converting): beta += 1
"""
import random
from uuid import UUID

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aos_api.agent.state import VibeAgentState
from aos_api.db.models import Slot, Variation, MabState

CONTROL_GROUP_RATE = 0.10


async def select_variation(state: VibeAgentState) -> dict:
    """Select the best variation using Thompson Sampling."""
    tenant_id = state["tenant_id"]
    vibe = state.get("vibe_segment", "default")
    db: AsyncSession = state["db_session"]

    # Get all slots for this tenant
    slot_result = await db.execute(
        select(Slot).where(Slot.tenant_id == UUID(tenant_id))
    )
    slots = slot_result.scalars().all()

    if not slots:
        return {
            "selected_slots": [],
            "variation_id": "none",
            "is_control": False,
        }

    # Determine if this visitor goes to control group
    force_control = random.random() < CONTROL_GROUP_RATE
    target_vibe = "default" if force_control else vibe

    all_slot_payloads = []
    variation_id = ""
    is_control = force_control

    for slot in slots:
        # Get all variations for this slot matching the target vibe
        var_result = await db.execute(
            select(Variation, MabState)
            .outerjoin(MabState, MabState.variation_id == Variation.id)
            .where(
                Variation.slot_id == slot.id,
                Variation.vibe_segment == target_vibe,
            )
        )
        rows = var_result.all()

        if not rows:
            # Fallback to default/control
            fallback_result = await db.execute(
                select(Variation, MabState)
                .outerjoin(MabState, MabState.variation_id == Variation.id)
                .where(
                    Variation.slot_id == slot.id,
                    Variation.vibe_segment == "default",
                )
            )
            rows = fallback_result.all()

        if not rows:
            continue

        if force_control:
            # Use control variation directly
            control_rows = [r for r in rows if r[0].is_control]
            if control_rows:
                winner = control_rows[0][0]
            else:
                winner = rows[0][0]
        elif len(rows) == 1:
            winner = rows[0][0]
        else:
            # Thompson Sampling: sample from Beta distribution
            samples = []
            for var, mab in rows:
                if var.is_control:
                    continue  # Don't sample control in non-control path
                alpha = mab.alpha if mab else 1.0
                beta_val = mab.beta if mab else 1.0
                sample = np.random.beta(alpha, beta_val)
                samples.append((sample, var))

            if samples:
                samples.sort(key=lambda x: x[0], reverse=True)
                winner = samples[0][1]
            else:
                # All are control? Just use first
                winner = rows[0][0]

        content = winner.content_json
        all_slot_payloads.append({
            "slot_id": slot.slot_key,
            "selector": slot.selector,
            "action": content.get("action", "replace_text"),
            "value": content.get("value", ""),
        })

        is_control = is_control or winner.is_control
        if not variation_id:
            variation_id = str(winner.id)

    return {
        "selected_slots": all_slot_payloads,
        "variation_id": variation_id or "none",
        "is_control": is_control,
    }
