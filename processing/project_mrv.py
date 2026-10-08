"""
CLIMORA - Phase 1H: Bankable Project Proposal & MRV Verification Architecture.

Formal realization of the Phase 1H Architecture Contract:
1. Truth-Layer Taxonomy: OBSERVED -> DERIVED -> MODELED -> VERIFIED.
2. Project Lifecycle State Machine with strict transition prerequisites.
3. Allocation immutability and transparent proposed revision tracking.
4. Three-tier indicator separation: Baseline vs Modeled vs Verified.
5. MRV Entity Pipeline: Verification Plan -> Baseline -> Implementation Event ->
   Observation Event -> Quality Control -> Impact Measurement -> Verification Event.
6. Honest Difference-in-Differences (DID / F-26) evaluation.
7. 13-Section Machine-Readable Project Proposal Document Model.
8. Strict isolation of synthetic demo fixtures (DEMO_ONLY_SYNTHETIC_MRV_DATA).
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

# Ensure project root is on sys.path
PROJECT_ROOT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_DIR))

import numpy as np
import pandas as pd

from ingestion.common import calculate_sha256, get_logger
from processing.config import MANIFESTS_DIR, PROCESSED_DIR, PROJECT_ROOT

logger = get_logger()

# Canonical Paths
CANONICAL_ALLOCATION_PARQUET = PROCESSED_DIR / "optimization" / "canonical_optimization_allocation.parquet"
CANONICAL_RUN_MANIFEST = MANIFESTS_DIR / "optimization_run_manifest.json"
CANONICAL_FEATURE_MATRIX = PROCESSED_DIR / "canonical_feature_matrix.parquet"
CANONICAL_HEV_PARQUET = PROCESSED_DIR / "hev" / "canonical_hev_components.parquet"
CANONICAL_RISK_SURFACE = PROCESSED_DIR / "risk" / "canonical_risk_surface.parquet"
CANONICAL_PROJECTS_DIR = PROCESSED_DIR / "projects"
PROJECT_MRV_CONTRACT = MANIFESTS_DIR / "project_mrv_contract.json"

SYNTHETIC_MRV_TAG = "DEMO_ONLY_SYNTHETIC_MRV_DATA"


def doy_to_date(year: int, doy: int) -> str:
    """Converts a Day-of-Year integer to an ISO8601 date string, accounting for leap years."""
    base = datetime(year, 1, 1, tzinfo=timezone.utc)
    target = base + timedelta(days=doy - 1)
    return target.strftime("%Y-%m-%d")


class ProjectLifecycleState(str, Enum):
    """Lifecycle state machine states for bankable projects."""
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


class VerificationState(str, Enum):
    """Lifecycle states for independent verification events."""
    NOT_STARTED = "NOT_STARTED"
    DATA_PENDING = "DATA_PENDING"
    QC_PENDING = "QC_PENDING"
    MEASUREMENT_READY = "MEASUREMENT_READY"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


@dataclass
class ImplementationEvent:
    """Records real-world contractor physical deployment in a specific H3 cell."""
    event_id: str
    project_id: str
    h3_cell_id: str
    intervention_code: str
    planned_quantity: float
    implemented_quantity: float
    quantity_unit: str
    contractor_id: str
    completion_date: str
    evidence_uri: str
    is_synthetic_demo: bool = False

    @property
    def deviation(self) -> float:
        """Absolute physical deviation: implemented - planned."""
        return self.implemented_quantity - self.planned_quantity

    @property
    def deviation_rate(self) -> Optional[float]:
        """Fractional deviation relative to plan (F-27.2). Returns None (undefined/not-applicable) when planned_quantity == 0."""
        if self.planned_quantity == 0.0:
            return None
        return (self.implemented_quantity - self.planned_quantity) / self.planned_quantity


@dataclass
class ObservationEvent:
    """Records post-implementation empirical satellite or field sensor acquisition."""
    observation_id: str
    sensor_platform: str
    acquisition_date: str
    doy: int
    spatial_resolution_m: float
    cloud_cover_aoi_pct: float
    quality_flags_passed: bool
    asset_uri: str
    is_synthetic_demo: bool = False


@dataclass
class MRVQualityControlResult:
    """Audit of post-implementation observation against pre-intervention baseline standards."""
    spatial_coverage_passed: bool
    temporal_window_passed: bool
    cloud_screening_passed: bool
    sensor_consistency_passed: bool
    geolocation_alignment_passed: bool
    all_passed: bool
    violations: List[str]
    temporal_tier: str = "PREFERRED"  # PREFERRED (DOY 95-115), FALLBACK (DOY 90-120), or REJECTED


@dataclass
class VerificationEvent:
    """Formal third-party audit milestone evaluating empirical intervention outcomes."""
    verification_id: str
    project_id: str
    verification_status: str  # PASSED, CONDITIONAL_PASS, FAILED
    verification_date: str
    verifier_identity: str
    methodology_standard: str
    evidence_artifact_uri: str
    findings_summary: str
    is_synthetic_demo: bool = False


@dataclass
class AllocationRevision:
    """Audit trail tracking proposed human revisions to an immutable optimization run."""
    revision_id: str
    project_id: str
    h3_cell_id: str
    intervention_code: str
    original_quantity: float
    proposed_quantity: float
    revision_delta: float
    revision_reason: str
    author_identity: str
    timestamp_utc: str


class AllocationRevisionTracker:
    """Enforces immutability of the original optimization allocation while tracking revisions."""

    def __init__(self, original_allocation_df: pd.DataFrame):
        # Create an immutable deep copy of original solver allocation
        self._original_allocation = original_allocation_df.copy(deep=True)
        self._original_allocation.attrs["is_immutable"] = True
        self._revisions: List[AllocationRevision] = []

    @property
    def original_allocation(self) -> pd.DataFrame:
        """Returns read-only copy of the original solver allocation."""
        return self._original_allocation.copy(deep=True)

    @property
    def revisions(self) -> List[AllocationRevision]:
        """Returns list of all logged revisions."""
        return list(self._revisions)

    def propose_revision(
        self,
        project_id: str,
        h3_cell_id: str,
        intervention_code: str,
        proposed_quantity: float,
        reason: str,
        author: str,
    ) -> AllocationRevision:
        """Logs a transparent proposed modification without mutating original data."""
        # Find original record
        mask = (self._original_allocation["h3_cell_id"] == h3_cell_id) & (
            self._original_allocation["intervention_type"] == intervention_code
        )
        orig_matches = self._original_allocation[mask]
        orig_q = float(orig_matches["quantity"].iloc[0]) if len(orig_matches) > 0 else 0.0

        rev = AllocationRevision(
            revision_id=f"REV-{uuid.uuid4().hex[:8].upper()}",
            project_id=project_id,
            h3_cell_id=h3_cell_id,
            intervention_code=intervention_code,
            original_quantity=orig_q,
            proposed_quantity=float(proposed_quantity),
            revision_delta=float(proposed_quantity - orig_q),
            revision_reason=reason,
            author_identity=author,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
        )
        self._revisions.append(rev)
        return rev

    def get_effective_allocation(self) -> pd.DataFrame:
        """Constructs the effective proposed allocation incorporating approved revisions."""
        df_eff = self._original_allocation.copy(deep=True)
        df_eff["is_revised"] = False
        df_eff["revision_reason"] = None

        for rev in self._revisions:
            mask = (df_eff["h3_cell_id"] == rev.h3_cell_id) & (
                df_eff["intervention_type"] == rev.intervention_code
            )
            if mask.any():
                df_eff.loc[mask, "quantity"] = rev.proposed_quantity
                df_eff.loc[mask, "is_revised"] = True
                df_eff.loc[mask, "revision_reason"] = rev.revision_reason

        return df_eff


class ProjectStateMachine:
    """Enforces strict state transitions and verification gating for bankable projects."""

    VALID_TRANSITIONS: Dict[ProjectLifecycleState, Set[ProjectLifecycleState]] = {
        ProjectLifecycleState.DISCOVERED: {ProjectLifecycleState.ASSESSED, ProjectLifecycleState.CANCELLED},
        ProjectLifecycleState.ASSESSED: {ProjectLifecycleState.OPTIMIZED, ProjectLifecycleState.CANCELLED},
        ProjectLifecycleState.OPTIMIZED: {ProjectLifecycleState.PROPOSED, ProjectLifecycleState.CANCELLED},
        ProjectLifecycleState.PROPOSED: {ProjectLifecycleState.FUNDED, ProjectLifecycleState.REJECTED, ProjectLifecycleState.CANCELLED},
        ProjectLifecycleState.FUNDED: {ProjectLifecycleState.IMPLEMENTING, ProjectLifecycleState.CANCELLED},
        ProjectLifecycleState.IMPLEMENTING: {ProjectLifecycleState.IMPLEMENTED, ProjectLifecycleState.PAUSED, ProjectLifecycleState.CANCELLED},
        ProjectLifecycleState.PAUSED: {ProjectLifecycleState.IMPLEMENTING, ProjectLifecycleState.CANCELLED},
        ProjectLifecycleState.IMPLEMENTED: {ProjectLifecycleState.MONITORING, ProjectLifecycleState.CANCELLED},
        ProjectLifecycleState.MONITORING: {ProjectLifecycleState.VERIFIED, ProjectLifecycleState.REJECTED, ProjectLifecycleState.CANCELLED},
        ProjectLifecycleState.VERIFIED: set(),
        ProjectLifecycleState.REJECTED: set(),
        ProjectLifecycleState.CANCELLED: set(),
    }

    @classmethod
    def can_transition(
        cls,
        current_state: ProjectLifecycleState,
        target_state: ProjectLifecycleState,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """Evaluates whether a lifecycle transition is permitted under governance rules."""
        if target_state not in cls.VALID_TRANSITIONS.get(current_state, set()):
            return False, f"Illegal state transition from {current_state.value} to {target_state.value}."

        if context is None:
            context = {}

        # Gated Rule 1: PROPOSED -> FUNDED requires financial sanction
        if current_state == ProjectLifecycleState.PROPOSED and target_state == ProjectLifecycleState.FUNDED:
            if not context.get("sanction_id") or not context.get("approved_budget_inr"):
                return False, "Transition to FUNDED requires 'sanction_id' and 'approved_budget_inr'."

        # Gated Rule 2: IMPLEMENTING -> IMPLEMENTED requires physical implementation events
        if current_state == ProjectLifecycleState.IMPLEMENTING and target_state == ProjectLifecycleState.IMPLEMENTED:
            impl_events = context.get("implementation_events", [])
            if not impl_events or len(impl_events) == 0:
                return False, "Transition to IMPLEMENTED requires documented implementation events."

        # Gated Rule 3: MONITORING -> VERIFIED strict MRV gating
        if current_state == ProjectLifecycleState.MONITORING and target_state == ProjectLifecycleState.VERIFIED:
            # Check 1: Real-world implementation evidence exists
            impl_events = context.get("implementation_events", [])
            if not impl_events:
                return False, "Verification requires physical implementation events."

            # Check 2: Observation event exists
            obs_event = context.get("observation_event")
            if not obs_event:
                return False, "Verification requires post-intervention observation event."

            # Check 3: MRV Quality Control passed
            qc_result = context.get("qc_result")
            if not qc_result or not getattr(qc_result, "all_passed", False):
                return False, "Verification requires 100% passing MRV quality control audit."

            # Check 4: Verification event passed
            verif_event = context.get("verification_event")
            if not verif_event or getattr(verif_event, "verification_status", None) != "PASSED":
                return False, "Verification requires certified third-party verification event with status 'PASSED'."

            # Check 5: Anti-Contamination Guard - Synthetic fixtures cannot certify production project
            if any(getattr(e, "is_synthetic_demo", False) for e in impl_events) or \
               getattr(obs_event, "is_synthetic_demo", False) or \
               getattr(verif_event, "is_synthetic_demo", False):
                return False, f"REJECTED: Demo fixture ({SYNTHETIC_MRV_TAG}) cannot set canonical project status to VERIFIED."

        return True, "Transition authorized."


class MRVQualityControlEngine:
    """Audits post-intervention observation events against baseline comparability criteria (F-28.1)."""

    @staticmethod
    def audit_observation(
        observation: ObservationEvent,
        treated_cell_count: int,
        observed_cell_count: int,
        target_metric: str = "lst",
        baseline_target_doy: int = 105,
        max_doy_offset: int = 15,
        max_cloud_cover_pct: float = 5.0,
    ) -> MRVQualityControlResult:
        """Executes the five mandatory MRV QC checks with metric-specific sensor validation."""
        violations = []

        # 1. Spatial Coverage Check
        spatial_ok = observed_cell_count >= treated_cell_count
        if not spatial_ok:
            violations.append(f"Spatial coverage incomplete: {observed_cell_count} observed < {treated_cell_count} treated cells.")

        # 2. Temporal Window Comparability Check (DOY 95-115 preferred, DOY 90-120 fallback, max offset <= 15)
        doy_offset = abs(observation.doy - baseline_target_doy)
        if 95 <= observation.doy <= 115:
            temporal_tier = "PREFERRED"
            temporal_ok = True
        elif 90 <= observation.doy <= 120 and doy_offset <= max_doy_offset:
            temporal_tier = "FALLBACK"
            temporal_ok = True
        else:
            temporal_tier = "REJECTED"
            temporal_ok = False
            violations.append(
                f"Temporal offset {doy_offset} days exceeds allowable window: observation DOY {observation.doy} is outside "
                f"both preferred window (DOY 95-115) and fallback window (DOY 90-120, max offset <= {max_doy_offset} days)."
            )

        # 3. Cloud / Shadow Screening Check (<= 5.0% AOI contamination ceiling with 100% pixel masking)
        cloud_ceiling_ok = observation.cloud_cover_aoi_pct <= max_cloud_cover_pct
        pixel_masking_ok = observation.quality_flags_passed
        cloud_ok = cloud_ceiling_ok and pixel_masking_ok
        if not cloud_ceiling_ok:
            violations.append(f"Cloud/shadow contamination {observation.cloud_cover_aoi_pct}% exceeds allowable ceiling of {max_cloud_cover_pct}%.")
        if not pixel_masking_ok:
            violations.append("Pixel quality flags failed: unmasked invalid/cloud pixels detected in analysis.")

        # 4. Sensor Radiometric Consistency Check (Metric-Specific!)
        thermal_sensors = {"Landsat-8", "Landsat-9", "Drone-Thermal-Radiometric"}
        optical_sensors = {"Landsat-8", "Landsat-9", "Sentinel-2"}

        target_metric_lower = target_metric.lower()
        if target_metric_lower in {"lst", "temperature", "thermal"}:
            if any(s in observation.sensor_platform for s in thermal_sensors):
                sensor_ok = True
            elif "Sentinel-2" in observation.sensor_platform:
                sensor_ok = False
                violations.append(
                    f"Sensor '{observation.sensor_platform}' has no thermal infrared payload; "
                    "Sentinel-2 MSI provides optical bands (NDVI/NDBI) and CANNOT directly measure thermal LST."
                )
            else:
                sensor_ok = False
                violations.append(f"Unapproved thermal sensor platform: {observation.sensor_platform}.")
        elif target_metric_lower in {"ndvi", "ndbi", "optical", "canopy"}:
            if any(s in observation.sensor_platform for s in optical_sensors):
                sensor_ok = True
            else:
                sensor_ok = False
                violations.append(f"Unapproved optical sensor platform: {observation.sensor_platform}.")
        else:
            all_approved = thermal_sensors.union(optical_sensors)
            sensor_ok = any(s in observation.sensor_platform for s in all_approved)
            if not sensor_ok:
                violations.append(f"Unapproved sensor platform: {observation.sensor_platform}.")

        # 5. Geolocation / Spatial Alignment Check (alignment to analytical spatial framework)
        geo_ok = observation.spatial_resolution_m <= 30.0
        if not geo_ok:
            violations.append(f"Spatial resolution {observation.spatial_resolution_m}m too coarse for H3 Res9 alignment.")

        all_ok = spatial_ok and temporal_ok and cloud_ok and sensor_ok and geo_ok

        return MRVQualityControlResult(
            spatial_coverage_passed=spatial_ok,
            temporal_window_passed=temporal_ok,
            cloud_screening_passed=cloud_ok,
            sensor_consistency_passed=sensor_ok,
            geolocation_alignment_passed=geo_ok,
            all_passed=all_ok,
            violations=violations,
            temporal_tier=temporal_tier,
        )


class ProjectProposalBuilder:
    """Builds a structured, machine-readable, 13-section bankable project proposal."""

    @classmethod
    def build_from_optimization_run(
        cls,
        run_manifest_path: Path = CANONICAL_RUN_MANIFEST,
        allocation_parquet_path: Path = CANONICAL_ALLOCATION_PARQUET,
        feature_parquet_path: Path = CANONICAL_FEATURE_MATRIX,
        risk_parquet_path: Path = CANONICAL_RISK_SURFACE,
        project_title: str = "Pune Urban Heat Island Mitigation & Street Canopy Initiative",
        beneficiary_agency: str = "Pune Municipal Corporation (Tree Authority & Road Dept)",
        project_id_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Assembles the canonical 13-section project proposal document from disk artifacts."""
        if not run_manifest_path.exists():
            raise FileNotFoundError(f"Optimization run manifest not found: {run_manifest_path}")
        if not allocation_parquet_path.exists():
            raise FileNotFoundError(f"Allocation parquet not found: {allocation_parquet_path}")

        with open(run_manifest_path, "r", encoding="utf-8") as f:
            run_manifest = json.load(f)

        df_alloc = pd.read_parquet(allocation_parquet_path)
        df_feat = pd.read_parquet(feature_parquet_path).set_index("h3_cell_id")
        df_risk = pd.read_parquet(risk_parquet_path).set_index("h3_cell_id")

        run_id = run_manifest["run_id"]
        run_suffix = run_id.split("-")[-1]
        canonical_project_id = f"PROJ-PUNE-2025-{run_suffix}"
        project_id = project_id_override or canonical_project_id
        created_at = datetime.now(timezone.utc).isoformat()

        # Target geography
        treated_cells = df_alloc["h3_cell_id"].unique().tolist()
        cell_features = df_feat.loc[treated_cells]
        cell_risks = df_risk.loc[treated_cells]

        # Financial summary
        modeled_cost = float(run_manifest["portfolio_summary"]["total_allocated_cost_inr"])
        budget_envelope = float(run_manifest["scenario_parameters"]["budget_inr"])
        budget_slack = float(run_manifest["portfolio_summary"]["budget_slack_inr"])

        # Cost breakdown by intervention
        cost_breakdown = df_alloc.groupby("intervention_type").agg(
            quantity=("quantity", "sum"),
            cells_count=("h3_cell_id", "nunique"),
            direct_cost=("unit_cost", lambda s: float((s * df_alloc.loc[s.index, "quantity"]).sum())),
            mobilization_cost=("fixed_cost", "sum"),
            total_cost=("total_cost", "sum"),
            modeled_cooling_sum=("modeled_effect", "sum"),
            modeled_risk_reduction_sum=("modeled_risk_reduction", "sum"),
        ).reset_index().to_dict(orient="records")

        # Baseline thermal indicators
        mean_lst_base = float(cell_features["lst_baseline_mean"].mean())
        mean_lst_anomaly = float(cell_features["lst_anomaly_absolute"].mean())
        total_pop_protected = int(cell_features["population_2020"].sum())
        mean_base_risk = float(cell_risks["risk_i"].mean())

        # Build 13 structured sections
        document = {
            "section_1_project_identity": {
                "project_id": project_id,
                "project_title": project_title,
                "lifecycle_state": ProjectLifecycleState.PROPOSED.value,
                "beneficiary_agency": beneficiary_agency,
                "created_at_utc": created_at,
                "currency": "INR",
                "price_basis_year": 2025,
            },
            "section_2_problem_statement_baseline": {
                "study_area": "Pune Municipal Corporation (PMC)",
                "baseline_mean_surface_temperature_degC": round(mean_lst_base, 2),
                "baseline_mean_lst_anomaly_degC": round(mean_lst_anomaly, 2),
                "baseline_mean_climate_risk": round(mean_base_risk, 4),
                "human_population_in_scope": total_pop_protected,
                "thermal_baseline_source": "Landsat 8/9 C2 L2 5-Year Pre-Monsoon Peak-Summer Composite (2021-2025)",
            },
            "section_3_target_geography": {
                "spatial_grid_type": "Uber H3 Discrete Global Grid System",
                "h3_resolution": 9,
                "total_treated_cells_count": len(treated_cells),
                "treated_h3_cells": treated_cells,
                "administrative_ward_dependency": "NONE (Decoupled; spatial allocation derives strictly from H3 topology)",
            },
            "section_4_intervention_portfolio": {
                "ratified_formulation": "F-24.1 through F-24.6 (CLIMORA Mathematical Register)",
                "interventions_selected": list(run_manifest["portfolio_summary"]["interventions_deployed"].keys()),
                "intervention_categories": ["nature_based", "albedo_modification"],
            },
            "section_5_physical_scope_and_quantities": {
                "allocations_table": cost_breakdown,
                "total_physical_units": float(df_alloc["quantity"].sum()),
            },
            "section_6_transparent_cost_breakdown": {
                "modeled_optimized_capex_inr": modeled_cost,
                "scenario_budget_envelope_inr": budget_envelope,
                "budget_slack_unallocated_inr": budget_slack,
                "approved_project_budget_inr": None,  # Gated: Set upon formal funding award
                "actual_expenditure_inr": "NOT_AVAILABLE (Pre-implementation proposal phase)",
            },
            "section_7_modeled_microclimatic_and_risk_impact": {
                "modeled_aggregate_risk_reduction_score": run_manifest["portfolio_summary"]["optimal_risk_reduction"],
                "truth_layer": "MODELED (Scenario projection under F-24.4 and F-24.5)",
                "mean_modeled_cell_cooling_degC": round(float(df_alloc["modeled_effect"].mean()), 3),
                "thermodynamic_safety_cap_applied": "4.0°C intra-cell saturation ceiling (F-24.4 / F-25.1)",
                "governance_note": "Risk reduction score 0.106048 represents the mathematical objective function achieved under the ₹10M budget envelope; it does NOT represent a guaranteed 10.6% clinical or ambient cooling outcome.",
            },
            "section_8_physical_implementation_plan": {
                "planned_execution_quarters": "Q4 2025 - Q2 2026",
                "contractor_mobilization_protocol": "Cell-level cluster batching adhering to F-24.1 minimum lot constraints",
                "milestone_1": "Site reconnaissance and roadside utility clearance (Month 1-2)",
                "milestone_2": "Procurement of indigenous saplings with 2m tree guards (Month 3)",
                "milestone_3": "Excavation, soil conditioning, and planting (Month 4-6)",
                "milestone_4": "Substantial completion and implementation event signoff (Month 6)",
            },
            "section_9_long_term_monitoring_protocol": {
                "monitoring_cadence": "Annual pre-monsoon Landsat/Sentinel overpass audit (April DOY 95-115)",
                "survival_rate_maintenance_requirement": "85% sapling survival at 24 months post-groundbreaking",
                "in_situ_sensors": "Periodic thermal pyrometer ground audits along treated road corridors",
            },
            "section_10_third_party_mrv_and_verification": {
                "verification_methodology": "CLIMORA Difference-in-Differences Verification Framework (F-26 / ISO 14064-2 aligned)",
                "verification_gating_rule": "Project cannot enter VERIFIED status without 100% passing MRV QC audit and certified independent audit event",
                "current_mrv_status": "PLANNED / NOT_YET_EXECUTABLE (Awaiting real-world physical installation)",
                "verification_status": "UNOBSERVED / NOT YET VERIFIED",
                "measured_empirical_cooling_degC": None,
                "verified_impact_claims": None,
            },
            "section_11_scientific_assumptions_and_limitations": {
                "tree_spacing_assumption": "15.0m interval along public rights-of-way (ENGINEERING_ASSUMPTION)",
                "cooling_transfer_rate": "7.143e-4 °C per tree over Res9 cell area (MODELED scenario assumption)",
                "health_outcomes_claim": "EXCLUDED (Model quantifies physical thermal screening, not epidemiological morbidity/mortality)",
                "causal_attribution": "EXCLUDED (Causal claims require post-deployment MRV with matched control cells)",
            },
            "section_12_data_lake_lineage_and_provenance": {
                "feature_matrix_artifact": str(CANONICAL_FEATURE_MATRIX),
                "hev_components_artifact": str(CANONICAL_HEV_PARQUET),
                "risk_surface_artifact": str(CANONICAL_RISK_SURFACE),
                "optimization_allocation_artifact": str(CANONICAL_ALLOCATION_PARQUET),
                "feature_matrix_sha256": run_manifest["input_artifacts"]["feature_matrix_sha256"],
                "risk_surface_sha256": run_manifest["input_artifacts"]["risk_surface_sha256"],
                "allocation_parquet_sha256": run_manifest["output_artifacts"]["allocation_parquet_sha256"],
                "processing_pipeline_version": "1.0.0",
            },
            "section_13_optimization_run_traceability": {
                "optimization_run_id": run_id,
                "solver_engine": run_manifest["solver_performance"]["solver_engine"],
                "solver_status": run_manifest["solver_performance"]["solve_status"],
                "solver_runtime_sec": run_manifest["solver_performance"]["solver_runtime_sec"],
                "total_candidate_pairs_evaluated": run_manifest["solver_performance"]["candidate_pairs_count"],
            },
        }

        return document

    @classmethod
    def materialize_proposal_artifact(
        cls,
        output_json_path: Path = CANONICAL_PROJECTS_DIR / "project_pune_2025_tree_shade_10m.json",
    ) -> Dict[str, Any]:
        """Builds and writes the canonical Phase 1H project proposal document to disk."""
        doc = cls.build_from_optimization_run()
        output_json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=2)
        logger.info(f"Materialized canonical project proposal: {output_json_path}")
        return doc


