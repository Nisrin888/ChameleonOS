"""
Agent state definitions for LangGraph.
Each graph operates on a typed state dictionary.
"""
from typing import TypedDict, Optional


class VibeAgentState(TypedDict, total=False):
    """State for the handshake graph (hot path)."""

    # --- Input ---
    tenant_id: str
    visitor_context: dict  # Matches VisitorContext schema
    session_id: Optional[str]

    # --- DB/Redis handles (injected at invocation) ---
    db_session: object  # AsyncSession
    redis: object

    # --- Vibe Classification ---
    vibe_segment: Optional[str]
    vibe_confidence: Optional[float]
    is_known_referrer: Optional[bool]

    # --- Variation Selection ---
    selected_slots: Optional[list]  # List of SlotVariation dicts
    variation_id: Optional[str]  # UUID for attribution
    is_control: Optional[bool]

    # --- Error ---
    error: Optional[str]


class OptimizationState(TypedDict, total=False):
    """State for the optimization graph (warm path — on conversion)."""

    tenant_id: str
    variation_id: str
    event_type: str  # "conversion"
    db_session: object
    updated: Optional[bool]


class InsightState(TypedDict, total=False):
    """State for the insight generation graph (cold path — scheduled)."""

    tenant_id: str
    db_session: object
    days: int  # lookback window
    insights: Optional[str]  # Generated text
    anomalies: Optional[list]
