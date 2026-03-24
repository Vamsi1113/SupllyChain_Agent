"""
LangGraph shared state definition for Supply Chain Orchestrator.
TypedDict used as the GraphState — all nodes read/write from this.
"""

from __future__ import annotations

from typing import Any, Optional
from typing_extensions import TypedDict


class SupplyChainState(TypedDict, total=False):
    # ── Run metadata ──────────────────────────────────────────────────────────
    run_id: str
    part_id: str
    disruption_type: str
    quantity_needed: int
    priority: str
    notes: Optional[str]

    # ── Agent outputs ─────────────────────────────────────────────────────────
    inventory: Optional[dict[str, Any]]          # from InventoryAgent
    suppliers: list[dict[str, Any]]              # from SupplierAgent
    risk_report: Optional[dict[str, Any]]        # from RiskAgent
    decision: Optional[dict[str, Any]]           # from DecisionAgent
    validation_result: Optional[dict[str, Any]]  # from ValidationAgent

    # ── Flow control ──────────────────────────────────────────────────────────
    tried_suppliers: list[str]          # Track to avoid repeats
    retry_count: int                    # Validation retries
    iteration_count: int                # Graph loop counter
    current_node: str                   # Active node name
    status: str                         # RunStatus value

    # ── Human-in-the-loop ─────────────────────────────────────────────────────
    approval_status: str                # ApprovalStatus value
    approval_comments: Optional[str]

    # ── Logging ───────────────────────────────────────────────────────────────
    agent_logs: list[dict[str, Any]]    # Serialized AgentLog objects
    error: Optional[str]
