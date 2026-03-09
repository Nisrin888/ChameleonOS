"""
Dashboard API endpoints.
GET /v1/dashboard/performance — returns summary + per-source breakdown.
GET /v1/dashboard/insights — AI-generated Profit Pulse summary.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, case, and_
from sqlalchemy.ext.asyncio import AsyncSession

from aos_api.db.models import Tenant, Event, Variation, Slot
from aos_api.db.session import get_db
from aos_api.schemas.dashboard import DashboardData, DashboardSummary, PerformanceRow

router = APIRouter()


@router.get("/performance", response_model=DashboardData)
async def get_performance(
    public_key: str = Query(..., description="Tenant public key"),
    db: AsyncSession = Depends(get_db),
):
    # Resolve tenant
    tenant_result = await db.execute(
        select(Tenant).where(Tenant.public_key == public_key)
    )
    tenant = tenant_result.scalar_one_or_none()
    if not tenant:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Tenant not found")

    tenant_id = tenant.id

    # Get all impression events grouped by vibe_segment + variation_id
    impression_query = (
        select(
            Event.vibe_segment,
            Event.variation_id,
            Event.utm_source,
            func.count().label("impressions"),
        )
        .where(
            Event.tenant_id == tenant_id,
            Event.event_type == "impression",
        )
        .group_by(Event.vibe_segment, Event.variation_id, Event.utm_source)
    )
    impression_result = await db.execute(impression_query)
    impression_rows = impression_result.all()

    # Get all conversion events grouped similarly
    conversion_query = (
        select(
            Event.vibe_segment,
            Event.variation_id,
            Event.utm_source,
            func.count().label("conversions"),
        )
        .where(
            Event.tenant_id == tenant_id,
            Event.event_type == "conversion",
        )
        .group_by(Event.vibe_segment, Event.variation_id, Event.utm_source)
    )
    conversion_result = await db.execute(conversion_query)
    conversion_rows = conversion_result.all()

    # Build lookup: (vibe, variation_id, utm_source) -> conversions
    conv_map: dict[tuple, int] = {}
    for row in conversion_rows:
        key = (row.vibe_segment, str(row.variation_id), row.utm_source)
        conv_map[key] = row.conversions

    # Get variation metadata
    var_result = await db.execute(
        select(Variation).join(Slot).where(Slot.tenant_id == tenant_id)
    )
    variations = {str(v.id): v for v in var_result.scalars().all()}

    # Build performance rows
    rows: list[PerformanceRow] = []
    total_impressions = 0
    total_conversions = 0
    control_impressions = 0
    control_conversions = 0

    for imp_row in impression_rows:
        vibe = imp_row.vibe_segment or "default"
        var_id = str(imp_row.variation_id) if imp_row.variation_id else "unknown"
        source = imp_row.utm_source or "direct"
        impressions = imp_row.impressions
        key = (imp_row.vibe_segment, var_id, imp_row.utm_source)
        conversions = conv_map.get(key, 0)

        var = variations.get(var_id)
        var_name = var.name if var else "Unknown"
        is_control = var.is_control if var else False

        cvr = conversions / impressions if impressions > 0 else 0.0

        total_impressions += impressions
        total_conversions += conversions
        if is_control:
            control_impressions += impressions
            control_conversions += conversions

        rows.append(PerformanceRow(
            traffic_source=source,
            vibe=vibe,
            variation_name=var_name,
            variation_id=var_id,
            impressions=impressions,
            conversions=conversions,
            cvr=round(cvr, 4),
            is_control=is_control,
        ))

    # Calculate summary
    overall_cvr = total_conversions / total_impressions if total_impressions > 0 else 0.0
    control_cvr = (
        control_conversions / control_impressions if control_impressions > 0 else 0.0
    )
    lift = (
        ((overall_cvr - control_cvr) / control_cvr * 100)
        if control_cvr > 0
        else 0.0
    )

    return DashboardData(
        summary=DashboardSummary(
            total_impressions=total_impressions,
            total_conversions=total_conversions,
            overall_cvr=round(overall_cvr, 4),
            control_cvr=round(control_cvr, 4),
            lift_vs_control=round(lift, 1),
        ),
        rows=rows,
        last_updated=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/insights")
async def get_insights(
    public_key: str = Query(..., description="Tenant public key"),
    days: int = Query(7, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
):
    """Generate AI-powered Profit Pulse insights."""
    from fastapi import HTTPException

    # Resolve tenant
    tenant_result = await db.execute(
        select(Tenant).where(Tenant.public_key == public_key)
    )
    tenant = tenant_result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    from aos_api.agent.nodes.insight_generator import generate_insights

    result = await generate_insights({
        "tenant_id": tenant.id,
        "db_session": db,
        "days": days,
    })

    return {
        "insights": result.get("insights", ""),
        "anomalies": result.get("anomalies", []),
        "error": result.get("error"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
