"""
Risk Tool — LangChain tool wrapper.
Fetches live supply chain disruption data via Tavily Search API.
Falls back to a structured empty response on API failure.
"""

from __future__ import annotations

import json
import os
from datetime import datetime

from langchain_core.tools import tool

from schemas.supply_chain import RiskReport, RiskSeverity
from utils.cache import cache
from utils.security import sanitize_input, validate_external_data


def _score_to_severity(score: float) -> RiskSeverity:
    if score >= 8.0:
        return RiskSeverity.critical
    elif score >= 6.0:
        return RiskSeverity.high
    elif score >= 3.5:
        return RiskSeverity.medium
    else:
        return RiskSeverity.low


def _estimate_severity_score(content: str) -> float:
    """Heuristic severity scoring based on keywords in Tavily results."""
    content_lower = content.lower()
    score = 2.0
    critical_terms = ["factory shut", "complete halt", "force majeure", "banned", "sanctioned"]
    high_terms = ["major disruption", "shortage", "significant delay", "flood", "earthquake", "strike"]
    medium_terms = ["delay", "disruption", "supply constraint", "increased lead time", "tariff"]
    low_terms = ["minor", "slight", "temporary", "manageable", "partial"]

    for t in critical_terms:
        if t in content_lower:
            score += 3.0
    for t in high_terms:
        if t in content_lower:
            score += 1.5
    for t in medium_terms:
        if t in content_lower:
            score += 0.8
    for t in low_terms:
        if t in content_lower:
            score -= 0.5

    return min(10.0, max(0.0, score))


@tool
def get_external_risk_data(query: str) -> str:
    """
    Fetches real-time supply chain risk and disruption data from external sources using Tavily.
    Use this tool to understand geopolitical, logistical, or market risks for a supply chain query.
    Examples: 'semiconductor shortage Taiwan 2024', 'shipping delays Suez Canal', 'US tariffs electronics'.

    Args:
        query: A natural language search query about supply chain risk (max 200 chars).

    Returns:
        JSON string with RiskReport fields including severity score, summary, sources, and affected regions.
    """
    try:
        query = sanitize_input(query)[:200]

        cache_key = f"risk:{query[:80]}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        tavily_api_key = os.getenv("TAVILY_API_KEY", "")

        if tavily_api_key:
            try:
                from tavily import TavilyClient
                client = TavilyClient(api_key=tavily_api_key)
                response = client.search(
                    query=query,
                    search_depth="advanced",
                    max_results=5,
                    include_answer=True,
                )

                validate_external_data(response)

                combined_content = " ".join(
                    r.get("content", "") for r in response.get("results", [])
                )
                severity_score = _estimate_severity_score(combined_content)

                report = RiskReport(
                    query=query,
                    severity=_score_to_severity(severity_score),
                    severity_score=round(severity_score, 2),
                    sources=[r.get("url", "") for r in response.get("results", []) if r.get("url")],
                    summary=response.get("answer", combined_content[:500] or "No summary available"),
                    affected_regions=_extract_regions(combined_content),
                    estimated_duration_days=_estimate_duration(combined_content),
                )
            except Exception as api_exc:
                # Graceful fallback: return structured low-confidence report
                report = RiskReport(
                    query=query,
                    severity=RiskSeverity.medium,
                    severity_score=5.0,
                    sources=[],
                    summary=f"External risk data unavailable (API issue: {str(api_exc)[:100]}). Manual assessment recommended.",
                    affected_regions=[],
                    estimated_duration_days=None,
                )
        else:
            # No API key — return a structured placeholder
            report = RiskReport(
                query=query,
                severity=RiskSeverity.medium,
                severity_score=5.0,
                sources=[],
                summary="TAVILY_API_KEY not configured. Risk data based on internal heuristics only.",
                affected_regions=[],
                estimated_duration_days=7,
            )

        result = json.dumps(report.model_dump(mode="json"))
        cache.set(cache_key, result)
        return result

    except Exception as exc:
        return json.dumps({"error": f"Risk data fetch failed: {str(exc)}"})


def _extract_regions(content: str) -> list[str]:
    known_regions = [
        "Taiwan", "China", "Japan", "South Korea", "India",
        "Germany", "United States", "Suez Canal", "Ukraine",
        "Russia", "Southeast Asia", "Europe", "North America",
        "Middle East", "Latin America",
    ]
    return [r for r in known_regions if r.lower() in content.lower()]


def _estimate_duration(content: str) -> int | None:
    import re
    matches = re.findall(r"(\d+)\s*(day|week|month)", content.lower())
    if not matches:
        return None
    total_days = 0
    for num, unit in matches[:3]:
        n = int(num)
        if unit == "week":
            n *= 7
        elif unit == "month":
            n *= 30
        total_days += n
    return total_days // len(matches[:3]) if matches else None
