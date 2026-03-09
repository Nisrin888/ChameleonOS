"""
Node 4: Optimizer — Updates Thompson Sampling MAB weights.

Called when a conversion event is received via /v1/track.
NOT part of the handshake flow — invoked separately.

On conversion:      mab_state.alpha += 1 (reward)
On no-conversion:   mab_state.beta += 1 (penalty, applied via cron on expired sessions)
"""
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from aos_api.agent.state import OptimizationState
from aos_api.db.models import MabState


async def update_mab_weights(state: OptimizationState) -> dict:
    """Update MAB weights based on conversion events."""
    variation_id = state.get("variation_id")
    event_type = state.get("event_type")
    db: AsyncSession = state["db_session"]

    if not variation_id or variation_id == "none":
        return {"updated": False}

    try:
        var_uuid = UUID(variation_id)
    except (ValueError, TypeError):
        return {"updated": False}

    if event_type == "conversion":
        # Reward: increment alpha
        await db.execute(
            update(MabState)
            .where(MabState.variation_id == var_uuid)
            .values(alpha=MabState.alpha + 1)
        )
        await db.commit()
        return {"updated": True}

    return {"updated": False}


async def penalize_expired_sessions(db: AsyncSession, variation_id: str) -> bool:
    """
    Penalty: increment beta for variations shown in sessions that expired
    without a conversion. Called by a scheduled job.
    """
    try:
        var_uuid = UUID(variation_id)
    except (ValueError, TypeError):
        return False

    await db.execute(
        update(MabState)
        .where(MabState.variation_id == var_uuid)
        .values(beta=MabState.beta + 1)
    )
    await db.commit()
    return True
