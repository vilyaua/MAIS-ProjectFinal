"""LangGraph StateGraph for the Dev Team workflow.

Graph:
    START -> ba_node -> hitl_gate -> (approved?)
                                      |- NO  -> ba_node (with feedback)
                                      +- YES -> dev_node -> qa_node -> (verdict?)
                                                                        |- REVISION_NEEDED & iter<5 -> dev_node
                                                                        +- APPROVED or iter>=5 -> END
"""

import logging

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, StateGraph

from config import Settings
from nodes import ba_node, dev_node, hitl_gate, qa_node
from state import DevTeamState

logger = logging.getLogger("graph")
settings = Settings()


def _route_after_hitl(state: DevTeamState) -> str:
    """Route after HITL gate: back to BA or forward to Developer."""
    if state.get("spec_approved"):
        return "dev_node"
    return "ba_node"


def _route_after_qa(state: DevTeamState) -> str:
    """Route after QA: back to Developer or end."""
    review = state.get("review")
    iteration = state.get("iteration", 0)

    if review and review.verdict == "APPROVED":
        logger.info("QA APPROVED — finishing pipeline")
        return END

    if iteration >= settings.max_qa_iterations:
        logger.warning(
            "Max QA iterations (%d) reached — finishing with last review",
            settings.max_qa_iterations,
        )
        return END

    logger.info("QA REVISION_NEEDED — returning to Developer (iteration %d)", iteration)
    return "dev_node"


def build_graph() -> StateGraph:
    """Build and compile the Dev Team StateGraph."""
    graph = StateGraph(DevTeamState)

    # Add nodes
    graph.add_node("ba_node", ba_node)
    graph.add_node("hitl_gate", hitl_gate)
    graph.add_node("dev_node", dev_node)
    graph.add_node("qa_node", qa_node)

    # Edges
    graph.set_entry_point("ba_node")
    graph.add_edge("ba_node", "hitl_gate")

    # HITL gate: conditional routing
    graph.add_conditional_edges("hitl_gate", _route_after_hitl, {
        "ba_node": "ba_node",
        "dev_node": "dev_node",
    })

    # Dev -> QA
    graph.add_edge("dev_node", "qa_node")

    # QA: conditional routing (loop or end)
    graph.add_conditional_edges("qa_node", _route_after_qa, {
        "dev_node": "dev_node",
        END: END,
    })

    # Compile with checkpointer for HITL interrupt/resume
    checkpointer = InMemorySaver()
    compiled = graph.compile(checkpointer=checkpointer)

    logger.info("Dev Team graph compiled successfully")
    return compiled
