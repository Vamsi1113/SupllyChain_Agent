"""
Risk Agent — LangGraph ReAct implementation.
Accesses external APIs via Tavily to determine global disruption impacts.
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
from schemas.supply_chain import AgentLog, ReActStep, RiskReport
from tools.risk_tool import get_external_risk_data

logger = logging.getLogger(__name__)

RISK_SYSTEM_PROMPT = """
You are the Supply Chain Risk Agent. 
Your objective is to assess the external real-world impact of a given disruption type on a specific geographic region or supplier.

STRICT RULES:
- Use the provided search tool to find live, current data.
- Synthesize the findings into a structured risk report.
- Return ONLY JSON in your final answer.
- The JSON must match this structure:
    "disruption_type": "string",
    "severity": "low" | "medium" | "high" | "critical",
    "severity_score": number (0-10),
    "summary": "concise overview of risk",
    "affected_regions": ["region1", "region2"],
    "notes": "any extra details"
"""

def run_risk_agent(disruption_type: str, context: dict[str, Any]) -> tuple[AgentLog, dict[str, Any]]:
    """
    Runs the risk agent to analyze a specific disruption.
    Returns an AgentLog and the extracted RiskReport data.
    """
    settings = get_settings()
    start_time = time.time()
    log = AgentLog(agent_name="RiskAgent")

    try:
        llm = get_llm()
        tools = [get_external_risk_data]
        
        agent = create_react_agent(llm, tools)

        messages = [
            SystemMessage(content=RISK_SYSTEM_PROMPT),
            HumanMessage(content=f"Assess this disruption: {disruption_type}. Additional context: {json.dumps(context)}")
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

        final_msg = result["messages"][-1]
        raw_output = final_msg.content if hasattr(final_msg, "content") else "{}"

        try:
            import re
            json_match = re.search(r"\{.*\}", raw_output, re.DOTALL)
            parsed = json.loads(json_match.group(0)) if json_match else {}
        except Exception:
            parsed = {}

        log.output = parsed
        log.duration_ms = (time.time() - start_time) * 1000

        risk_data: dict[str, Any] = {}
        for step in log.steps:
            if "risk" in step.action.lower():
                try:
                    obs_data = json.loads(step.observation)
                    if "severity" in obs_data:
                        risk_data = obs_data
                except Exception:
                    pass

        # Give AI the final structured parsed dict if it exists, otherwise use tool data
        if "severity" in parsed:
            risk_data = parsed

        return log, risk_data

    except Exception as exc:
        logger.error(f"RiskAgent failed: {exc}")
        log.error = str(exc)
        log.steps.append(ReActStep(
            thought="Error analyzing risk",
            action="get_external_risk_data",
            observation=str(exc),
        ))
        log.duration_ms = (time.time() - start_time) * 1000
        return log, {}
