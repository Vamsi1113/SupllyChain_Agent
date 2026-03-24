"""
Supplier Search Tool — LangChain tool wrapper.
Finds alternative suppliers for a given part, excluding already-tried ones.
Suppliers are ranked by reliability, lead time, and price.
"""

from __future__ import annotations

import json
from typing import Optional

from langchain_core.tools import tool

from schemas.supply_chain import Supplier
from utils.cache import cache
from utils.security import sanitize_input


# Simulated supplier catalog — keyed by part_id
_SUPPLIER_CATALOG: dict[str, list[dict]] = {
    "PART-001": [
        {
            "supplier_id": "SUP-ALT01",
            "supplier_name": "TechFlow Components Ltd",
            "unit_price": 13.80,
            "lead_time_days": 7,
            "reliability_score": 0.94,
            "location": "Taiwan",
            "capacity": 50000,
            "certifications": ["ISO-9001", "RoHS"],
            "contact_email": "orders@techflow.tw",
        },
        {
            "supplier_id": "SUP-ALT02",
            "supplier_name": "NexGen Chips GmbH",
            "unit_price": 14.50,
            "lead_time_days": 5,
            "reliability_score": 0.97,
            "location": "Germany",
            "capacity": 30000,
            "certifications": ["ISO-9001", "CE", "REACH"],
            "contact_email": "supply@nexgen.de",
        },
        {
            "supplier_id": "SUP-ALT03",
            "supplier_name": "Meridian Electronics US",
            "unit_price": 15.20,
            "lead_time_days": 3,
            "reliability_score": 0.91,
            "location": "United States",
            "capacity": 20000,
            "certifications": ["UL", "ISO-9001"],
            "contact_email": "procurement@meridian.us",
        },
        {
            "supplier_id": "SUP-ALT04",
            "supplier_name": "SilkRoute Semiconductors",
            "unit_price": 11.00,
            "lead_time_days": 14,
            "reliability_score": 0.82,
            "location": "India",
            "capacity": 80000,
            "certifications": ["ISO-9001"],
            "contact_email": "b2b@silkroute.in",
        },
    ],
    "PART-002": [
        {
            "supplier_id": "SUP-ALT05",
            "supplier_name": "PowerTech Nordic AB",
            "unit_price": 3.60,
            "lead_time_days": 6,
            "reliability_score": 0.95,
            "location": "Sweden",
            "capacity": 200000,
            "certifications": ["ISO-9001", "CE"],
            "contact_email": "orders@powertech.se",
        },
        {
            "supplier_id": "SUP-ALT06",
            "supplier_name": "Volt Source Korea",
            "unit_price": 3.10,
            "lead_time_days": 10,
            "reliability_score": 0.88,
            "location": "South Korea",
            "capacity": 500000,
            "certifications": ["KC", "ISO-9001"],
            "contact_email": "supply@voltsource.kr",
        },
    ],
    "PART-003": [
        {
            "supplier_id": "SUP-ALT07",
            "supplier_name": "DataFlash Memory Inc",
            "unit_price": 9.20,
            "lead_time_days": 8,
            "reliability_score": 0.93,
            "location": "Japan",
            "capacity": 100000,
            "certifications": ["ISO-14001", "ISO-9001"],
            "contact_email": "b2b@dataflash.jp",
        },
        {
            "supplier_id": "SUP-ALT08",
            "supplier_name": "ByteStore Components",
            "unit_price": 8.50,
            "lead_time_days": 12,
            "reliability_score": 0.85,
            "location": "China",
            "capacity": 1000000,
            "certifications": ["ISO-9001"],
            "contact_email": "sales@bytestore.cn",
        },
    ],
    "PART-004": [
        {
            "supplier_id": "SUP-ALT09",
            "supplier_name": "NetCore Devices LLC",
            "unit_price": 23.50,
            "lead_time_days": 4,
            "reliability_score": 0.96,
            "location": "United States",
            "capacity": 15000,
            "certifications": ["UL", "FCC", "ISO-9001"],
            "contact_email": "enterprise@netcore.us",
        },
    ],
    "PART-005": [
        {
            "supplier_id": "SUP-ALT10",
            "supplier_name": "MotionTech Italia SRL",
            "unit_price": 152.00,
            "lead_time_days": 9,
            "reliability_score": 0.92,
            "location": "Italy",
            "capacity": 5000,
            "certifications": ["CE", "ISO-9001"],
            "contact_email": "orders@motiontechitalia.it",
        },
        {
            "supplier_id": "SUP-ALT11",
            "supplier_name": "RoboServo Japan",
            "unit_price": 148.00,
            "lead_time_days": 11,
            "reliability_score": 0.98,
            "location": "Japan",
            "capacity": 8000,
            "certifications": ["ISO-9001", "CE"],
            "contact_email": "supply@roboservo.jp",
        },
    ],
}


@tool
def search_suppliers(part_id: str, exclude_suppliers: str = "") -> str:
    """
    Searches for alternative suppliers for a given part ID.
    Excludes any suppliers that have already been tried (pass as comma-separated IDs).
    Results are sorted by composite score (reliability × lead_time × price).

    Args:
        part_id: The part identifier (e.g. 'PART-001').
        exclude_suppliers: Comma-separated list of supplier IDs to exclude (e.g. 'SUP-ASIA01,SUP-ALT01').

    Returns:
        JSON string with a ranked list of Supplier objects, or error if no alternatives found.
    """
    try:
        part_id = sanitize_input(part_id).upper().strip()
        excluded: set[str] = set()
        if exclude_suppliers:
            excluded = {s.strip().upper() for s in sanitize_input(exclude_suppliers).split(",") if s.strip()}

        cache_key = f"suppliers:{part_id}:{','.join(sorted(excluded))}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        catalog = _SUPPLIER_CATALOG.get(part_id, [])
        if not catalog:
            return json.dumps({
                "error": f"No suppliers found for part '{part_id}'",
                "part_id": part_id,
                "suppliers": [],
            })

        available = [s for s in catalog if s["supplier_id"] not in excluded]
        if not available:
            return json.dumps({
                "error": f"All known suppliers for '{part_id}' have been exhausted",
                "tried_suppliers": list(excluded),
                "suppliers": [],
            })

        # Validate each supplier through Pydantic
        validated_suppliers: list[dict] = []
        for raw in available:
            try:
                sup = Supplier(**raw)
                validated_suppliers.append(sup.model_dump(mode="json"))
            except Exception:
                continue  # Skip invalid supplier records

        # Rank by composite score: reliability (weight 0.4), lead_time inverse (0.3), price inverse (0.3)
        def composite_score(s: dict) -> float:
            max_price = max(x["unit_price"] for x in validated_suppliers) or 1
            max_lead = max(x["lead_time_days"] for x in validated_suppliers) or 1
            price_norm = 1 - (s["unit_price"] / max_price)
            lead_norm = 1 - (s["lead_time_days"] / max_lead)
            return 0.4 * s["reliability_score"] + 0.3 * lead_norm + 0.3 * price_norm

        ranked = sorted(validated_suppliers, key=composite_score, reverse=True)

        result = json.dumps({
            "part_id": part_id,
            "total_found": len(ranked),
            "excluded_count": len(excluded),
            "suppliers": ranked,
        })

        cache.set(cache_key, result)
        return result

    except Exception as exc:
        return json.dumps({"error": f"Supplier search failed: {str(exc)}"})
