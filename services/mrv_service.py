"""CLIMORA MRV Domain Service.

Enforces MRV verification guards, metric-specific sensor compatibility,
temporal window validation, physical deviation computation, and anti-contamination rules.
Prohibits synthetic fixture leakage into verified states.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

import pandas as pd

from ingestion.common import get_logger
from processing.project_mrv import (
    CANONICAL_ALLOCATION_PARQUET,
    ImplementationEvent,
    MRVQualityControlEngine,
    MRVQualityControlResult,
    ObservationEvent,
    ProjectLifecycleState,
    ProjectStateMachine,
    SYNTHETIC_MRV_TAG,
    VerificationEvent,
    VerificationState,
)
from services.exceptions import (
    ProjectNotFoundError,
    ValidationError,
    VerificationNotEligibleError,
)

logger = get_logger()


class MRVDomainService:
    """Application service governing implementation tracking, observation QC audits, and verification."""

    def __init__(self, allocation_df: Optional[pd.DataFrame] = None):
        if allocation_df is None:
            self._df_alloc = pd.read_parquet(CANONICAL_ALLOCATION_PARQUET)
        else:
            self._df_alloc = allocation_df.copy(deep=True)

        self._implementation_events: Dict[str, List[ImplementationEvent]] = {}
        self._observation_events: Dict[str, List[ObservationEvent]] = {}
        self._qc_results: Dict[str, List[MRVQualityControlResult]] = {}
        self._verification_events: Dict[str, List[VerificationEvent]] = {}

    def _get_planned_quantity(self, h3_cell_id: str, intervention_code: str) -> float:
        """Retrieves planned quantity from canonical allocation for cell and intervention."""
        mask = (self._df_alloc["h3_cell_id"] == h3_cell_id) & (
            self._df_alloc["intervention_type"] == intervention_code
        )
        matches = self._df_alloc[mask]
        if len(matches) > 0:
            return float(matches["quantity"].iloc[0])
        return 0.0

    def record_implementation_event(
        self,
        project_id: str,
        intervention_code: str,
        h3_cell_id: str,
        implemented_quantity: float,
        quantity_unit: str = "tree_count",
        contractor_id: str = "PMC-FORESTRY-CONTRACTOR",
        completion_date: str = "2026-04-15",
        evidence_uri: str = "s3://climora/evidence/default.pdf",
        is_synthetic_demo: bool = False,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Validates and records a physical deployment event while guaranteeing allocation immutability."""
        # 1. Validation: quantity must be non-negative
        if implemented_quantity < 0.0:
            raise ValidationError(
                "Implemented quantity must be non-negative.",
                details={"implemented_quantity": implemented_quantity},
            )

        # 2. Validation: H3 cell format
        h3_str = str(h3_cell_id).strip().lower()
        if len(h3_str) < 14 or not all(c in "0123456789abcdef" for c in h3_str):
            raise ValidationError(
                f"Invalid H3 cell identifier '{h3_cell_id}'. Must be a valid H3 hexadecimal index.",
                details={"h3_cell_id": h3_cell_id},
            )

        # 3. Retrieve planned quantity from canonical allocation
        planned_quantity = self._get_planned_quantity(h3_str, intervention_code)

        # 4. Create ImplementationEvent (deviation and deviation_rate calculated automatically)
        event_id = f"EVT-IMPL-{uuid.uuid4().hex[:8].upper()}"
        event = ImplementationEvent(
            event_id=event_id,
            project_id=project_id,
            h3_cell_id=h3_str,
            intervention_code=intervention_code,
            planned_quantity=planned_quantity,
            implemented_quantity=float(implemented_quantity),
            quantity_unit=quantity_unit,
            contractor_id=contractor_id,
            completion_date=completion_date,
            evidence_uri=evidence_uri,
            is_synthetic_demo=is_synthetic_demo,
        )

        if project_id not in self._implementation_events:
            self._implementation_events[project_id] = []
        self._implementation_events[project_id].append(event)

        logger.info(
            f"Logged implementation event {event_id} for {project_id}: "
            f"planned={planned_quantity}, implemented={implemented_quantity}, dev={event.deviation}"
        )

        return {
            "event_id": event.event_id,
            "project_id": event.project_id,
            "h3_cell_id": event.h3_cell_id,
            "intervention_code": event.intervention_code,
            "planned_quantity": event.planned_quantity,
            "implemented_quantity": event.implemented_quantity,
            "deviation": event.deviation,
            "deviation_rate": event.deviation_rate,
            "quantity_unit": event.quantity_unit,
            "contractor_id": event.contractor_id,
            "completion_date": event.completion_date,
            "evidence_uri": event.evidence_uri,
            "is_synthetic_demo": event.is_synthetic_demo,
            "notes": notes,
        }

    def get_mrv_overview(self, project_id: str) -> Dict[str, Any]:
        """Returns the complete MRV tracking and readiness status for a project."""
        impl_events = self._implementation_events.get(project_id, [])
        obs_events = self._observation_events.get(project_id, [])
        verif_events = self._verification_events.get(project_id, [])

        total_planned = float(self._df_alloc["quantity"].sum())
        total_implemented = sum(e.implemented_quantity for e in impl_events)
        overall_dev = total_implemented - total_planned
        overall_dev_rate = (overall_dev / total_planned) if total_planned > 0 else None

        # Determine states
        if not impl_events:
            impl_status = "PLANNED"
        elif total_implemented >= total_planned:
            impl_status = "COMPLETED"
        else:
            impl_status = "IN_PROGRESS"

        verif_state = VerificationState.NOT_STARTED.value
        if verif_events:
            verif_state = verif_events[-1].verification_status

        qc_state = "NOT_PERFORMED"
        if project_id in self._qc_results and self._qc_results[project_id]:
            qc = self._qc_results[project_id][-1]
            qc_state = "PASSED" if qc.all_passed else "FAILED"

        return {
            "project_id": project_id,
            "implementation_status": impl_status,
            "total_planned_quantity": total_planned,
            "total_implemented_quantity": total_implemented,
            "overall_deviation": overall_dev,
            "overall_deviation_rate": overall_dev_rate,
            "quantity_unit": "tree_count",
            "implementation_events_count": len(impl_events),
            "implementation_events": [
                {
                    "event_id": e.event_id,
                    "h3_cell_id": e.h3_cell_id,
                    "intervention_code": e.intervention_code,
                    "planned_quantity": e.planned_quantity,
                    "implemented_quantity": e.implemented_quantity,
                    "deviation": e.deviation,
                    "deviation_rate": e.deviation_rate,
                    "quantity_unit": e.quantity_unit,
                    "contractor_id": e.contractor_id,
                    "completion_date": e.completion_date,
                    "evidence_uri": e.evidence_uri,
                    "is_synthetic_demo": e.is_synthetic_demo,
                }
                for e in impl_events
            ],
            "observation_events_count": len(obs_events),
            "observation_events": [
                {
                    "observation_id": o.observation_id,
                    "sensor_platform": o.sensor_platform,
                    "acquisition_date": o.acquisition_date,
                    "doy": o.doy,
                    "spatial_resolution_m": o.spatial_resolution_m,
                    "cloud_cover_aoi_pct": o.cloud_cover_aoi_pct,
                    "quality_flags_passed": o.quality_flags_passed,
                    "asset_uri": o.asset_uri,
                    "is_synthetic_demo": o.is_synthetic_demo,
                }
                for o in obs_events
            ],
            "qc_state": qc_state,
            "verification_state": verif_state,
            "verification_events_count": len(verif_events),
            "verification_events": [
                {
                    "verification_id": v.verification_id,
                    "verification_status": v.verification_status,
                    "verification_date": v.verification_date,
                    "verifier_identity": v.verifier_identity,
                    "methodology_standard": v.methodology_standard,
                    "evidence_artifact_uri": v.evidence_artifact_uri,
                    "findings_summary": v.findings_summary,
                    "is_synthetic_demo": v.is_synthetic_demo,
                }
                for v in verif_events
            ],
            "verified_impact": None,
            "difference_in_differences_status": {
                "current_operational_status": "PLANNED / NOT_YET_EXECUTABLE",
                "is_executable": False,
                "rationale": (
                    "Honest empirical DID evaluation requires post-deployment satellite acquisitions "
                    "matching pre-intervention baseline seasonality. Cannot execute against baseline-only, "
                    "synthetic, or modeled data."
                ),
            },
            "truth_layer": "VERIFIED (Unobserved at proposal phase)",
        }

    def process_verification_request(
        self,
        project_id: str,
        observation_payload: Dict[str, Any],
        verification_payload: Dict[str, Any],
        target_metric: str = "lst",
        is_synthetic_demo: bool = False,
    ) -> Dict[str, Any]:
        """Processes a formal third-party verification submission through strict multi-tier gates."""
        # Check 1: Anti-Contamination Guard - Outright rejection of synthetic demo data
        if (
            is_synthetic_demo
            or observation_payload.get("is_synthetic_demo", False)
            or verification_payload.get("is_synthetic_demo", False)
            or observation_payload.get("synthetic_tag") == SYNTHETIC_MRV_TAG
        ):
            raise VerificationNotEligibleError(
                message=f"REJECTED: Demo fixture ({SYNTHETIC_MRV_TAG}) cannot set canonical project status to VERIFIED.",
                details={
                    "error_code": "DEMO_FIXTURE_REJECTED",
                    "reason": "Synthetic demonstration fixtures are prohibited from certifying production projects.",
                },
            )

        # Check 2: Physical implementation evidence must exist
        impl_events = self._implementation_events.get(project_id, [])
        if not impl_events:
            raise VerificationNotEligibleError(
                message="Project does not satisfy verification prerequisites: missing physical implementation evidence.",
                details={
                    "current_state": "MONITORING",
                    "missing_requirements": ["PHYSICAL_IMPLEMENTATION_EVENTS"],
                },
            )

        # Check 3: Assemble ObservationEvent
        obs_id = observation_payload.get("observation_id") or f"OBS-{uuid.uuid4().hex[:8].upper()}"
        obs_event = ObservationEvent(
            observation_id=obs_id,
            sensor_platform=observation_payload["sensor_platform"],
            acquisition_date=observation_payload["acquisition_date"],
            doy=int(observation_payload["doy"]),
            spatial_resolution_m=float(observation_payload.get("spatial_resolution_m", 30.0)),
            cloud_cover_aoi_pct=float(observation_payload["cloud_cover_aoi_pct"]),
            quality_flags_passed=bool(observation_payload["quality_flags_passed"]),
            asset_uri=observation_payload["asset_uri"],
            is_synthetic_demo=False,
        )

        # Check 4: Execute 5 mandatory MRV QC checks
        treated_cell_count = len(self._df_alloc["h3_cell_id"].unique())
        raw_count = observation_payload.get("observed_cell_count")
        observed_cell_count = int(raw_count) if raw_count is not None else treated_cell_count

        qc_result = MRVQualityControlEngine.audit_observation(
            observation=obs_event,
            treated_cell_count=treated_cell_count,
            observed_cell_count=observed_cell_count,
            target_metric=target_metric,
        )

        if project_id not in self._qc_results:
            self._qc_results[project_id] = []
        self._qc_results[project_id].append(qc_result)

        if not qc_result.all_passed:
            raise VerificationNotEligibleError(
                message="MRV Quality Control audit failed: observation does not meet scientific comparability criteria.",
                details={
                    "qc_passed": False,
                    "violations": qc_result.violations,
                    "temporal_tier": qc_result.temporal_tier,
                    "cloud_screening_passed": qc_result.cloud_screening_passed,
                    "sensor_consistency_passed": qc_result.sensor_consistency_passed,
                },
            )

        # Check 5: Assemble and validate third-party verification event
        verif_status = verification_payload.get("verification_status", "FAILED")
        if verif_status != "PASSED":
            raise VerificationNotEligibleError(
                message=f"Verification event must have status 'PASSED', received '{verif_status}'.",
                details={"verification_status": verif_status},
            )

        verif_id = verification_payload.get("verification_id") or f"VERIF-{uuid.uuid4().hex[:8].upper()}"
        verif_event = VerificationEvent(
            verification_id=verif_id,
            project_id=project_id,
            verification_status="PASSED",
            verification_date=verification_payload["verification_date"],
            verifier_identity=verification_payload["verifier_identity"],
            methodology_standard=verification_payload["methodology_standard"],
            evidence_artifact_uri=verification_payload["evidence_artifact_uri"],
            findings_summary=verification_payload.get("findings_summary", "Formal audit passed."),
            is_synthetic_demo=False,
        )

        # Store validated events in service registry
        if project_id not in self._observation_events:
            self._observation_events[project_id] = []
        self._observation_events[project_id].append(obs_event)

        if project_id not in self._verification_events:
            self._verification_events[project_id] = []
        self._verification_events[project_id].append(verif_event)

        # Check 6: State machine transition check
        can_trans, reason = ProjectStateMachine.can_transition(
            current_state=ProjectLifecycleState.MONITORING,
            target_state=ProjectLifecycleState.VERIFIED,
            context={
                "implementation_events": impl_events,
                "observation_event": obs_event,
                "qc_result": qc_result,
                "verification_event": verif_event,
            },
        )

        if not can_trans:
            raise VerificationNotEligibleError(
                message=f"State machine rejected transition to VERIFIED: {reason}",
                details={"reason": reason},
            )

        logger.info(f"Project '{project_id}' successfully verified under audit {verif_event.verification_id}.")

        return {
            "project_id": project_id,
            "verification_status": "VERIFIED",
            "verification_id": verif_event.verification_id,
            "verifier_identity": verif_event.verifier_identity,
            "methodology_standard": verif_event.methodology_standard,
            "verification_date": verif_event.verification_date,
            "qc_audit": {
                "all_passed": True,
                "temporal_tier": qc_result.temporal_tier,
                "violations_count": 0,
            },
            "observation_id": obs_event.observation_id,
            "truth_layer": "VERIFIED",
        }
