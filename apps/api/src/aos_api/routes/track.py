"""
POST /v1/track — Event tracking endpoint.
Receives events from the SDK (impressions, clicks, conversions, form submits).
On conversion events, triggers MAB weight optimization via LangGraph.
"""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from aos_api.db.session import get_db
from aos_api.redis_client import get_redis
from aos_api.schemas.track import TrackEventRequest, TrackEventResponse
from aos_api.services import tenant_service, session_service, event_service

router = APIRouter()


@router.post("/track", response_model=TrackEventResponse)
async def track_event(
    request: TrackEventRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    redis = get_redis()

    # Validate tenant
    tenant = await tenant_service.get_tenant_by_public_key(db, request.public_key)
    if not tenant:
        raise HTTPException(status_code=404, detail="Invalid public key")

    # Resolve session for context
    session_data = await session_service.get_session(redis, request.session_id)
    vibe = session_data.get("vibe", "default") if session_data else "default"

    # Record event in background
    background_tasks.add_task(
        _record_and_optimize,
        str(tenant.id),
        request.session_id,
        request.variation_id,
        request.slot_id,
        request.event_type,
        request.event_name,
        vibe,
        request.metadata,
    )

    return TrackEventResponse(status="ok")


async def _record_and_optimize(
    tenant_id: str,
    session_id: str,
    variation_id: str | None,
    slot_id: str | None,
    event_type: str,
    event_name: str | None,
    vibe: str,
    metadata: dict | None,
):
    """Background task: persist event + update MAB on conversion."""
    from aos_api.db.session import async_session_factory

    redis = get_redis()
    async with async_session_factory() as db:
        # Record the event
        await event_service.record_event(
            db=db,
            redis=redis,
            tenant_id=tenant_id,
            session_id=session_id,
            variation_id=variation_id,
            slot_id=slot_id,
            event_type=event_type,
            event_name=event_name,
            referrer=None,
            utm_source=None,
            vibe_segment=vibe,
            metadata=metadata,
        )
        await db.commit()

        # On conversion, update MAB weights via the optimization graph
        if event_type == "conversion" and variation_id:
            try:
                from aos_api.agent.graph import optimization_graph

                await optimization_graph.ainvoke({
                    "tenant_id": tenant_id,
                    "variation_id": variation_id,
                    "event_type": "conversion",
                    "db_session": db,
                })
            except Exception as e:
                # Fallback: direct update if graph fails
                print(f"[AOS] MAB optimization graph error: {e}")
                from aos_api.agent.nodes.optimizer import update_mab_weights

                await update_mab_weights({
                    "variation_id": variation_id,
                    "event_type": "conversion",
                    "db_session": db,
                })
