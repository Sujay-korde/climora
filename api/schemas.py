"""CLIMORA API Schemas & Serialization Contracts.

Defines hardened Pydantic v2 schemas for all requests, responses, truth-layer labels,
and structured error bodies with strict validation against NaN, Infinity, and malformed inputs.
"""

from __future__ import annotations

from enum import Enum
import math
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class TruthLayerEnum(str, Enum):
    """Authoritative CLIMORA Truth-Layer Taxonomy."""
    OBSERVED = "OBSERVED"
    DERIVED = "DERIVED"
    MODELED = "MODELED"
    VERIFIED = "VERIFIED"


class ProjectLifecycleStateEnum(str, Enum):
    """Project lifecycle state machine states."""
    DISCOVERED = "DISCOVERED"
    ASSESSED = "ASSESSED"
    OPTIMIZED = "OPTIMIZED"
    PROPOSED = "PROPOSED"
    FUNDED = "FUNDED"
    IMPLEMENTING = "IMPLEMENTING"
    IMPLEMENTED = "IMPLEMENTED"
    MONITORING = "MONITORING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    PAUSED = "PAUSED"


class VerificationStateEnum(str, Enum):
    """Verification milestone states."""
    NOT_STARTED = "NOT_STARTED"
    DATA_PENDING = "DATA_PENDING"
    QC_PENDING = "QC_PENDING"
    MEASUREMENT_READY = "MEASUREMENT_READY"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


# ==============================================================================
# Validation Helpers
# ==============================================================================

H3_HEX_PATTERN = re.compile(r"^[0-9a-fA-F]{15}$")
PROJECT_ID_PATTERN = re.compile(r"^PROJ-[A-Z0-9_\-]+$")


def validate_finite_number(val: float, field_name: str) -> float:
    """Rejects NaN and Infinity values."""
    if math.isnan(val) or math.isinf(val):
        raise ValueError(f"Field '{field_name}' must be a finite real number, cannot be NaN or Infinity.")
    return val


def validate_h3_cell_string(cell_str: str) -> str:
    """Validates 15-character H3 hexadecimal analytical cell format."""
    s = cell_str.strip().lower()
    if not H3_HEX_PATTERN.match(s):
        raise ValueError(f"Invalid H3 cell index '{cell_str}'. Must be a 15-character hexadecimal index.")
    return s


# ==============================================================================
# Query & Request Schemas
# ==============================================================================

