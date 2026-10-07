"""Contrats métier partagés par les outils directs et MCP."""

from datetime import date
from enum import StrEnum
from typing import Any, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Role(StrEnum):
    VIEWER = "viewer"
    OPERATOR = "operator"
    SUPERVISOR = "maintenance_supervisor"
    ADMIN = "admin"


class Identity(Model):
    actor: str = Field(min_length=1)
    role: Role = Role.OPERATOR


class Asset(Model):
    asset_id: str
    type: Literal["transformer"] = "transformer"
    substation: str
    commissioned: date
    manufacturer: str
    rating_mva: float = Field(gt=0)
    criticality: Literal["low", "medium", "high"]


class Anomaly(Model):
    event_id: str
    asset_id: str
    anomaly_type: str
    severity_score: float = Field(ge=0, le=1)
    model_confidence: float = Field(ge=0, le=1)
    timestamp: AwareDatetime


class Telemetry(Model):
    asset_id: str
    timestamp: AwareDatetime
    temperature_c: float
    load_pct: float = Field(ge=0, le=200)
    baseline_stddev: float
    oil_degradation_confirmed: bool
    oil_pressure: float | None = None


class Prediction(Model):
    asset_id: str
    failure_probability_30d: float = Field(ge=0, le=1)
    risk_level: Literal["low", "medium", "high"]
    main_factors: list[str]
    model_version: str


class Maintenance(Model):
    work_order_id: str
    asset_id: str
    date: date
    type: str
    finding: str


class Recommendation(Model):
    outcome: Literal["recommendation_ready", "insufficient_evidence", "no_action"]
    summary: str = Field(min_length=1, max_length=4000)
    citations: list[str] = Field(default_factory=list, max_length=30)
    missing_evidence: list[str] = Field(default_factory=list, max_length=20)
    action: Literal["inspection"] | None = None
    priority: Literal["P1"] | None = None
    deadline_hours: Literal[24] | None = None


class ToolResult(Model):
    ok: bool = True
    data: dict[str, Any] = Field(default_factory=dict)
    sources: list[str] = Field(default_factory=list)
    error: str | None = None


class DomainError(Exception):
    """Erreur métier présentable en français, sans détail interne sensible."""
