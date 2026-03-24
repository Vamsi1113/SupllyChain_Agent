"""
Decision Agent — selects the best supplier based on cost, ETA, and risk score.
Uses LLM reasoning + deterministic scoring to produce a structured Decision.
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from config import get_settings
from utils.llm import get_llm
from schemas.supply_chain import AgentLog, Decision, ReActStep, Supplier
from memory.vector_store import vector_store

logger = logging.getLogger(__name__)


def _compute_supplier_score(
    supplier: dict[str, Any],
    max_price: float,
    max_lead: float,
    risk_score: float,
) -> dict[str, float]:
    """Deterministic composite scoring: cost (30%), ETA (30%), risk (20%), reliability (20%)."""
    price_norm = 1.0 - (supplier["unit_price"] / max_price) if max_price > 0 else 0
    lead_norm = 1.0 - (supplier["lead_time_days"] / max_lead) if max_lead > 0 else 0
    risk_norm = 1.0 - (risk_score / 10.0)
    reliability = supplier.get("reliability_score", 0.8)

    cost_score = round(price_norm * 10, 2)
    eta_score = round(lead_norm * 10, 2)
    risk_score_adj = round(risk_norm * 10, 2)
    composite = round(
        0.30 * cost_score + 0.30 * eta_score + 0.20 * risk_score_adj + 0.20 * reliability * 10,
        3,
    )

    return {
        "cost_score": cost_score,
        "eta_score": eta_score,
        "risk_score": risk_score_adj,
        "composite_score": composite,
    }


def run_decision_agent(
    part_id: str,
    suppliers: list[dict[str, Any]],
    risk_report: dict[str, Any],
    inventory: dict[str, Any],
    quantity_needed: int,
    state: dict[str, Any],
) -> tuple[AgentLog, dict[str, Any]]:
    """
    Runs the decision agent to select the optimal supplier.
    Returns an AgentLog and a Decision dict.
    """
    settings = get_settings()
    start_time = time.time()
    log = AgentLog(agent_name="DecisionAgent")

    try:
        if not suppliers:
            log.error = "No suppliers available for decision"
            log.steps.append(ReActStep(
                thought="No suppliers were provided to evaluate",
                action="evaluate_suppliers",
                observation="Empty supplier list — cannot make decision",
            ))
            log.duration_ms = (time.time() - start_time) * 1000
            return log, {}

        risk_score_val = float(risk_report.get("severity_score", 5.0))
        max_price = max(s["unit_price"] for s in suppliers)
        max_lead = max(s["lead_time_days"] for s in suppliers)

        # Score all suppliers
        scored = []
        for sup in suppliers:
            scores = _compute_supplier_score(sup, max_price, max_lead, risk_score_val)
            scored.append({**sup, **scores})

        # Sort by composite score descending
        scored.sort(key=lambda x: x["composite_score"], reverse=True)
        best = scored[0]

        log.steps.append(ReActStep(
            thought=(
                f"Evaluating {len(suppliers)} suppliers. Risk severity score: {risk_score_val}/10. "
                f"Weighting: cost 30%, ETA 30%, risk 20%, reliability 20%."
            ),
            action="evaluate_suppliers",
            observation=json.dumps([
                {"id": s["supplier_id"], "composite": s["composite_score"]} for s in scored
            ]),
        ))

        # LLM reasoning for the final justification
        llm = get_llm()
        reason = f"Supplier {best['supplier_name']} selected based on optimal composite score of {best['composite_score']}."

        try:
            summary_prompt = (
                f"You are a supply chain decision analyst. Given these scored suppliers:\n"
                f"{json.dumps(scored[:3], indent=2)}\n\n"
                f"Risk context: {risk_report.get('summary', 'N/A')}\n"
                f"Part: {part_id}, Quantity needed: {quantity_needed}\n\n"
                f"In ONE concise sentence, explain why {best['supplier_name']} is the best choice."
            )

            reason_response = llm.invoke([
                SystemMessage(content="You are a supply chain decision analyst. Be concise and factual."),
                HumanMessage(content=summary_prompt),
            ])
            if hasattr(reason_response, "content") and reason_response.content:
                reason = reason_response.content.strip()
        except Exception as llm_exc:
            logger.warning(f"DecisionAgent LLM justification failed: {llm_exc}. Using fallback reason.")

        log.steps.append(ReActStep(
            thought=f"Best supplier is {best['supplier_name']} with composite score {best['composite_score']}",
            action="generate_justification",
            observation=reason,
        ))

        # Build Decision object
        best_supplier = Supplier(
            supplier_id=best["supplier_id"],
            supplier_name=best["supplier_name"],
            unit_price=best["unit_price"],
            lead_time_days=best["lead_time_days"],
            reliability_score=best["reliability_score"],
            location=best["location"],
            capacity=best["capacity"],
            certifications=best.get("certifications", []),
            contact_email=best.get("contact_email", ""),
        )

        decision = Decision(
            recommended_supplier=best_supplier,
            reason=reason,
            cost_score=best["cost_score"],
            eta_score=best["eta_score"],
            risk_score=best["risk_score"],
            composite_score=best["composite_score"],
            estimated_total_cost=round(best["unit_price"] * quantity_needed, 2),
            quantity_to_order=quantity_needed,
            alternatives_considered=[s["supplier_id"] for s in scored[1:4]],
        )

        # Store decision in vector memory
        try:
            vector_store.store_decision(
                run_id=state.get("run_id", "unknown"),
                part_id=part_id,
                supplier_id=best_supplier.supplier_id,
                supplier_name=best_supplier.supplier_name,
                score=best["composite_score"],
                reason=reason,
            )
        except Exception as db_exc:
            logger.warning(f"DecisionAgent failed to store in vector DB: {db_exc}")

        decision_dict = decision.model_dump(mode="json")
        log.output = decision_dict
        log.duration_ms = (time.time() - start_time) * 1000
        return log, decision_dict

    except Exception as exc:
        logger.error(f"DecisionAgent failed: {exc}")
        log.error = str(exc)
        log.steps.append(ReActStep(
            thought="Error during decision evaluation",
            action="evaluate_suppliers",
            observation=str(exc),
        ))
        log.duration_ms = (time.time() - start_time) * 1000
        return log, {}
