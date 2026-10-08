/**
 * CLIMORA Frontend API Types
 * Strictly aligned with Phase 2A and Phase 2B frozen backend contracts.
 */

export type TruthLayer = 'OBSERVED' | 'DERIVED' | 'MODELED' | 'VERIFIED' | 'NOT_YET_VERIFIED';

export type ProjectLifecycleState =
  | 'PROPOSED'
  | 'FUNDED'
  | 'IMPLEMENTING'
  | 'IMPLEMENTED'
  | 'MONITORING'
  | 'VERIFIED';

export interface ProjectSummary {
  project_id: string;
  project_name: string;
  project_status: ProjectLifecycleState;
  optimization_run_id: string;
  geographic_scope: {
    study_area: string;
    spatial_grid_type: string;
    h3_resolution: number;
    total_treated_cells_count: number;
    administrative_ward_dependency: string;
  };
  intervention_summary: {
    intervention_types: string[];
    total_physical_units: number;
    quantity_unit: string;
  };
  modeled_cost: number;
  budget: number;
  remaining_budget: number;
  population_in_scope: {
    canonical_exact: number;
    display_rounded: number;
  };
  modeled_risk_reduction_achieved: number;
  truth_layer: string;
}

export interface AllocationItem {
  h3_cell_id: string;
  intervention_type: string;
  activation: number;
  planned_quantity: number;
  unit: string;
  unit_cost: number;
  mobilization_fixed_cost: number;
  total_modeled_cost: number;
  modeled_cooling_degC: number;
  modeled_risk_reduction: number;
  baseline_cell_risk: number;
  population_in_cell: number;
  truth_layer: TruthLayer;
  optimization_run_id: string;
}

export interface PortfolioSummary {
  intervention_type: string;
  total_planned_quantity: number;
  quantity_unit: string;
  direct_cost_inr: number;
  mobilization_cost_inr: number;
  total_modeled_cost_inr: number;
  scenario_budget_envelope_inr: number;
  budget_slack_unallocated_inr: number;
  optimal_aggregate_risk_reduction: number;
  total_population_protected: {
    canonical_exact: number;
    display_rounded: number;
  };
  truth_layer: TruthLayer;
}

export interface AllocationResponse {
  status: string;
  data: {
    project_id: string;
    optimization_run_id: string;
    h3_resolution: number;
    total_selected_cells: number;
    portfolio_summary: PortfolioSummary;
    allocations: AllocationItem[];
    pagination: {
      page: number;
      page_size: number;
      total_items: number;
      total_pages: number;
      has_next: boolean;
      has_prev: boolean;
    };
    provenance: {
      source_artifact: string;
      source_sha256: string;
      formulation_version: string;
      is_immutable: boolean;
    };
  };
}

export interface MetricValue {
  value: number;
  unit: string;
  truth_layer: TruthLayer;
}

export interface BaselineCell {
  h3_cell_id: string;
  ward_id: string;
  metrics: {
    lst_2025: MetricValue;
    lst_baseline_mean: MetricValue;
    lst_anomaly_absolute: MetricValue;
    lst_persistence: MetricValue;
    lst_recurrence_ge45: MetricValue;
    ndvi_2025: MetricValue;
    ndbi_2025: MetricValue;
    population_2020: MetricValue;
    population_density_2020: MetricValue;
    road_length_m: MetricValue;
    H_i: MetricValue;
    E_i: MetricValue;
    V_i: MetricValue;
    risk_i: MetricValue;
    lisa_quadrant: { value: string; unit: string; truth_layer: TruthLayer };
    local_moran_i: { value: number | null; unit: string; truth_layer: TruthLayer };
    lisa_cluster: { value: string; unit: string; truth_layer: TruthLayer };
  };
}

