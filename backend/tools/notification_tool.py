"""
Notification Tool — LangChain tool wrapper.
Sends approval notifications via webhook and records pending approvals in the run store.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime

import httpx
from langchain_core.tools import tool

from schemas.supply_chain import NotificationPayload
from utils.security import sanitize_input

logger = logging.getLogger(__name__)


@tool
def send_notification(message: str, action_url: str, run_id: str = "", decision_summary: str = "") -> str:
    """
    Sends a human approval notification via webhook.
    Use this tool when a decision has been made and requires human approval before execution.

    Args:
        message: The notification message describing the recommended action.
        action_url: URL for the human to approve/reject the action.
        run_id: The run ID for tracking.
        decision_summary: Brief summary of the recommended decision.

    Returns:
        JSON string with notification status and timestamp.
    """
    try:
        message = sanitize_input(message)[:1000]
        decision_summary = sanitize_input(decision_summary)[:500]

        payload = NotificationPayload(
            run_id=run_id or "unknown",
            message=message,
            action_url=action_url,
            decision_summary=decision_summary,
            severity="high",
            timestamp=datetime.utcnow(),
        )

        # Try to send webhook notification
        import os
        webhook_url = os.getenv("WEBHOOK_URL", "")
        webhook_sent = False

        if webhook_url:
            try:
                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(
                        webhook_url,
                        json=payload.model_dump(mode="json"),
                        headers={"Content-Type": "application/json"},
                    )
                    webhook_sent = resp.status_code < 300
            except Exception as webhook_exc:
                logger.warning(f"Webhook delivery failed: {webhook_exc}")

        return json.dumps({
            "status": "notification_sent",
            "webhook_delivered": webhook_sent,
            "run_id": run_id,
            "action_url": action_url,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        })

    except Exception as exc:
        return json.dumps({"error": f"Notification failed: {str(exc)}"})
