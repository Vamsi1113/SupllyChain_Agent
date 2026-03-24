"""
LangGraph Workflow — Supply Chain Orchestrator.
Defines the multi-agent graph with conditional routing, retry logic,
human-in-the-loop approval, and max iteration guards.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Literal

from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from graph.state import SupplyChainState
from agents.inventory_agent import run_inventory_agent
from agents.risk_agent import run_risk_agent
from agents.supplier_agent import run_supplier_agent
from agents.decision_agent import run_decision_agent
from agents.validation_agent import run_validation_agent
from config import get_settings
from memory.vector_store import vector_store

logger = logging.getLogger(__name__)


# ── Helper ────────────────────────────────────────────────────────────────────

def _append_log(state: SupplyChainState, log: Any) -> list[dict]:
    existing = state.get("agent_logs", [])
    return existing + [log.model_dump(mode="json")]


# ── Graph Nodes ───────────────────────────────────────────────────────────────

def inventory_node(state: SupplyChainState) -> SupplyChainState:
    settings = get_settings()
    iteration = state.get("iteration_count", 0) + 1

    if iteration > settings.max_iterations:
        return {
            **state,
            "status": "failed",
            "error": f"Max iterations ({settings.max_iterations}) exceeded at inventory_node",
            "current_node": "inventory",
            "iteration_count": iteration,
        }

    part_id = state["part_id"]
    log, inventory_data = run_inventory_agent(part_id, state)

    return {
        **state,
        "inventory": inventory_data if inventory_data else state.get("inventory"),
        "agent_logs": _append_log(state, log),
        "current_node": "inventory",
        "iteration_count": iteration,
        "status": "running",
    }


def risk_node(state: SupplyChainState) -> SupplyChainState:
    log, risk_data = run_risk_agent(
        disruption_type=state.get("disruption_type", "supplier_failure"),
        context=state,
    )

    # Store incident in vector memory
    if risk_data:
        vector_store.store_incident(
            run_id=state.get("run_id", "unknown"),
            part_id=state["part_id"],
            disruption_type=state.get("disruption_type", "unknown"),
            severity=risk_data.get("severity", "medium"),
            summary=risk_data.get("summary", ""),
        )

    return {
        **state,
        "risk_report": risk_data if risk_data else state.get("risk_report"),
        "agent_logs": _append_log(state, log),
        "current_node": "risk",
        "status": "running",
    }


def supplier_node(state: SupplyChainState) -> SupplyChainState:
    tried = state.get("tried_suppliers", [])

    # Add current supplier from inventory to tried list
    inventory = state.get("inventory", {})
    current_supplier = inventory.get("current_supplier_id", "")
    if current_supplier and current_supplier not in tried:
        tried = tried + [current_supplier]

    log, suppliers = run_supplier_agent(
        part_id=state["part_id"],
        tried_suppliers=tried,
        quantity_needed=state.get("quantity_needed", 100),
        state=state,
    )

    # Update tried list with newly searched suppliers
    new_supplier_ids = [s["supplier_id"] for s in suppliers]
    updated_tried = list(set(tried + new_supplier_ids))

    return {
        **state,
        "suppliers": suppliers,
        "tried_suppliers": updated_tried,
        "agent_logs": _append_log(state, log),
        "current_node": "supplier",
        "status": "running",
    }


def decision_node(state: SupplyChainState) -> SupplyChainState:
    log, decision = run_decision_agent(
        part_id=state["part_id"],
        suppliers=state.get("suppliers", []),
        risk_report=state.get("risk_report", {}),
        inventory=state.get("inventory", {}),
        quantity_needed=state.get("quantity_needed", 100),
        state=state,
    )

    return {
        **state,
        "decision": decision if decision else state.get("decision"),
        "agent_logs": _append_log(state, log),
        "current_node": "decision",
        "status": "running",
    }


def validation_node(state: SupplyChainState) -> SupplyChainState:
    retry_count = state.get("retry_count", 0)
    log, validation_result = run_validation_agent(
        inventory=state.get("inventory"),
        suppliers=state.get("suppliers", []),
        risk_report=state.get("risk_report"),
        decision=state.get("decision"),
        retry_count=retry_count,
        state=state,
    )

    is_valid = validation_result.valid
    new_retry_count = retry_count if is_valid else retry_count + 1

    return {
        **state,
        "validation_result": validation_result.model_dump(mode="json"),
        "agent_logs": _append_log(state, log),
        "current_node": "validation",
        "status": "running",
        "retry_count": new_retry_count,
    }


def approval_wait_node(state: SupplyChainState) -> SupplyChainState:
    """Pauses execution and waits for human approval."""
    settings = get_settings()

    decision = state.get("decision", {})
    recommended = decision.get("recommended_supplier", {})
    supplier_name = recommended.get("supplier_name", "Unknown Supplier")
    total_cost = decision.get("estimated_total_cost", 0)
    run_id = state.get("run_id", "")

    # Send notification (non-blocking — actual waiting is managed by the API layer)
    try:
        from tools.notification_tool import send_notification
        send_notification.invoke({
            "message": (
                f"Supply chain action requires approval for part {state['part_id']}. "
                f"Recommended supplier: {supplier_name}. "
                f"Estimated cost: ${total_cost:,.2f}."
            ),
            "action_url": f"{settings.base_url}/approve",
            "run_id": run_id,
            "decision_summary": decision.get("reason", ""),
        })
    except Exception as e:
        logger.warning(f"Notification failed in approval_wait_node: {e}")

    return {
        **state,
        "approval_status": "pending",
        "current_node": "approval",
        "status": "awaiting_approval",
    }


def execute_node(state: SupplyChainState) -> SupplyChainState:
    """Executes the approved procurement action."""
    decision = state.get("decision", {})
    recommended = decision.get("recommended_supplier", {})

    logger.info(
        f"[EXECUTE] Run {state.get('run_id')}: Placing order for {state['part_id']} "
        f"from {recommended.get('supplier_name', 'N/A')} — "
        f"qty {decision.get('quantity_to_order')}, "
        f"total ${decision.get('estimated_total_cost', 0):,.2f}"
    )

    return {
        **state,
        "status": "completed",
        "current_node": "execute",
    }


def human_fallback_node(state: SupplyChainState) -> SupplyChainState:
    """Called when all automated attempts fail — escalates to human."""
    logger.warning(f"[FALLBACK] Run {state.get('run_id')}: Escalating to human review for {state['part_id']}")

    return {
        **state,
        "status": "human_fallback",
        "current_node": "human_fallback",
        "error": state.get("error") or "Automated resolution failed — manual intervention required",
    }


# ── Conditional Routers ───────────────────────────────────────────────────────

def route_after_validation(
    state: SupplyChainState,
) -> Literal["decision", "supplier", "human_fallback"]:
    """Route based on validation result and retry count."""
    settings = get_settings()
    vr = state.get("validation_result", {})
    retry_count = state.get("retry_count", 0)

    if vr.get("valid"):
        return "decision"

    errors = vr.get("errors", [])
    
    # Check if we should retry specific steps
    if retry_count < settings.max_retries:
        # If suppliers are the problem, try searching again
        if any("supplier" in e.lower() for e in errors):
            return "supplier"
        
        # If decision is the problem, retry decision logic
        if any("decision" in e.lower() for e in errors):
            return "decision"
            
        # If risk is the problem, retry risk analysis
        if any("risk" in e.lower() for e in errors):
            return "risk"

    return "human_fallback"


def route_after_approval(
    state: SupplyChainState,
) -> Literal["execute", "human_fallback"]:
    """Route based on human approval decision."""
    approval = state.get("approval_status", "pending")
    if approval == "approved":
        return "execute"
    elif approval == "rejected":
        return "human_fallback"
    # Still pending — stay at approval node (graph will re-enter)
    return "human_fallback"


def route_after_decision(
    state: SupplyChainState,
) -> Literal["approval", "human_fallback"]:
    """Require approval if decision exists, else fallback."""
    decision = state.get("decision")
    if decision and decision.get("recommended_supplier"):
        return "approval"
    return "human_fallback"


# ── Graph Builder ─────────────────────────────────────────────────────────────

def build_workflow() -> StateGraph:
    """Builds and returns the compiled LangGraph StateGraph."""
    graph = StateGraph(SupplyChainState)

    # Register nodes
    graph.add_node("inventory", inventory_node)
    graph.add_node("risk", risk_node)
    graph.add_node("supplier", supplier_node)
    graph.add_node("validation", validation_node)
    graph.add_node("decision", decision_node)
    graph.add_node("approval", approval_wait_node)
    graph.add_node("execute", execute_node)
    graph.add_node("human_fallback", human_fallback_node)

    # Linear entry flow: inventory → risk → supplier → validation
    graph.add_edge(START, "inventory")
    graph.add_edge("inventory", "risk")
    graph.add_edge("risk", "supplier")
    graph.add_edge("supplier", "validation")

    # Conditional: validation → decision | supplier (retry) | human_fallback
    graph.add_conditional_edges(
        "validation",
        route_after_validation,
        {
            "decision": "decision",
            "supplier": "supplier",
            "human_fallback": "human_fallback",
        },
    )

    # Conditional: decision → approval | human_fallback
    graph.add_conditional_edges(
        "decision",
        route_after_decision,
        {
            "approval": "approval",
            "human_fallback": "human_fallback",
        },
    )

    # Conditional: approval → execute | human_fallback
    graph.add_conditional_edges(
        "approval",
        route_after_approval,
        {
            "execute": "execute",
            "human_fallback": "human_fallback",
        },
    )

    # Terminal nodes
    graph.add_edge("execute", END)
    graph.add_edge("human_fallback", END)

    return graph


def compile_workflow():
    """Returns a compiled, checkpointed LangGraph app."""
    graph = build_workflow()
    memory = MemorySaver()
    return graph.compile(checkpointer=memory, interrupt_after=["approval"])