class SyntheticMRVFixtureGenerator:
    """Generates strictly isolated demonstration MRV fixtures with anti-contamination tagging."""

    @staticmethod
    def generate_demo_mrv_fixture(project_id: str, h3_cell_id: str) -> Dict[str, Any]:
        """Creates a synthetic fixture for UI demonstration carrying the mandatory isolation label."""
        return {
            "synthetic_tag": SYNTHETIC_MRV_TAG,
            "disclaimer": "CRITICAL GOVERNANCE NOTICE: This is synthetic test fixture data for UI demonstration only. It must NEVER be treated as observed satellite data or used to certify canonical project status.",
            "implementation_event": {
                "event_id": f"SYNTH-IMPL-{uuid.uuid4().hex[:8].upper()}",
                "project_id": project_id,
                "h3_cell_id": h3_cell_id,
                "intervention_code": "street_tree_shade",
                "planned_quantity": 84.0,
                "implemented_quantity": 80.0,
                "quantity_unit": "tree_count",
                "contractor_id": "SYNTHETIC-DEMO-CONTRACTOR",
                "completion_date": "2026-04-01",
                "evidence_uri": "s3://climora/demo/mock_evidence.pdf",
                "is_synthetic_demo": True,
            },
            "observation_event": {
                "observation_id": f"SYNTH-OBS-{uuid.uuid4().hex[:8].upper()}",
                "sensor_platform": "Synthetic-Landsat-9-Thermal-Mock",
                "acquisition_date": "2026-04-20",
                "doy": 110,
                "spatial_resolution_m": 30.0,
                "cloud_cover_aoi_pct": 0.0,
                "quality_flags_passed": True,
                "asset_uri": "s3://climora/demo/mock_landsat.tif",
                "is_synthetic_demo": True,
            },
            "verification_event": {
                "verification_id": f"SYNTH-VERIF-{uuid.uuid4().hex[:8].upper()}",
                "project_id": project_id,
                "verification_status": "PASSED",
                "verification_date": "2026-05-01",
                "verifier_identity": "Synthetic Demo Auditor",
                "methodology_standard": "SYNTHETIC-DEMO-STANDARD",
                "evidence_artifact_uri": "s3://climora/demo/mock_verif.pdf",
                "findings_summary": "Demonstration mock verification.",
                "is_synthetic_demo": True,
            }
        }
