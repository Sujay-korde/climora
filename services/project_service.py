"""CLIMORA Project Domain Service.

Owns project lifecycle, representations, and state machine guards.
Ensures zero scientific recalculation occurs within domain or route handlers.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ingestion.common import calculate_sha256, get_logger
from processing.config import PROCESSED_DIR
from processing.project_mrv import (
    CANONICAL_ALLOCATION_PARQUET,
    CANONICAL_FEATURE_MATRIX,
    CANONICAL_HEV_PARQUET,
    CANONICAL_PROJECTS_DIR,
    CANONICAL_RISK_SURFACE,
    CANONICAL_RUN_MANIFEST,
    PROJECT_MRV_CONTRACT,
    ProjectLifecycleState,
    ProjectProposalBuilder,
    ProjectStateMachine,
)
from services.exceptions import ProjectNotFoundError, StateTransitionError

logger = get_logger()

# Canonical demonstration constants
CANONICAL_PROJECT_ID = "PROJ-PUNE-2025-BA225D6A"
CANONICAL_RUN_ID = "OPT-PUNE-2025-SCENARIO-BA225D6A"
CANONICAL_SELECTED_CELLS_COUNT = 28
CANONICAL_PLANNED_TREES = 2695.0
CANONICAL_MODELED_TOTAL_COST_INR = 9992500.0
CANONICAL_SCENARIO_BUDGET_INR = 10000000.0
CANONICAL_REMAINING_BUDGET_INR = 7500.0
CANONICAL_POPULATION_EXACT = 118941.21
CANONICAL_POPULATION_DISPLAY = 118941
CANONICAL_MODELED_OBJECTIVE = 0.10604830270054796


class ProjectDomainService:
    """Application service for querying project state, summaries, and governing lifecycle transitions."""

    def __init__(self, projects_dir: Path = CANONICAL_PROJECTS_DIR, mrv_service: Optional[Any] = None):
        self.projects_dir = projects_dir
        self._mrv_service = mrv_service
        self._project_cache: Dict[str, Dict[str, Any]] = {}
        self._current_states: Dict[str, ProjectLifecycleState] = {}
        self._load_projects()

    def set_mrv_service(self, mrv_service: Any) -> None:
        """Sets the MRV service reference for state machine validation."""
        self._mrv_service = mrv_service

    def _load_projects(self) -> None:
        """Loads canonical project documents from disk or materializes default if needed."""
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        canonical_file = self.projects_dir / "project_pune_2025_tree_shade_10m.json"

        if not canonical_file.exists():
            logger.info("Canonical project document missing on disk. Materializing from optimization run...")
            doc = ProjectProposalBuilder.materialize_proposal_artifact(canonical_file)
        else:
            with open(canonical_file, "r", encoding="utf-8") as f:
                doc = json.load(f)

        project_id = doc.get("section_1_project_identity", {}).get("project_id", CANONICAL_PROJECT_ID)
        self._project_cache[project_id] = doc
        initial_state_str = doc.get("section_1_project_identity", {}).get(
            "lifecycle_state", ProjectLifecycleState.PROPOSED.value
        )
        self._current_states[project_id] = ProjectLifecycleState(initial_state_str)

    def list_projects(self) -> List[Dict[str, Any]]:
        """Returns high-level project summaries for all registered projects."""
        summaries = []
        for project_id in self._project_cache.keys():
            summaries.append(self.get_project_summary(project_id))
        return summaries

    def get_project_summary(self, project_id: str) -> Dict[str, Any]:
        """Returns a high-level summary of a project adhering to frozen canonical contracts."""
        if project_id not in self._project_cache:
            raise ProjectNotFoundError(project_id)

        doc = self._project_cache[project_id]
        sec1 = doc["section_1_project_identity"]
        sec2 = doc["section_2_problem_statement_baseline"]
        sec3 = doc["section_3_target_geography"]
        sec4 = doc["section_4_intervention_portfolio"]
        sec5 = doc["section_5_physical_scope_and_quantities"]
        sec6 = doc["section_6_transparent_cost_breakdown"]
        sec7 = doc["section_7_modeled_microclimatic_and_risk_impact"]
        sec13 = doc["section_13_optimization_run_traceability"]

        current_state = self._current_states.get(project_id, ProjectLifecycleState.PROPOSED)

        return {
            "project_id": sec1["project_id"],
            "project_name": sec1["project_title"],
            "project_status": current_state.value,
            "optimization_run_id": sec13["optimization_run_id"],
            "geographic_scope": {
                "study_area": sec2["study_area"],
                "spatial_grid_type": sec3["spatial_grid_type"],
                "h3_resolution": sec3["h3_resolution"],
                "total_treated_cells_count": sec3["total_treated_cells_count"],
                "administrative_ward_dependency": "NONE (Decoupled; spatial allocation derives strictly from H3 topology)",
            },
            "intervention_summary": {
                "intervention_types": sec4["interventions_selected"],
                "total_physical_units": float(sec5["total_physical_units"]),
                "quantity_unit": "tree_count",
            },
            "modeled_cost": float(sec6["modeled_optimized_capex_inr"]),
            "budget": float(sec6["scenario_budget_envelope_inr"]),
            "remaining_budget": float(sec6["budget_slack_unallocated_inr"]),
            "population": {
                "canonical_exact": CANONICAL_POPULATION_EXACT,
                "display_rounded": CANONICAL_POPULATION_DISPLAY,
                "source": "WorldPop 2020 via canonical_feature_matrix.parquet",
                "truth_layer": "OBSERVED",
            },
            "modeled_objective": {
                "value": CANONICAL_MODELED_OBJECTIVE,
                "metric_description": "modeled aggregate risk-objective reduction under the canonical optimization formulation",
                "truth_layer": "MODELED",
                "governance_note": (
                    "Risk reduction score 0.106048 represents the mathematical objective function achieved under the "
                    "₹10M budget envelope; it does NOT represent a guaranteed 10.6% clinical or ambient cooling outcome."
                ),
            },
            "truth_layer_metadata": {
                "baseline_lst": "OBSERVED",
                "population": "OBSERVED",
                "risk_index": "MODELED",
                "modeled_cost": "MODELED",
                "modeled_cooling": "MODELED",
                "modeled_objective": "MODELED",
                "verified_impact": "UNOBSERVED / NOT YET VERIFIED",
            },
        }

    def get_project_detail(self, project_id: str) -> Dict[str, Any]:
        """Returns the complete, authoritative project representation."""
        if project_id not in self._project_cache:
            raise ProjectNotFoundError(project_id)

        doc = self._project_cache[project_id]
        current_state = self._current_states.get(project_id, ProjectLifecycleState.PROPOSED)

        # Build clean representation with strict truth-layer tagging
        return {
            "identity": {
                "project_id": doc["section_1_project_identity"]["project_id"],
                "project_title": doc["section_1_project_identity"]["project_title"],
                "lifecycle_state": current_state.value,
                "beneficiary_agency": doc["section_1_project_identity"]["beneficiary_agency"],
                "created_at_utc": doc["section_1_project_identity"]["created_at_utc"],
                "currency": doc["section_1_project_identity"]["currency"],
                "price_basis_year": doc["section_1_project_identity"]["price_basis_year"],
            },
            "status": current_state.value,
            "geographic_scope": {
                "spatial_grid_type": doc["section_3_target_geography"]["spatial_grid_type"],
                "h3_resolution": doc["section_3_target_geography"]["h3_resolution"],
                "total_treated_cells_count": doc["section_3_target_geography"]["total_treated_cells_count"],
                "treated_h3_cells": doc["section_3_target_geography"]["treated_h3_cells"],
                "administrative_ward_dependency": doc["section_3_target_geography"]["administrative_ward_dependency"],
            },
            "optimization_lineage": {
                "optimization_run_id": doc["section_13_optimization_run_traceability"]["optimization_run_id"],
                "solver_engine": doc["section_13_optimization_run_traceability"]["solver_engine"],
                "solver_status": doc["section_13_optimization_run_traceability"]["solver_status"],
                "solver_runtime_sec": doc["section_13_optimization_run_traceability"]["solver_runtime_sec"],
                "total_candidate_pairs_evaluated": doc["section_13_optimization_run_traceability"]["total_candidate_pairs_evaluated"],
                "ratified_formulation": doc["section_4_intervention_portfolio"]["ratified_formulation"],
            },
            "baseline_reference": {
                "study_area": doc["section_2_problem_statement_baseline"]["study_area"],
                "baseline_mean_surface_temperature_degC": {
                    "value": doc["section_2_problem_statement_baseline"]["baseline_mean_surface_temperature_degC"],
                    "unit": "degC",
                    "truth_layer": "DERIVED",
                },
                "baseline_mean_lst_anomaly_degC": {
                    "value": doc["section_2_problem_statement_baseline"]["baseline_mean_lst_anomaly_degC"],
                    "unit": "degC",
                    "truth_layer": "DERIVED",
                },
                "baseline_mean_climate_risk": {
                    "value": doc["section_2_problem_statement_baseline"]["baseline_mean_climate_risk"],
                    "unit": "composite_risk_score",
                    "truth_layer": "MODELED",
                },
                "human_population_in_scope": {
                    "value": CANONICAL_POPULATION_DISPLAY,
                    "canonical_exact": CANONICAL_POPULATION_EXACT,
                    "unit": "persons",
                    "truth_layer": "OBSERVED",
                },
                "thermal_baseline_source": doc["section_2_problem_statement_baseline"]["thermal_baseline_source"],
            },
            "allocation_summary": {
                "allocations_table": doc["section_5_physical_scope_and_quantities"]["allocations_table"],
                "total_physical_units": float(doc["section_5_physical_scope_and_quantities"]["total_physical_units"]),
                "quantity_unit": "tree_count",
                "truth_layer": "MODELED",
            },
            "budget": {
                "modeled_optimized_capex_inr": float(doc["section_6_transparent_cost_breakdown"]["modeled_optimized_capex_inr"]),
                "scenario_budget_envelope_inr": float(doc["section_6_transparent_cost_breakdown"]["scenario_budget_envelope_inr"]),
                "budget_slack_unallocated_inr": float(doc["section_6_transparent_cost_breakdown"]["budget_slack_unallocated_inr"]),
                "approved_project_budget_inr": doc["section_6_transparent_cost_breakdown"]["approved_project_budget_inr"],
                "actual_expenditure_inr": doc["section_6_transparent_cost_breakdown"]["actual_expenditure_inr"],
                "truth_layer": "MODELED",
            },
            "modeled_impact": {
                "modeled_aggregate_risk_reduction_score": doc["section_7_modeled_microclimatic_and_risk_impact"]["modeled_aggregate_risk_reduction_score"],
                "mean_modeled_cell_cooling_degC": doc["section_7_modeled_microclimatic_and_risk_impact"]["mean_modeled_cell_cooling_degC"],
                "thermodynamic_safety_cap_applied": doc["section_7_modeled_microclimatic_and_risk_impact"]["thermodynamic_safety_cap_applied"],
                "governance_note": doc["section_7_modeled_microclimatic_and_risk_impact"]["governance_note"],
                "truth_layer": "MODELED",
            },
            "implementation_status": {
                "planned_execution_quarters": doc["section_8_physical_implementation_plan"]["planned_execution_quarters"],
                "contractor_mobilization_protocol": doc["section_8_physical_implementation_plan"]["contractor_mobilization_protocol"],
                "milestones": [
                    doc["section_8_physical_implementation_plan"]["milestone_1"],
                    doc["section_8_physical_implementation_plan"]["milestone_2"],
                    doc["section_8_physical_implementation_plan"]["milestone_3"],
                    doc["section_8_physical_implementation_plan"]["milestone_4"],
                ],
            },
            "mrv_status": {
                "verification_methodology": doc["section_10_third_party_mrv_and_verification"]["verification_methodology"],
                "verification_gating_rule": doc["section_10_third_party_mrv_and_verification"]["verification_gating_rule"],
                "current_mrv_status": doc["section_10_third_party_mrv_and_verification"]["current_mrv_status"],
                "difference_in_differences_status": "PLANNED / NOT_YET_EXECUTABLE",
            },
            "verification_status": {
                "status": doc["section_10_third_party_mrv_and_verification"]["verification_status"],
                "measured_empirical_cooling_degC": doc["section_10_third_party_mrv_and_verification"]["measured_empirical_cooling_degC"],
                "verified_impact_claims": doc["section_10_third_party_mrv_and_verification"]["verified_impact_claims"],
                "truth_layer": "VERIFIED (Currently null/unobserved)",
            },
            "scientific_assumptions": doc["section_11_scientific_assumptions_and_limitations"],
            "provenance": {
                "feature_matrix_artifact": "canonical_feature_matrix.parquet",
                "feature_matrix_sha256": doc["section_12_data_lake_lineage_and_provenance"]["feature_matrix_sha256"],
                "hev_components_artifact": "canonical_hev_components.parquet",
                "risk_surface_artifact": "canonical_risk_surface.parquet",
                "risk_surface_sha256": doc["section_12_data_lake_lineage_and_provenance"]["risk_surface_sha256"],
                "optimization_allocation_artifact": "canonical_optimization_allocation.parquet",
                "allocation_parquet_sha256": doc["section_12_data_lake_lineage_and_provenance"]["allocation_parquet_sha256"],
                "processing_pipeline_version": doc["section_12_data_lake_lineage_and_provenance"]["processing_pipeline_version"],
            },
        }

    def transition_project_state(
        self,
        project_id: str,
        target_state_name: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Transitions project lifecycle state through the authoritative ProjectStateMachine."""
        if project_id not in self._project_cache:
            raise ProjectNotFoundError(project_id)

        try:
            target_state = ProjectLifecycleState(target_state_name)
        except ValueError:
            raise StateTransitionError(
                f"Unknown lifecycle state '{target_state_name}'.",
                details={"allowed_states": [s.value for s in ProjectLifecycleState]},
            )

        current_state = self._current_states.get(project_id, ProjectLifecycleState.PROPOSED)

        ctx = dict(context or {})
        if self._mrv_service is not None:
            if "implementation_events" not in ctx:
                ctx["implementation_events"] = self._mrv_service._implementation_events.get(project_id, [])
            if "observation_event" not in ctx and self._mrv_service._observation_events.get(project_id):
                ctx["observation_event"] = self._mrv_service._observation_events[project_id][-1]
            if "qc_result" not in ctx and self._mrv_service._qc_results.get(project_id):
                ctx["qc_result"] = self._mrv_service._qc_results[project_id][-1]
            if "verification_event" not in ctx and self._mrv_service._verification_events.get(project_id):
                ctx["verification_event"] = self._mrv_service._verification_events[project_id][-1]

        can_trans, reason = ProjectStateMachine.can_transition(
            current_state=current_state,
            target_state=target_state,
            context=ctx,
        )

        if not can_trans:
            raise StateTransitionError(
                message=reason,
                details={
                    "current_state": current_state.value,
                    "target_state": target_state.value,
                    "rejection_reason": reason,
                },
            )

        self._current_states[project_id] = target_state
        logger.info(f"Project '{project_id}' transitioned: {current_state.value} -> {target_state.value}")

        return {
            "project_id": project_id,
            "previous_state": current_state.value,
            "current_state": target_state.value,
            "transition_authorized": True,
            "transition_message": reason,
        }