export interface BaselineResponse {
  status: string;
  data: {
    project_id: string;
    h3_resolution: number;
    total_selected_cells: number;
    portfolio_summary: Record<string, any>;
    cells: BaselineCell[];
    pagination: {
      page: number;
      page_size: number;
      total_items: number;
      total_pages: number;
      has_next: boolean;
      has_prev: boolean;
    };
    provenance: {
      feature_matrix_artifact: string;
      feature_matrix_sha256: string;
      hev_components_artifact: string;
      hev_components_sha256: string;
      risk_surface_artifact: string;
      risk_surface_sha256: string;
      spatial_autocorrelation_artifact: string;
      spatial_autocorrelation_sha256: string;
      spatial_framework: string;
      raw_rasters_exposed: boolean;
    };
  };
}

export interface MRVOverviewResponse {
  status: string;
  data: {
    project_id: string;
    current_lifecycle_state: ProjectLifecycleState;
    implementation_events_count: number;
    implementation_events: Array<{
      event_id: string;
      h3_cell_id: string;
      intervention_code: string;
      planned_quantity: number;
      implemented_quantity: number;
      deviation: number;
      deviation_rate: number;
      quantity_unit: string;
      contractor_id: string;
      completion_date: string;
      evidence_uri: string;
    }>;
    observation_events_count: number;
    observation_events: any[];
    qc_state: string;
    verification_state: string;
    verification_events_count: number;
    verification_events: any[];
    verified_impact: null;
    difference_in_differences_status: {
      current_operational_status: string;
      is_executable: boolean;
      rationale: string;
    };
    truth_layer: string;
  };
}

export interface GovernanceActor {
  actor_id: string;
  name: string;
  role: string;
  title: string;
  organization: string;
  description: string;
}

export interface GovernanceAuditRecord {
  audit_id: string;
  decision: 'ALLOW' | 'DENY';
  actor_id: string;
  actor_name: string;
  role: string;
  action: string;
  project_id: string;
  project_state: string;
  policy_id?: string;
  reason_summary: string;
  timestamp_utc: string;
}

export interface GovernanceCheckResult {
  allowed: boolean;
  decision: 'ALLOW' | 'DENY';
  actor_id: string;
  actor_name: string;
  role: string;
  action: string;
  project_id: string;
  project_state: string;
  policy_id?: string;
  reason_summary: string;
  audit_id: string;
  timestamp_utc: string;
}

export interface RiskSurfaceCell {
  h3_cell_id: string;
  risk_i: number;
  H_i: number;
  E_i: number;
  V_i: number;
  lst_2025: number;
  lst_anomaly: number;
  population_2020: number;
  lisa_cluster: string;
  is_eligible: boolean;
}

export interface RiskSurfaceResponse {
  status: string;
  data: {
    project_id: string;
    truth_layer: TruthLayer;
    total_cells: number;
    eligible_cells: number;
    cells: RiskSurfaceCell[];
  };
}

export interface ScenarioAllocationItem {
  h3_cell_id: string;
  intervention_type: string;
  quantity: number;
  unit: string;
  unit_cost: number;
  fixed_cost: number;
  total_cost: number;
  modeled_cooling_degC: number;
  marginal_risk_reduction: number;
  baseline_risk: number;
  population_2020: number;
}

export interface ScenarioOptimizeResponse {
  status: string;
  data: {
    scenario_id: string;
    project_id: string;
    truth_layer: TruthLayer;
    is_canonical: boolean;
    is_precomputed_benchmark?: boolean;
    disclaimer: string;
    generated_at_utc: string;
    formulation_ratified: string;
    solver_engine: string;
    budget_inr: number;
    total_allocated_cost_inr: number;
    budget_slack_inr: number;
    budget_utilization_pct: number;
    optimal_objective_value: number;
    objective_description: string;
    solver_status: string;
    solver_duration_sec: number;
    total_cells_treated: number;
    allocations: ScenarioAllocationItem[];
    summary_by_intervention: Record<string, {
      total_quantity: number;
      unit: string;
      total_cost_inr: number;
      cells_count: number;
    }>;
  };
}


