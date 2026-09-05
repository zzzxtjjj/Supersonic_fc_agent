from langgraph.graph import StateGraph, START, END

from agent.workflow.state import AgentState

from agent.workflow.nodes import (
    llm_node,
    tool_node,
    verify_tool_results_node,
    recovery_node,
    grounding_recovery_node,
    clarify_node,
    abort_node,
    verify_evidence_node,
    evidence_insufficient_node,
)

from agent.workflow.routers import (
    route_after_llm,
    route_after_verifier,
    route_after_evidence,
)


builder = StateGraph(AgentState)

# =========================
# 注册 Nodes
# =========================

builder.add_node("llm_node", llm_node)

builder.add_node("tool_node", tool_node)

builder.add_node(
    "verify_tool_results_node",
    verify_tool_results_node
)

builder.add_node(
    "verify_evidence_node",
    verify_evidence_node
)

builder.add_node(
    "recovery_node",
    recovery_node
)

builder.add_node(
    "grounding_recovery_node",
    grounding_recovery_node
)

builder.add_node(
    "clarify_node",
    clarify_node
)

builder.add_node(
    "abort_node",
    abort_node
)

builder.add_node(
    "evidence_insufficient_node",
    evidence_insufficient_node
)


# =========================
# START → LLM
# =========================

builder.add_edge(
    START,
    "llm_node"
)


# =========================
# LLM → Tool / END
# =========================

builder.add_conditional_edges(
    "llm_node",
    route_after_llm,
    {
        "tools": "tool_node",
        "end": END,
        "ungrounded": "grounding_recovery_node",
        "max_steps": "abort_node",
    }
)


# =========================
# Tool → Execution Verifier
# =========================

builder.add_edge(
    "tool_node",
    "verify_tool_results_node"
)


# =========================
# Execution Verifier
# =========================

builder.add_conditional_edges(
    "verify_tool_results_node",
    route_after_verifier,
    {
        "passed": "verify_evidence_node",
        "clarify": "clarify_node",
        "retry": "recovery_node",
        "abort": "abort_node",
    }
)


# =========================
# Evidence Verifier
# =========================

builder.add_conditional_edges(
    "verify_evidence_node",
    route_after_evidence,
    {
        "supported": "llm_node",
        "insufficient": "evidence_insufficient_node",
    }
)


# =========================
# Recovery → LLM
# =========================

builder.add_edge(
    "recovery_node",
    "llm_node"
)

builder.add_edge(
    "grounding_recovery_node",
    "llm_node"
)


# =========================
# Terminal Nodes
# =========================

builder.add_edge(
    "clarify_node",
    END
)

builder.add_edge(
    "abort_node",
    END
)

builder.add_edge(
    "evidence_insufficient_node",
    END
)


# =========================
# Compile
# =========================

graph = builder.compile()
