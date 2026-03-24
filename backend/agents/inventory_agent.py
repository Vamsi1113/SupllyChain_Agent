"""
Inventory Agent — LangGraph ReAct implementation.
Checks current inventory status and determines if restocking is needed.
"""

from __future__ import annotations

import json
import time
import logging
from typing import Any

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.prebuilt import create_react_agent

from config import get_settings
from utils.llm import get_llm
from schemas.supply_chain import AgentLog, InventoryItem, ReActStep
from tools.inventory_tool import get_inventory_status

logger = logging.getLogger(__name__)

INVENTORY_SYSTEM_PROMPT = """
You are the Inventory Agent for a Supply Chain Orchestrator AI System.
Your job is to check the current inventory status for a given part and determine whether restocking is required.

STRICT RULES:
- Only use the tools provided. Never hallucinate data.
- Return ONLY structured JSON in your final response.
- Your final response MUST be a JSON object with keys: part_id, is_critical, current_stock, reorder_threshold, stock_deficit, unit_cost, current_supplier_id, recommendation.
"""

def run_inventory_agent(part_id: str, state: dict[str, Any]) -> tuple[AgentLog, dict[str, Any]]:
    """
    Runs the inventory agent for the given part_id.
    Returns an AgentLog with steps and the extracted InventoryItem data.
    """
    settings = get_settings()
    start_time = time.time()
    log = AgentLog(agent_name="InventoryAgent")

    try:
        llm = get_llm()
        tools = [get_inventory_status]
        
        # Create the LangGraph compiled ReAct agent
        agent = create_react_agent(llm, tools)

        # Build initial messages
        messages = [
            SystemMessage(content=INVENTORY_SYSTEM_PROMPT),
            HumanMessage(content=f"Check inventory status for part '{part_id}'. Determine if restocking is urgently required.")
        ]

        # Invoke the agent graph
        result = agent.invoke({"messages": messages})
        
        # Parse intermediate steps into ReActStep log entries
        for msg in result.get("messages", []):
            if isinstance(msg, AIMessage) and msg.tool_calls:
                for call in msg.tool_calls:
                    log.steps.append(ReActStep(
                        thought=msg.content or "Invoking tool",
                        action=f"{call['name']}({json.dumps(call['args'])})",
                        observation="Waiting for observation..."
                    ))
            elif isinstance(msg, ToolMessage):
                # Update the last step with the observation
                if log.steps:
                    log.steps[-1].observation = str(msg.content)[:10000]

        # The final message is the answer
        final_msg = result["messages"][-1]
        raw_output = final_msg.content if hasattr(final_msg, "content") else "{}"

        try:
            # Extract JSON from the output
            import re
            json_match = re.search(r"\{.*\}", raw_output, re.DOTALL)
            parsed = json.loads(json_match.group(0)) if json_match else {}
        except Exception:
            parsed = {}

        log.output = parsed
        log.duration_ms = (time.time() - start_time) * 1000

        # Extract InventoryItem from tool result if present
        inventory_data: dict[str, Any] = {}
        for step in log.steps:
            if "inventory" in step.action.lower():
                try:
                    obs_data = json.loads(step.observation)
                    if "part_id" in obs_data and "error" not in obs_data:
                        inventory_data = obs_data
                except Exception:
                    pass

        return log, inventory_data

    except Exception as exc:
        logger.error(f"InventoryAgent failed: {exc}")
        log.error = str(exc)
        log.steps.append(ReActStep(
            thought="Encountered an error during inventory check",
            action="get_inventory_status",
            observation=str(exc),
        ))
        log.duration_ms = (time.time() - start_time) * 1000
        return log, {}
