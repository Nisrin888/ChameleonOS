"""
Node 5: Insight Generator — Detects patterns and anomalies.

Called on a schedule (daily) or on-demand from dashboard.
Uses Claude Haiku for fast, cheap summarization.

Generates:
- Top performing variation per traffic source
- Anomaly detection (sudden conversion drop)
- "Profit Pulse" summary text
"""
import json
from datetime import datetime, timezone, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from aos_api.agent.state import InsightState
from aos_api.db.models import Event, Variation, Slot


INSIGHT_PROMPT = """You are an analytics assistant for an A/B testing platform.
Analyze these performance results and provide actionable insights.

Data (last {days} days):
{stats_json}

Provide your response in this exact format:

**Top Performers:**
- [List the best performing variation per traffic source with CVR]

**Anomalies:**
- [List any concerning drops, spikes, or unusual patterns. Say "None detected" if all is normal]

**Profit Pulse Summary:**
[Write a 2-sentence summary suitable for a weekly email to the merchant. Be specific with numbers. Start with "This week..."]
"""


async def generate_insights(state: InsightState) -> dict:
    """Generate performance insights using Claude Haiku."""
    tenant_id = state["tenant_id"]
    db: AsyncSession = state["db_session"]
    days = state.get("days", 7)

    # Fetch recent stats
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # Get impressions by variation
    imp_query = (
        select(
            Event.vibe_segment,
            Event.variation_id,
            Event.utm_source,
            func.count().label("count"),
        )
        .where(
            Event.tenant_id == tenant_id,
            Event.event_type == "impression",
            Event.created_at >= cutoff,
        )
        .group_by(Event.vibe_segment, Event.variation_id, Event.utm_source)
    )
    imp_result = await db.execute(imp_query)

    # Get conversions by variation
    conv_query = (
        select(
            Event.variation_id,
            Event.utm_source,
            func.count().label("count"),
        )
        .where(
            Event.tenant_id == tenant_id,
            Event.event_type == "conversion",
            Event.created_at >= cutoff,
        )
        .group_by(Event.variation_id, Event.utm_source)
    )
    conv_result = await db.execute(conv_query)

    # Build stats dict
    conv_map = {}
    for row in conv_result.all():
        key = (str(row.variation_id), row.utm_source or "direct")
        conv_map[key] = row.count

    # Get variation names
    var_result = await db.execute(select(Variation).join(Slot).where(Slot.tenant_id == tenant_id))
    var_names = {str(v.id): v.name for v in var_result.scalars().all()}

    stats = []
    for row in imp_result.all():
        var_id = str(row.variation_id) if row.variation_id else "unknown"
        source = row.utm_source or "direct"
        impressions = row.count
        conversions = conv_map.get((var_id, source), 0)
        cvr = conversions / impressions if impressions > 0 else 0

        stats.append({
            "source": source,
            "vibe": row.vibe_segment or "default",
            "variation": var_names.get(var_id, "Unknown"),
            "impressions": impressions,
            "conversions": conversions,
            "cvr": round(cvr * 100, 2),
        })

    if not stats:
        return {
            "insights": "No data available for the selected period.",
            "anomalies": [],
        }

    # Call Claude Haiku for insights
    try:
        from langchain_anthropic import ChatAnthropic
        from aos_api.config import settings

        llm = ChatAnthropic(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            api_key=settings.anthropic_api_key,
        )
        prompt = INSIGHT_PROMPT.format(
            days=days,
            stats_json=json.dumps(stats, indent=2),
        )
        result = await llm.ainvoke(prompt)
        return {
            "insights": result.content,
            "anomalies": [],  # Could parse from response
        }
    except Exception as e:
        # Fallback: generate basic insights without AI
        sorted_stats = sorted(stats, key=lambda x: x["cvr"], reverse=True)
        top = sorted_stats[0] if sorted_stats else None
        summary = f"Top performer: {top['variation']} from {top['source']} at {top['cvr']}% CVR." if top else "No data."
        return {
            "insights": summary,
            "anomalies": [],
            "error": str(e),
        }
