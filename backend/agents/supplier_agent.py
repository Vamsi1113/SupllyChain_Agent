"""
Supplier Agent — LangGraph ReAct implementation.
Searches for alternative suppliers, avoiding already-tried ones to prevent loops.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.prebuilt import create_react_agent

from config import get_settings
from utils.llm import get_llm
from schemas.supply_chain import AgentLog, ReActStep, Supplier
from tools.supplier_tool import search_suppliers

logger = logging.getLogger(__name__)

SUPPLIER_SYSTEM_PROMPT = """
You are the Supplier Agent for a Supply Chain Orchestrator AI System.
Your job is to find the best alternative suppliers for a required part.
You MUST exclude any suppliers that have already been tried.

STRICT RULES:
- Only use provided tools. Never invent supplier data.
- Always pass excluded suppliers to the search tool.
- Return ONLY structured JSON in your final answer.
- The JSON must match this structure: keys: part_id, suppliers_found (integer).
"""

def run_supplier_agent(
    part_id: str,
    tried_suppliers: list[str],
    quantity_needed: int,
    state: dict[str, Any],
) -> tuple[AgentLog, list[dict[str, Any]]]:
    """
    Runs the supplier agent to find alternative suppliers.
    Returns an AgentLog and a list of validated Supplier dicts.
    """
    settings = get_settings()
    start_time = time.time()
    log = AgentLog(agent_name="SupplierAgent")

    try:
        llm = get_llm()
        tools = [search_suppliers]
        
        agent = create_react_agent(llm, tools)

        exclude_str = ",".join(tried_suppliers) if tried_suppliers else ""
        question = (
            f"Find alternative suppliers for part '{part_id}'. "
            f"I need {quantity_needed} units. "
            f"EXCLUDE these already-tried suppliers: '{exclude_str}'. "
            f"Return all available alternatives ranked by score."
        )

        messages = [
            SystemMessage(content=SUPPLIER_SYSTEM_PROMPT),
            HumanMessage(content=question)
        ]

        result = agent.invoke({"messages": messages})

        for msg in result.get("messages", []):
            if isinstance(msg, AIMessage) and msg.tool_calls:
                for call in msg.tool_calls:
                    log.steps.append(ReActStep(
                        thought=msg.content or "Invoking tool",
                        action=f"{call['name']}({json.dumps(call['args'])})",
                        observation="Waiting for observation..."
                    ))
            elif isinstance(msg, ToolMessage):
                if log.steps:
                    log.steps[-1].observation = str(msg.content)[:10000]

        # Extract supplier list from tool observations
        suppliers: list[dict[str, Any]] = []
        for step in log.steps:
            if "supplier" in step.action.lower():
                try:
                    obs = json.loads(step.observation)
                    if "suppliers" in obs and isinstance(obs["suppliers"], list):
                        # Validate each supplier via Pydantic
                        for raw in obs["suppliers"]:
                            try:
                                sup = Supplier(**raw)
                                suppliers.append(sup.model_dump(mode="json"))
                            except Exception:
                                pass
                        break
                except Exception:
                    pass

        log.output = {"part_id": part_id, "suppliers_found": len(suppliers)}
        log.duration_ms = (time.time() - start_time) * 1000
        return log, suppliers

    except Exception as exc:
        logger.error(f"SupplierAgent failed: {exc}")
        log.error = str(exc)
        log.steps.append(ReActStep(
            thought="Error encountered while searching suppliers",
            action="search_suppliers",
            observation=str(exc),
        ))
        log.duration_ms = (time.time() - start_time) * 1000
        return log, []