class PaginationParams(BaseModel):
    """Validated pagination and zonal query parameters."""
    model_config = ConfigDict(extra="forbid")

    page: int = Field(1, ge=1, description="Page number, 1-indexed")
    page_size: int = Field(28, ge=1, le=100, description="Items per page (1 to 100)")
    h3_cell_id: Optional[str] = Field(None, description="Optional target H3 cell index")

    @field_validator("h3_cell_id")
    @classmethod
    def check_h3(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_h3_cell_string(v)
        return v


class ImplementationEventCreateRequest(BaseModel):
    """Request payload for logging a physical field deployment event."""
    model_config = ConfigDict(extra="forbid")

    intervention_code: str = Field(..., description="Intervention code (e.g. street_tree_shade)")
    h3_cell_id: str = Field(..., description="Canonical H3 resolution 9 cell index")
    implemented_quantity: float = Field(..., ge=0.0, description="Non-negative physical quantity deployed")
    quantity_unit: str = Field("tree_count", description="Physical unit of measure")
    completion_date: str = Field(..., description="ISO 8601 completion date YYYY-MM-DD")
    contractor_id: str = Field("PMC-CONTRACTOR", description="Contractor identity")
    evidence_uri: str = Field(..., description="Auditable URI to signed field delivery report")
    is_synthetic_demo: bool = Field(False, description="Flag indicating mock fixture data")
    notes: Optional[str] = Field(None, description="Optional engineering notes")

    @field_validator("implemented_quantity")
    @classmethod
    def check_quantity(cls, v: float) -> float:
        return validate_finite_number(v, "implemented_quantity")

    @field_validator("h3_cell_id")
    @classmethod
    def check_cell(cls, v: str) -> str:
        return validate_h3_cell_string(v)


class ObservationData(BaseModel):
    """Post-intervention empirical satellite observation payload."""
    model_config = ConfigDict(extra="forbid")

    observation_id: Optional[str] = None
    sensor_platform: str = Field(..., description="Sensor platform (e.g. Landsat-9-TIRS)")
    acquisition_date: str = Field(..., description="ISO 8601 acquisition date YYYY-MM-DD")
    doy: int = Field(..., ge=1, le=366, description="Day of Year integer (canonical temporal unit)")
    spatial_resolution_m: float = Field(30.0, description="Spatial resolution in meters")
    cloud_cover_aoi_pct: float = Field(..., ge=0.0, le=100.0, description="AOI cloud cover percentage")
    quality_flags_passed: bool = Field(..., description="QA pixel screening passed status")
    asset_uri: str = Field(..., description="URI to sensor data asset")
    observed_cell_count: Optional[int] = Field(None, ge=1, description="Count of observed treated cells")
    is_synthetic_demo: bool = Field(False, description="Flag indicating mock fixture data")

    @field_validator("cloud_cover_aoi_pct", "spatial_resolution_m")
    @classmethod
    def check_finite(cls, v: float, info) -> float:
        return validate_finite_number(v, info.field_name)


class VerificationAuditData(BaseModel):
    """Certified third-party verification audit payload."""
    model_config = ConfigDict(extra="forbid")

    verification_id: Optional[str] = None
    verification_status: str = Field("PASSED", description="Audit determination (must be PASSED)")
    verification_date: str = Field(..., description="ISO 8601 audit date YYYY-MM-DD")
    verifier_identity: str = Field(..., description="Accredited third-party verifier identity")
    methodology_standard: str = Field(..., description="Standard evaluated (e.g. ISO 14064-2 / F-26)")
    evidence_artifact_uri: str = Field(..., description="URI to signed audit report")
    findings_summary: Optional[str] = Field("Passed third-party MRV audit.", description="Auditor findings summary")
    is_synthetic_demo: bool = Field(False, description="Flag indicating mock fixture data")


class VerificationEventCreateRequest(BaseModel):
    """Request payload for certifying verification."""
    model_config = ConfigDict(extra="forbid")

    observation: ObservationData
    verification: VerificationAuditData
    target_metric: str = Field("lst", description="Target metric evaluated (lst or ndvi)")
    is_synthetic_demo: bool = Field(False, description="Flag indicating mock fixture data")


class StateTransitionRequest(BaseModel):
    """Request payload for transitioning project lifecycle state."""
    model_config = ConfigDict(extra="forbid")

    target_state: str = Field(..., description="Target lifecycle state")
    sanction_id: Optional[str] = Field(None, description="Required for PROPOSED -> FUNDED")
    approved_budget_inr: Optional[float] = Field(None, description="Required for PROPOSED -> FUNDED")
    notes: Optional[str] = Field(None, description="Optional transition notes")

    @field_validator("approved_budget_inr")
    @classmethod
    def check_budget(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if v < 0:
                raise ValueError("Approved budget must be non-negative.")
            return validate_finite_number(v, "approved_budget_inr")
        return v


class AllocationRevisionRequest(BaseModel):
    """Request payload for proposing an auditable allocation revision."""
    model_config = ConfigDict(extra="forbid")

    h3_cell_id: str = Field(...)
    intervention_code: str = Field(...)
    proposed_quantity: float = Field(..., ge=0.0)
    reason: str = Field(...)
    author: str = Field(...)

    @field_validator("proposed_quantity")
    @classmethod
    def check_qty(cls, v: float) -> float:
        return validate_finite_number(v, "proposed_quantity")

    @field_validator("h3_cell_id")
    @classmethod
    def check_cell(cls, v: str) -> str:
        return validate_h3_cell_string(v)


class ScenarioOptimizationRequest(BaseModel):
    """Request payload for scenario optimization."""
    model_config = ConfigDict(extra="forbid")

    budget_inr: float = Field(..., description="Target scenario budget envelope in INR")

    @field_validator("budget_inr")
    @classmethod
    def check_budget(cls, v: float) -> float:
        v = validate_finite_number(v, "budget_inr")
        if v < 500_000.0 or v > 25_000_000.0:
            raise ValueError("Scenario budget must be between INR 500,000 and INR 25,000,000.")
        return v


# ==============================================================================
# Error Schemas
# ==============================================================================


class ErrorDetail(BaseModel):
    """Standardized API error detail."""
    code: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None


class ErrorResponse(BaseModel):
    """Top-level standardized error envelope."""
    error: ErrorDetail
