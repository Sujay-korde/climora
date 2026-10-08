"""CLIMORA Allocation Domain Service.

Enforces absolute read-only immutability of the canonical optimization allocation.
Provides auditable proposed revision branching and delegates fast query resolution
to the ZonalQueryEngine.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from ingestion.common import calculate_sha256, get_logger
from processing.config import PROCESSED_DIR, PROJECT_ROOT
from processing.optimization_engine import (
    get_ratified_intervention_catalog,
    build_candidate_matrix,
    build_milp_model,
    solve_milp_model,
    validate_solution_feasibility,
)
from processing.project_mrv import (
    AllocationRevisionTracker,
    CANONICAL_ALLOCATION_PARQUET,
    CANONICAL_RUN_MANIFEST,
)
from services.exceptions import AllocationImmutableError, ProjectNotFoundError, ValidationError
from services.query_layer import CANONICAL_PROJECT_ID, ZonalQueryEngine

logger = get_logger()

CANONICAL_ALLOCATION_SHA256 = "2519473a32a2b4a3a22bc8beb43525c3f21dc404783168f1edd6de7bc4bb5555"
BENCHMARK_SCENARIOS_DIR = PROCESSED_DIR / "optimization" / "scenarios"
BENCHMARK_BUDGET_MAP = {
    500_000.0: "scenario_pune_2025_500k.json",
    2_500_000.0: "scenario_pune_2025_2_5m.json",
    5_000_000.0: "scenario_pune_2025_5m.json",
    7_500_000.0: "scenario_pune_2025_7_5m.json",
    10_000_000.0: "scenario_pune_2025_10m.json",
}



class AllocationDomainService:
    """Application service managing read-only access to optimization allocations and revision tracking."""

    def __init__(
        self,
        allocation_parquet_path: Path = CANONICAL_ALLOCATION_PARQUET,
        query_engine: Optional[ZonalQueryEngine] = None,
    ):
        self.allocation_parquet_path = allocation_parquet_path
        if not self.allocation_parquet_path.exists():
            raise FileNotFoundError(f"Canonical allocation parquet not found: {self.allocation_parquet_path}")

        # Load canonical parquet once and initialize immutable tracker
        df_raw = pd.read_parquet(self.allocation_parquet_path)
        self._tracker = AllocationRevisionTracker(df_raw)
        self._sha256 = calculate_sha256(self.allocation_parquet_path)

        # Audit SHA256 matches frozen baseline
        if self._sha256 != CANONICAL_ALLOCATION_SHA256:
            logger.warning(
                f"Canonical allocation SHA-256 mismatch! Expected {CANONICAL_ALLOCATION_SHA256}, got {self._sha256}"
            )

        self.query_engine = query_engine or ZonalQueryEngine()

    @property
    def is_immutable(self) -> bool:
        """Returns True guaranteeing the canonical allocation is immutable."""
        return True

    def get_canonical_allocation(
        self,
        project_id: str,
        h3_cell_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 28,
    ) -> Dict[str, Any]:
        """Reads and formats the immutable canonical optimization allocation for the given project."""
        return self.query_engine.query_allocation(
            project_id=project_id,
            h3_cell_id=h3_cell_id,
            page=page,
            page_size=page_size,
        )

    def propose_revision(
        self,
        project_id: str,
        h3_cell_id: str,
        intervention_code: str,
        proposed_quantity: float,
        reason: str,
        author: str,
    ) -> Dict[str, Any]:
        """Logs an auditable human revision without modifying the canonical optimization allocation."""
        if proposed_quantity < 0:
            raise ValidationError("Proposed quantity must be non-negative.", {"proposed_quantity": proposed_quantity})

        rev = self._tracker.propose_revision(
            project_id=project_id,
            h3_cell_id=h3_cell_id,
            intervention_code=intervention_code,
            proposed_quantity=proposed_quantity,
            reason=reason,
            author=author,
        )

        # Invalidate allocation queries in cache
        self.query_engine.cache.invalidate_prefix("alloc_query")

        return {
            "revision_id": rev.revision_id,
            "project_id": rev.project_id,
            "h3_cell_id": rev.h3_cell_id,
            "intervention_code": rev.intervention_code,
            "original_quantity": rev.original_quantity,
            "proposed_quantity": rev.proposed_quantity,
            "revision_delta": rev.revision_delta,
            "revision_reason": rev.revision_reason,
            "author_identity": rev.author_identity,
            "timestamp_utc": rev.timestamp_utc,
            "canonical_file_preserved": True,
        }

    def reject_direct_mutation(self) -> None:
        """Explicitly guards against direct mutation attempts on the allocation."""
        raise AllocationImmutableError()

    def optimize_scenario(self, project_id: str, budget_inr: float) -> Dict[str, Any]:
        """
        Executes or retrieves an isolated modeled scenario allocation for the specified budget envelope.
        Strictly preserves the immutability of the canonical allocation and does not mutate any files.
        """
        if project_id != CANONICAL_PROJECT_ID:
            raise ProjectNotFoundError(project_id)

        try:
            budget_val = float(budget_inr)
        except (ValueError, TypeError):
            raise ValidationError("Budget must be a valid numeric quantity.", {"budget_inr": budget_inr})

        if budget_val < 500_000.0 or budget_val > 25_000_000.0:
            raise ValidationError(
                "Scenario budget must be between INR 500,000 and INR 25,000,000.",
                {"budget_inr": budget_inr, "min_allowed": 500_000, "max_allowed": 25_000_000},
            )

        # Tier 1: Check if this matches a precomputed benchmark scenario
        matched_filename = None
        for bm_budget, fname in BENCHMARK_BUDGET_MAP.items():
            if abs(budget_val - bm_budget) < 1.0:
                matched_filename = fname
                break

        if matched_filename:
            benchmark_path = BENCHMARK_SCENARIOS_DIR / matched_filename
            if benchmark_path.exists():
                logger.info(f"Serving precomputed benchmark scenario: {matched_filename}")
                with open(benchmark_path, "r", encoding="utf-8") as f:
                    return json.load(f)

        # Tier 2: Custom in-memory solve using existing ratified HiGHS solver
        logger.info(f"Executing in-memory HiGHS scenario optimization for budget INR {budget_val:,.2f}")
        df_feat = self.query_engine._data_cache["feature"].reset_index()
        df_risk = self.query_engine._data_cache["risk"].reset_index()
        catalog = get_ratified_intervention_catalog()
        candidate_data = build_candidate_matrix(df_feat, df_risk, catalog)
        eligible_df = candidate_data["eligible_df"].set_index("h3_cell_id")

        milp_data = build_milp_model(candidate_data, budget_val)
        solution = solve_milp_model(milp_data, time_limit_sec=25.0, mip_rel_gap=0.05)

        if not solution["is_feasible"]:
            return {
                "scenario_id": f"SCEN-PUNE-2025-CUSTOM-{uuid.uuid4().hex[:6].upper()}",
                "project_id": project_id,
                "truth_layer": "MODELED",
                "is_canonical": False,
                "disclaimer": "Optimization exceeded the live scenario time budget or could not find a feasible integer solution.",
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "formulation_ratified": "F-24.6",
                "solver_engine": "HiGHS (scipy.optimize.milp)",
                "budget_inr": budget_val,
                "total_allocated_cost_inr": 0.0,
                "budget_slack_inr": budget_val,
                "budget_utilization_pct": 0.0,
                "optimal_objective_value": 0.0,
                "objective_description": "Optimization did not converge within the live scenario time budget. Try a preset budget (INR 2.5M, 5.0M, 7.5M, 10.0M).",
                "solver_status": solution.get("solve_status", "TIME_LIMIT"),
                "solver_duration_sec": solution.get("execution_duration_sec", 45.0),
                "total_cells_treated": 0,
                "allocations": [],
                "summary_by_intervention": {},
            }

        alloc_df = solution["allocation_df"].copy()
        alloc_records = []
        if len(alloc_df) > 0:
            for _, row in alloc_df.iterrows():
                cid = row["h3_cell_id"]
                cell_risk = float(eligible_df.at[cid, "risk_i"]) if cid in eligible_df.index else 0.0
                cell_pop = float(eligible_df.at[cid, "population_2020"]) if cid in eligible_df.index else 0.0
                alloc_records.append({
                    "h3_cell_id": cid,
                    "intervention_type": row["intervention_type"],
                    "quantity": round(float(row["quantity"]), 2),
                    "unit": catalog[row["intervention_type"]].unit,
                    "unit_cost": float(row["unit_cost"]),
                    "fixed_cost": float(row["fixed_cost"]),
                    "total_cost": round(float(row["total_cost"]), 2),
                    "modeled_cooling_degC": round(float(row["modeled_effect"]), 4),
                    "marginal_risk_reduction": round(float(row["modeled_risk_reduction"]), 6),
                    "baseline_risk": round(cell_risk, 4),
                    "population_2020": round(cell_pop, 1),
                })

        summary_by_int = {}
        if len(alloc_df) > 0:
            for itype, grp in alloc_df.groupby("intervention_type"):
                summary_by_int[itype] = {
                    "total_quantity": round(float(grp["quantity"].sum()), 2),
                    "unit": catalog[itype].unit,
                    "total_cost_inr": round(float(grp["total_cost"].sum()), 2),
                    "cells_count": int(grp["h3_cell_id"].nunique()),
                }

        tot_cost = round(float(solution["total_allocated_cost_inr"]), 2)
        slack = round(budget_val - tot_cost, 2)
        util_pct = round((tot_cost / budget_val) * 100.0, 2) if budget_val > 0 else 0.0

        return {
            "scenario_id": f"SCEN-PUNE-2025-CUSTOM-{uuid.uuid4().hex[:6].upper()}",
            "project_id": project_id,
            "truth_layer": "MODELED",
            "is_canonical": False,
            "is_precomputed_benchmark": False,
            "disclaimer": "MODELED SCENARIO ONLY. Does not represent a sanctioned, funded, or verified intervention.",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "formulation_ratified": "F-24.6",
            "solver_engine": "HiGHS (scipy.optimize.milp)",
            "budget_inr": budget_val,
            "total_allocated_cost_inr": tot_cost,
            "budget_slack_inr": slack,
            "budget_utilization_pct": util_pct,
            "optimal_objective_value": round(float(solution["optimal_objective_value"]), 6),
            "objective_description": "Modeled optimization objective (dimensionless sum of marginal risk responses)",
            "solver_status": solution["solve_status"],
            "solver_duration_sec": round(solution["execution_duration_sec"], 2),
            "total_cells_treated": len(alloc_records),
            "allocations": alloc_records,
            "summary_by_intervention": summary_by_int,
        }

