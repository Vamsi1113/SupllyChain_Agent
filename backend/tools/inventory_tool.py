"""
Inventory Tool — LangChain tool wrapper.
Returns structured inventory status for a given part_id.
Data is simulated but structured as it would come from a real ERP system.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from langchain_core.tools import tool

from schemas.supply_chain import InventoryItem
from utils.cache import cache
from utils.security import sanitize_input


# Simulated ERP inventory database
_INVENTORY_DB: dict[str, dict[str, Any]] = {
    "PART-001": {
        "part_name": "Microcontroller Unit MCU-32",
        "current_stock": 45,
        "reorder_threshold": 100,
        "unit_cost": 12.50,
        "current_supplier_id": "SUP-ASIA01",
        "location": "Warehouse-A, Austin TX",
    },
    "PART-002": {
        "part_name": "Power Regulator IC PR-5V",
        "current_stock": 200,
        "reorder_threshold": 150,
        "unit_cost": 3.25,
        "current_supplier_id": "SUP-EUR01",
        "location": "Warehouse-B, Detroit MI",
    },
    "PART-003": {
        "part_name": "NAND Flash Memory 256MB",
        "current_stock": 12,
        "reorder_threshold": 80,
        "unit_cost": 8.75,
        "current_supplier_id": "SUP-ASIA02",
        "location": "Warehouse-A, Austin TX",
    },
    "PART-004": {
        "part_name": "Industrial Ethernet Controller",
        "current_stock": 300,
        "reorder_threshold": 200,
        "unit_cost": 22.00,
        "current_supplier_id": "SUP-US01",
        "location": "Warehouse-C, Phoenix AZ",
    },
    "PART-005": {
        "part_name": "High-Torque Servo Motor 12Nm",
        "current_stock": 5,
        "reorder_threshold": 50,
        "unit_cost": 145.00,
        "current_supplier_id": "SUP-EUR02",
        "location": "Warehouse-D, Nashville TN",
    },
}


@tool
def get_inventory_status(part_id: str) -> str:
    """
    Retrieves current inventory status for a given part ID.
    Returns a JSON object with stock levels, reorder threshold, unit cost, and supplier info.
    Use this tool first to understand the inventory situation before searching for suppliers.

    Args:
        part_id: The part identifier (e.g. 'PART-001'). Must be uppercase alphanumeric with dashes.

    Returns:
        JSON string with InventoryItem fields, or error message if part not found.
    """
    try:
        part_id = sanitize_input(part_id).upper().strip()

        # Check cache
        cache_key = f"inventory:{part_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        if part_id not in _INVENTORY_DB:
            return json.dumps({
                "error": f"Part '{part_id}' not found in inventory system",
                "available_parts": list(_INVENTORY_DB.keys()),
            })

        raw = _INVENTORY_DB[part_id]
        item = InventoryItem(
            part_id=part_id,
            part_name=raw["part_name"],
            current_stock=raw["current_stock"],
            reorder_threshold=raw["reorder_threshold"],
            unit_cost=raw["unit_cost"],
            current_supplier_id=raw["current_supplier_id"],
            location=raw["location"],
            last_updated=datetime.utcnow(),
        )

        result = json.dumps({
            **item.model_dump(mode="json"),
            "is_critical": item.is_critical,
            "stock_deficit": max(0, item.reorder_threshold - item.current_stock),
        })

        cache.set(cache_key, result)
        return result

    except Exception as exc:
        return json.dumps({"error": f"Inventory lookup failed: {str(exc)}"})
