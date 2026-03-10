"""
POST /v1/handshake — Core endpoint.
Receives visitor context, classifies vibe, selects variation, returns payload.

Uses LangGraph agent for vibe classification + Thompson Sampling variation selection.
Falls back to rule-based if the agent errors.
"""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from aos_api.db.session import get_db
from aos_api.redis_client import get_redis
from aos_api.schemas.handshake import (
    HandshakeRequest,
    HandshakeResponse,
    SlotVariationResponse,
)
from aos_api.services import (
    tenant_service,
    session_service,
    variation_service,
    vibe_classifier,
    event_service,
)

router = APIRouter()


@router.post("/handshake", response_model=HandshakeResponse)
async def handshake(
    request: HandshakeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    redis = get_redis()

    # 1. Validate tenant
    tenant = await tenant_service.get_tenant_by_public_key(db, request.public_key)
    if not tenant:
        raise HTTPException(status_code=404, detail="Invalid public key")

    # 2. Check for existing session (stickiness)
    if request.session_id:
        cached_session = await session_service.get_session(redis, request.session_id)
        if cached_session:
            return HandshakeResponse(
                session_id=request.session_id,
                variation_id=cached_session["variation_id"],
                vibe=cached_session["vibe"],
                slots=[SlotVariationResponse(**s) for s in cached_session["slots"]],
                ttl=86400,
                is_control=cached_session.get("is_control", False),
            )

    # 3. Run LangGraph agent for vibe classification + variation selection
    try:
        slots, variation_id, vibe, is_control = await _run_agent(
            db, redis, str(tenant.id), request
        )
    except Exception:
        # Fallback to rule-based if agent errors
        slots, variation_id, vibe, is_control = await _run_fallback(
            db, redis, str(tenant.id), request
        )

    # 4. Generate session ID and persist
    session_id = session_service.generate_session_id()
    await session_service.create_session(
        redis=redis,
        session_id=session_id,
        tenant_id=str(tenant.id),
        variation_id=variation_id,
        vibe=vibe,
        slots=slots,
        is_control=is_control,
        utm_source=request.context.utm_source,
    )

    # 5. Record impression events asynchronously
    background_tasks.add_task(
        _record_impressions,
        str(tenant.id),
        session_id,
        variation_id,
        slots,
        request.context.referrer,
        request.context.utm_source,
        vibe,
    )

    return HandshakeResponse(
        session_id=session_id,
        variation_id=variation_id,
        vibe=vibe,
        slots=[SlotVariationResponse(**s) for s in slots],
        ttl=86400,
        is_control=is_control,
    )


async def _run_agent(
    db: AsyncSession,
    redis,
    tenant_id: str,
    request: HandshakeRequest,
) -> tuple[list[dict], str, str, bool]:
    """Run the LangGraph handshake agent."""
    from aos_api.agent.graph import handshake_graph

    initial_state = {
        "tenant_id": tenant_id,
        "visitor_context": request.context.model_dump(),
        "session_id": request.session_id,
        "db_session": db,
        "redis": redis,
    }

    result = await handshake_graph.ainvoke(initial_state)

    return (
        result.get("selected_slots", []),
        result.get("variation_id", "none"),
        result.get("vibe_segment", "default"),
        result.get("is_control", False),
    )


async def _run_fallback(
    db: AsyncSession,
    redis,
    tenant_id: str,
    request: HandshakeRequest,
) -> tuple[list[dict], str, str, bool]:
    """Fallback: rule-based classifier + simple variation selection."""
    vibe = vibe_classifier.classify(request.context)
    slots, variation_id, is_control = await variation_service.get_variations_for_vibe(
        db, redis, tenant_id, vibe
    )
    return slots, variation_id, vibe, is_control


async def _record_impressions(
    tenant_id: str,
    session_id: str,
    variation_id: str,
    slots: list[dict],
    referrer: str | None,
    utm_source: str | None,
    vibe: str,
):
    """Background task to record impression events."""
    from aos_api.db.session import async_session_factory

    redis = get_redis()
    async with async_session_factory() as db:
        await event_service.record_impressions(
            db=db,
            redis=redis,
            tenant_id=tenant_id,
            session_id=session_id,
            variation_id=variation_id,
            slots=slots,
            referrer=referrer,
            utm_source=utm_source,
            vibe=vibe,
        )
        await db.commit()
