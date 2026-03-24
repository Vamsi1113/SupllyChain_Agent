"""
Validation Agent — validates all agent outputs using Pydantic schemas.
On failure: logs errors and signals the graph to retry or fallback.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Optional

from schemas.supply_chain import (
    AgentLog,
    Decision,
    InventoryItem,
    ReActStep,
    RiskReport,
    Supplier,
    ValidationResult,
)

logger = logging.getLogger(__name__)


def run_validation_agent(
    inventory: Optional[dict[str, Any]],
    suppliers: list[dict[str, Any]],
    risk_report: Optional[dict[str, Any]],
    decision: Optional[dict[str, Any]],
    retry_count: int,
    state: dict[str, Any],
) -> tuple[AgentLog, ValidationResult]:
    """
    Validates all agent outputs using Pydantic schemas.
    Returns AgentLog and a ValidationResult with pass/fail status and error list.
    """
    start_time = time.time()
    log = AgentLog(agent_name="ValidationAgent")
    errors: list[str] = []

    # ── Validate Inventory ────────────────────────────────────────────────────
    log.steps.append(ReActStep(
        thought="Validating inventory data structure and field constraints",
        action="validate_inventory",
        observation="Checking part_id format, stock levels, and supplier ID pattern",
    ))

    if inventory:
        try:
            InventoryItem(**inventory)
            log.steps[-1].observation = f"✓ Inventory valid for part {inventory.get('part_id')}"
        except Exception as e:
            err = f"Inventory validation failed: {str(e)}"
            errors.append(err)
            log.steps[-1].observation = f"✗ {err}"
    else:
        errors.append("Inventory data is missing")
        log.steps[-1].observation = "✗ Inventory data absent"

    # ── Validate Suppliers ────────────────────────────────────────────────────
    log.steps.append(ReActStep(
        thought="Validating each supplier record — ID pattern, price > 0, ETA >= 1",
        action="validate_suppliers",
        observation="Starting supplier validation...",
    ))

    if suppliers:
        invalid_sups = []
        for sup in suppliers:
            try:
                Supplier(**sup)
            except Exception as e:
                invalid_sups.append(f"Supplier {sup.get('supplier_id', 'UNKNOWN')}: {str(e)}")

        if invalid_sups:
            errors.extend(invalid_sups)
            log.steps[-1].observation = f"✗ {len(invalid_sups)} invalid supplier(s): {invalid_sups[0]}"
        else:
            log.steps[-1].observation = f"✓ All {len(suppliers)} suppliers valid"
    else:
        errors.append("No suppliers found — cannot proceed")
        log.steps[-1].observation = "✗ Supplier list is empty"

    # ── Validate Risk Report ──────────────────────────────────────────────────
    log.steps.append(ReActStep(
        thought="Validating risk report structure",
        action="validate_risk_report",
        observation="Checking severity score range (0-10) and required fields",
    ))

    if risk_report:
        try:
            RiskReport(**risk_report)
            log.steps[-1].observation = f"✓ Risk report valid, severity: {risk_report.get('severity')}"
        except Exception as e:
            err = f"Risk report validation failed: {str(e)}"
            errors.append(err)
            log.steps[-1].observation = f"✗ {err}"
    else:
        # Risk report is optional — log warning but don't fail
        log.steps[-1].observation = "⚠ Risk report missing — proceeding without risk context"

    # ── Validate Decision ─────────────────────────────────────────────────────
    log.steps.append(ReActStep(
        thought="Validating final decision — supplier, scores, total cost, quantity",
        action="validate_decision",
        observation="Checking composite score bounds and required fields",
    ))

    if decision:
        try:
            Decision(**decision)
            recommended = decision.get("recommended_supplier", {})
            log.steps[-1].observation = (
                f"✓ Decision valid — recommended: {recommended.get('supplier_name')}, "
                f"composite score: {decision.get('composite_score')}"
            )
        except Exception as e:
            err = f"Decision validation failed: {str(e)}"
            errors.append(err)
            log.steps[-1].observation = f"✗ {err}"
    else:
        # Decision is optional at this stage of the graph
        log.steps[-1].observation = "◌ Decision not yet generated — skipping validation"

    # ── Final result ──────────────────────────────────────────────────────────
    is_valid = len(errors) == 0
    validation_result = ValidationResult(
        valid=is_valid,
        errors=errors,
        retry_count=retry_count,
    )

    log.output = {
        "valid": is_valid,
        "error_count": len(errors),
        "errors": errors,
        "retry_count": retry_count,
    }
    log.duration_ms = (time.time() - start_time) * 1000

    if is_valid:
        logger.info(f"ValidationAgent: All checks passed (retry_count={retry_count})")
    else:
        logger.warning(f"ValidationAgent: {len(errors)} error(s) found: {errors}")

    return log, validation_result
