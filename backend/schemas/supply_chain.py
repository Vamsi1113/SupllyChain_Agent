"""
Pydantic schemas for Supply Chain Orchestrator AI System.
All inputs/outputs are strictly typed and validated.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ── Enums ─────────────────────────────────────────────────────────────────────


class DisruptionType(str, Enum):
    supplier_failure = "supplier_failure"
    logistics_delay = "logistics_delay"
    quality_issue = "quality_issue"
    demand_spike = "demand_spike"
    geopolitical = "geopolitical"
    natural_disaster = "natural_disaster"


class RiskSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class ApprovalStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    not_required = "not_required"


class RunStatus(str, Enum):
    queued = "queued"
    running = "running"
    awaiting_approval = "awaiting_approval"
    completed = "completed"
    failed = "failed"
    human_fallback = "human_fallback"


class AgentStep(str, Enum):
    inventory = "inventory"
    risk = "risk"
    supplier = "supplier"
    decision = "decision"
    validation = "validation"
    approval = "approval"
    execution = "execution"


# ── Core domain models ────────────────────────────────────────────────────────


class InventoryItem(BaseModel):
    part_id: str
    part_name: str = ""
    current_stock: int = Field(default=0, ge=0)
    reorder_threshold: int = Field(default=0, ge=0)
    unit_cost: float = Field(default=1.0, gt=0)
    current_supplier_id: str = ""
    location: str = ""
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("part_id", "current_supplier_id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        if not re.match(r"^[A-Z0-9\-]{3,30}$", v):
            raise ValueError(f"ID '{v}' must be uppercase alphanumeric with dashes, 3-30 chars")
        return v

    @property
    def is_critical(self) -> bool:
        return self.current_stock <= self.reorder_threshold


class Supplier(BaseModel):
    supplier_id: str
    supplier_name: str
    unit_price: float = Field(gt=0, description="Price must be positive")
    lead_time_days: int = Field(ge=1, description="ETA in days, min 1")
    reliability_score: float = Field(ge=0.0, le=1.0)
    location: str
    capacity: int = Field(ge=0)
    certifications: list[str] = Field(default_factory=list)
    contact_email: str = ""

    @field_validator("supplier_id")
    @classmethod
    def validate_supplier_id(cls, v: str) -> str:
        if not re.match(r"^SUP-[A-Z0-9]{3,20}$", v):
            raise ValueError(
                f"Supplier ID '{v}' must match pattern SUP-XXX (uppercase alphanumeric)"
            )
        return v

    @field_validator("unit_price")
    @classmethod
    def validate_price(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("unit_price must be > 0")
        return round(v, 4)


class RiskReport(BaseModel):
    query: str = ""
    severity: RiskSeverity = RiskSeverity.medium
    severity_score: float = Field(default=5.0, ge=0.0, le=10.0)
    sources: list[str] = Field(default_factory=list)
    summary: str = ""
    affected_regions: list[str] = Field(default_factory=list)
    estimated_duration_days: Optional[int] = None
    fetched_at: datetime = Field(default_factory=datetime.utcnow)

    @model_validator(mode="before")
    @classmethod
    def handle_numeric_severity(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Map 'notes' to 'summary' if summary is missing
            if "notes" in data and not data.get("summary"):
                data["summary"] = data["notes"]
            
            # Map numeric 'severity' (1-10) to 'severity_score' AND enum 'severity'
            sev = data.get("severity")
            if isinstance(sev, (int, float)):
                data["severity_score"] = float(sev)
                if sev >= 8: data["severity"] = "critical"
                elif sev >= 6: data["severity"] = "high"
                elif sev >= 4: data["severity"] = "medium"
                else: data["severity"] = "low"
            
            # Ensure query exists
            if not data.get("query") and data.get("disruption_type"):
                data["query"] = str(data["disruption_type"])
                
        return data


class Decision(BaseModel):
    recommended_supplier: Supplier
    reason: str = ""
    cost_score: float = Field(default=0.0, ge=0.0, le=10.0)
    eta_score: float = Field(default=0.0, ge=0.0, le=10.0)
    risk_score: float = Field(default=0.0, ge=0.0, le=10.0)
    composite_score: float = Field(default=0.0, ge=0.0, le=10.0)
    estimated_total_cost: float = Field(default=1.0, gt=0)
    quantity_to_order: int = Field(default=1, ge=1)
    alternatives_considered: list[str] = Field(default_factory=list)


# ── Agent log models ──────────────────────────────────────────────────────────


class ReActStep(BaseModel):
    thought: str
    action: str
    observation: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentLog(BaseModel):
    agent_name: str
    steps: list[ReActStep] = Field(default_factory=list)
    output: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None


# ── Validation ────────────────────────────────────────────────────────────────


class ValidationResult(BaseModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)
    retried_agent: Optional[str] = None
    retry_count: int = 0


# ── API request/response models ───────────────────────────────────────────────


class RunAgentRequest(BaseModel):
    part_id: str = Field(..., description="Part ID to process (e.g. PART-001)")
    disruption_type: DisruptionType
    quantity_needed: int = Field(ge=1, default=100)
    priority: str = Field(default="normal", pattern="^(low|normal|high|critical)$")
    notes: Optional[str] = Field(default=None, max_length=500)

    @field_validator("part_id")
    @classmethod
    def sanitize_part_id(cls, v: str) -> str:
        v = re.sub(r"[^\w\-]", "", v).upper()
        if not v:
            raise ValueError("part_id cannot be empty after sanitization")
        return v


class RunAgentResponse(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: RunStatus = RunStatus.queued
    message: str = "Agent run queued successfully"


class StatusResponse(BaseModel):
    run_id: str
    status: RunStatus
    current_node: Optional[str] = None
    agent_logs: list[AgentLog] = Field(default_factory=list)
    inventory: Optional[InventoryItem] = None
    risk_report: Optional[RiskReport] = None
    suppliers: list[Supplier] = Field(default_factory=list)
    decision: Optional[Decision] = None
    approval_status: ApprovalStatus = ApprovalStatus.pending
    validation_result: Optional[ValidationResult] = None
    iteration_count: int = 0
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ApprovalRequest(BaseModel):
    run_id: str
    approved: bool
    reviewer_comments: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("run_id")
    @classmethod
    def validate_run_id(cls, v: str) -> str:
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError("run_id must be a valid UUID")
        return v


class NotificationPayload(BaseModel):
    run_id: str
    message: str
    action_url: str
    decision_summary: Optional[str] = None
    severity: str = "info"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
