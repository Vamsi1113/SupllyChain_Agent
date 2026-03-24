"""
FastAPI routes for Supply Chain Orchestrator AI System.
- POST /run-agent: starts a new orchestration run
- GET /status/{run_id}: retrieves current run state and agent logs
- POST /approve: accepts or rejects the recommended procurement action
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from fastapi.responses import JSONResponse

from config import get_settings
from graph.workflow import compile_workflow
from graph.state import SupplyChainState
from schemas.supply_chain import (
    ApprovalRequest,
    ApprovalStatus,
    RunAgentRequest,
    RunAgentResponse,
    RunStatus,
    StatusResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# ── In-memory run store (replace with Redis/DB in production) ─────────────────
_runs: dict[str, dict[str, Any]] = {}
_workflow_app = None


def get_workflow():
    global _workflow_app
    if _workflow_app is None:
        _workflow_app = compile_workflow()
    return _workflow_app


# ── Background task executor ───────────────────────────────────────────────────

async def _execute_run(run_id: str, initial_state: SupplyChainState) -> None:
    """Runs the LangGraph workflow asynchronously in the background."""
    settings = get_settings()
    app = get_workflow()
    config = {"configurable": {"thread_id": run_id}}

    try:
        _runs[run_id]["status"] = RunStatus.running

        # Stream events from the graph (runs until interrupt or END)
        async for event in app.astream(initial_state, config=config, stream_mode="values"):
            # Merge each emitted state into our run store
            _runs[run_id].update({
                "status": event.get("status", RunStatus.running),
                "current_node": event.get("current_node"),
                "agent_logs": event.get("agent_logs", []),
                "inventory": event.get("inventory"),
                "risk_report": event.get("risk_report"),
                "decision": event.get("decision"),
                "approval_status": event.get("approval_status", ApprovalStatus.pending),
                "validation_result": event.get("validation_result"),
                "iteration_count": event.get("iteration_count", 0),
                "error": event.get("error"),
                "tried_suppliers": event.get("tried_suppliers", []),
            })

            # Stop streaming if interrupted for approval
            current_status = _runs[run_id]["status"]
            if current_status in (RunStatus.awaiting_approval, RunStatus.completed,
                                   RunStatus.failed, RunStatus.human_fallback):
                break

    except Exception as exc:
        logger.error(f"Run {run_id} failed: {exc}")
        _runs[run_id].update({
            "status": RunStatus.failed,
            "error": str(exc),
        })


async def _resume_after_approval(run_id: str, approved: bool, comments: str = "") -> None:
    """Resumes the graph after human approval/rejection."""
    app = get_workflow()
    config = {"configurable": {"thread_id": run_id}}

    approval_status = "approved" if approved else "rejected"
    _runs[run_id]["approval_status"] = approval_status
    _runs[run_id]["status"] = RunStatus.running

    # Update the graph state with approval
    update_state: SupplyChainState = {
        "approval_status": approval_status,
        "approval_comments": comments,
    }

    try:
        app.update_state(config, update_state)

        # Resume execution from the interrupt point
        async for event in app.astream(None, config=config, stream_mode="values"):
            _runs[run_id].update({
                "status": event.get("status", RunStatus.running),
                "current_node": event.get("current_node"),
                "agent_logs": event.get("agent_logs", _runs[run_id].get("agent_logs", [])),
                "error": event.get("error"),
            })
            current_status = _runs[run_id]["status"]
            if current_status in (RunStatus.completed, RunStatus.failed, RunStatus.human_fallback):
                break

    except Exception as exc:
        logger.error(f"Resume failed for run {run_id}: {exc}")
        _runs[run_id].update({
            "status": RunStatus.failed,
            "error": str(exc),
        })


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post(
    "/run-agent",
    response_model=RunAgentResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start a new supply chain orchestration run",
)
async def run_agent(
    request: RunAgentRequest,
    background_tasks: BackgroundTasks,
) -> RunAgentResponse:
    """
    Triggers a new multi-agent supply chain orchestration run.
    Returns immediately with a run_id for status polling.
    """
    run_id = str(uuid.uuid4())

    initial_state: SupplyChainState = {
        "run_id": run_id,
        "part_id": request.part_id,
        "disruption_type": request.disruption_type,
        "quantity_needed": request.quantity_needed,
        "priority": request.priority,
        "notes": request.notes,
        "inventory": None,
        "suppliers": [],
        "risk_report": None,
        "decision": None,
        "validation_result": None,
        "tried_suppliers": [],
        "retry_count": 0,
        "iteration_count": 0,
        "current_node": "start",
        "status": RunStatus.queued,
        "approval_status": ApprovalStatus.pending,
        "approval_comments": None,
        "agent_logs": [],
        "error": None,
    }

    _runs[run_id] = dict(initial_state)

    background_tasks.add_task(_execute_run, run_id, initial_state)

    return RunAgentResponse(
        run_id=run_id,
        status=RunStatus.queued,
        message="Agent run started. Poll /status/{run_id} for updates.",
    )


@router.get(
    "/status/{run_id}",
    response_model=StatusResponse,
    summary="Get current status and logs for a run",
)
async def get_status(run_id: str) -> StatusResponse:
    """
    Returns the current state of a supply chain orchestration run,
    including all agent logs with Thought/Action/Observation steps.
    """
    if run_id not in _runs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found",
        )

    run = _runs[run_id]

    return StatusResponse(
        run_id=run_id,
        status=run.get("status", RunStatus.queued),
        current_node=run.get("current_node"),
        agent_logs=run.get("agent_logs", []),
        inventory=run.get("inventory"),
        risk_report=run.get("risk_report"),
        suppliers=run.get("suppliers", []),
        decision=run.get("decision"),
        approval_status=run.get("approval_status", ApprovalStatus.pending),
        validation_result=run.get("validation_result"),
        iteration_count=run.get("iteration_count", 0),
        error=run.get("error"),
    )


@router.post(
    "/approve",
    summary="Approve or reject a pending supply chain action",
)
async def approve_action(
    request: ApprovalRequest,
    background_tasks: BackgroundTasks,
) -> JSONResponse:
    """
    Approves or rejects the pending procurement recommendation.
    Resumes graph execution based on the decision.
    """
    run_id = request.run_id

    if run_id not in _runs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found",
        )

    current_status = _runs[run_id].get("status")
    if current_status != RunStatus.awaiting_approval:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Run '{run_id}' is not awaiting approval (current status: {current_status})",
        )

    background_tasks.add_task(
        _resume_after_approval,
        run_id,
        request.approved,
        request.reviewer_comments or "",
    )

    return JSONResponse(
        content={
            "run_id": run_id,
            "approved": request.approved,
            "message": "Approval processed. Agent resuming execution.",
        }
    )


@router.get("/runs", summary="List all active runs (debug)")
async def list_runs() -> dict:
    return {
        "total": len(_runs),
        "runs": [
            {
                "run_id": rid,
                "status": data.get("status"),
                "part_id": data.get("part_id"),
                "current_node": data.get("current_node"),
            }
            for rid, data in _runs.items()
        ],
    }
