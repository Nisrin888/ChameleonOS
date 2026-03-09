"""
LangGraph StateGraph definitions for Adaptive-OS.

Three separate graphs:
1. Handshake Graph (hot path): classify → select → (conditional) enrich → END
2. Optimization Graph (warm path): update MAB weights → END
3. Insight Graph (cold path): generate insights → END
"""
from langgraph.graph import StateGraph, END

from aos_api.agent.state import VibeAgentState, OptimizationState, InsightState
from aos_api.agent.nodes.vibe_classifier import classify_vibe
from aos_api.agent.nodes.variation_selector import select_variation
from aos_api.agent.nodes.background_enricher import enqueue_enrichment
from aos_api.agent.nodes.optimizer import update_mab_weights
from aos_api.agent.nodes.insight_generator import generate_insights


def _should_enrich(state: VibeAgentState) -> str:
    """Conditional edge: enrich if referrer is unknown."""
    if not state.get("is_known_referrer", True):
        return "enrich"
    return "end"


def build_handshake_graph():
    """
    Hot-path graph for handshake requests.

    Flow:
      classify_vibe → select_variation → (if unknown referrer) enqueue_enrichment → END
                                        → (if known referrer) END
    """
    graph = StateGraph(VibeAgentState)

    # Add nodes
    graph.add_node("classify_vibe", classify_vibe)
    graph.add_node("select_variation", select_variation)
    graph.add_node("enqueue_enrichment", enqueue_enrichment)

    # Set entry point
    graph.set_entry_point("classify_vibe")

    # Edges
    graph.add_edge("classify_vibe", "select_variation")

    # Conditional: only enrich if referrer is unknown
    graph.add_conditional_edges(
        "select_variation",
        _should_enrich,
        {"enrich": "enqueue_enrichment", "end": END},
    )
    graph.add_edge("enqueue_enrichment", END)

    return graph.compile()


def build_optimization_graph():
    """
    Warm-path graph for conversion event processing.

    Flow: update_mab_weights → END
    """
    graph = StateGraph(OptimizationState)

    graph.add_node("update_weights", update_mab_weights)
    graph.set_entry_point("update_weights")
    graph.add_edge("update_weights", END)

    return graph.compile()


def build_insight_graph():
    """
    Cold-path graph for scheduled insight generation.

    Flow: generate_insights → END
    """
    graph = StateGraph(InsightState)

    graph.add_node("generate_insights", generate_insights)
    graph.set_entry_point("generate_insights")
    graph.add_edge("generate_insights", END)

    return graph.compile()


# Pre-compiled graph instances (singletons)
handshake_graph = build_handshake_graph()
optimization_graph = build_optimization_graph()
insight_graph = build_insight_graph()
