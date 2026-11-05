"""CLIMORA API Schemas & Serialization Contracts.

Defines hardened Pydantic v2 schemas for all requests, responses, truth-layer labels,
and structured error bodies with strict validation against NaN, Infinity, and malformed inputs.
"""

from __future__ import annotations

from enum import Enum
import math
import os
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


def validate_evidence_uri(uri_str: str, field_name: str) -> str:
    """Validates that evidence artifact URI uses an approved, auditable storage scheme (s3://, mock://).
    
    Security Guard:
    Strictly forbids http://, https://, file://, and arbitrary external schemas to prevent SSRF and unverified remote references.
    In production and staging environments, mock:// is strictly rejected to prevent synthetic evidence contamination.
    """
    if not isinstance(uri_str, str):
        raise ValueError(f"Field '{field_name}' must be a string URI.")
    s = uri_str.strip()
    
    env = os.environ.get("ENV", os.environ.get("FLASK_ENV", "development")).lower()
    if env in ["production", "staging"]:
        if not s.startswith("s3://"):
            raise ValueError(
                f"Field '{field_name}' must use an approved production S3 storage reference (s3://). "
                f"Mock schemes ('mock://') and arbitrary external schemes are strictly prohibited in {env} environments."
            )
        return s

    if not s or not (s.startswith("s3://") or s.startswith("mock://")):
        raise ValueError(
            f"Field '{field_name}' must use an approved storage reference scheme (s3:// or mock://). "
            f"External HTTP/HTTPS/FILE schemes are strictly forbidden to prevent SSRF (received '{uri_str}')."
        )
    return s


def validate_sha256_hex(checksum: Optional[str], field_name: str) -> Optional[str]:
    """Validates that a cryptographic checksum is a valid 64-character lowercase hex SHA-256 digest."""
    if checksum is None:
        return None
    s = str(checksum).strip().lower()
    if len(s) != 64 or not all(c in "0123456789abcdef" for c in s):
        raise ValueError(
            f"Field '{field_name}' must be a valid 64-character hexadecimal SHA-256 digest (received '{checksum}')."
        )
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
    evidence_sha256: Optional[str] = Field(None, description="SHA-256 cryptographic checksum of evidence artifact")
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

    @field_validator("evidence_uri")
    @classmethod
    def check_evidence(cls, v: str) -> str:
        return validate_evidence_uri(v, "evidence_uri")

    @field_validator("evidence_sha256")
    @classmethod
    def check_sha(cls, v: Optional[str]) -> Optional[str]:
        return validate_sha256_hex(v, "evidence_sha256")


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
    evidence_artifact_sha256: Optional[str] = Field(None, description="SHA-256 checksum of verification report")
    findings_summary: Optional[str] = Field("Passed third-party MRV audit.", description="Auditor findings summary")
    is_synthetic_demo: bool = Field(False, description="Flag indicating mock fixture data")

    @field_validator("evidence_artifact_uri")
    @classmethod
    def check_artifact_uri(cls, v: str) -> str:
        return validate_evidence_uri(v, "evidence_artifact_uri")

    @field_validator("evidence_artifact_sha256")
    @classmethod
    def check_artifact_sha(cls, v: Optional[str]) -> Optional[str]:
        return validate_sha256_hex(v, "evidence_artifact_sha256")


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
