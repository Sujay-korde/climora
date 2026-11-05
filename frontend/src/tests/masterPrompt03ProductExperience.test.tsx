import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { InterventionsPage } from '../pages/InterventionsPage';
import { MRVImpactPage } from '../pages/MRVImpactPage';
import { MethodologyPage } from '../pages/MethodologyPage';
import { ProjectBriefModal } from '../components/ProjectBriefModal';

describe('MASTER PROMPT 03 — Product Experience & Judge Readiness Suite', () => {
  it('InterventionsPage renders all 5 ratified interventions with physical units and costs', () => {
    render(
      <MemoryRouter>
        <InterventionsPage />
      </MemoryRouter>
    );

    // Title and catalog
    expect(screen.getByText('Ratified Adaptation Intervention Library')).toBeInTheDocument();
    expect(screen.getAllByText('Urban Street Tree Canopy Planting').length).toBeGreaterThan(0);
    expect(screen.getByText('High-Albedo Cool Roof Coating')).toBeInTheDocument();
    expect(screen.getByText('Vegetative Micro-Corridor / Bioretention')).toBeInTheDocument();
    expect(screen.getByText('Permeable Interlocking Concrete Pavement')).toBeInTheDocument();
    expect(screen.getByText('Bioswale Infiltration Trench')).toBeInTheDocument();

    // Mathematical hard constraint disclosure
    expect(screen.getByText(/Ground-Surface Spatial Exclusivity/i)).toBeInTheDocument();

    // Interactive selection
    fireEvent.click(screen.getByText('High-Albedo Cool Roof Coating'));
    expect(screen.getByText(/0.40 \* norm_ndbi \* cell_area_m2/i)).toBeInTheDocument();
  });

  it('MRVImpactPage renders tripartite states, detectability limits, and Landsat noise floor notice', () => {
    render(
      <MemoryRouter>
        <MRVImpactPage />
      </MemoryRouter>
    );

    expect(screen.getByText('MRV, Empirical Impact & Verification Architecture')).toBeInTheDocument();

    // Tripartite States
    expect(screen.getAllByText('PREDICTED').length).toBeGreaterThan(0);
    expect(screen.getAllByText('OBSERVED').length).toBeGreaterThan(0);
    expect(screen.getAllByText('VERIFIED').length).toBeGreaterThan(0);

    // Landsat noise floor and detectability
    expect(screen.getByText(/Landsat Thermal Sensor Noise Floor/i)).toBeInTheDocument();
    expect(screen.getAllByText(/~6.91°C/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/~0.07°C/i).length).toBeGreaterThan(0);

    // Econometric Difference-in-Differences status
    expect(screen.getByText(/STATUS: PLANNED \/ NOT_YET_EXECUTABLE/i)).toBeInTheDocument();
  });

  it('MethodologyPage renders all 4 foundational datasets and IPCC risk equations', () => {
    render(
      <MemoryRouter>
        <MethodologyPage />
      </MemoryRouter>
    );

    expect(screen.getByText('Data Provenance & Scientific Methodology')).toBeInTheDocument();

    // Datasets
    expect(screen.getByText('Landsat 8 & 9 TIRS')).toBeInTheDocument();
    expect(screen.getByText('Sentinel-2 MSI (Level-2A)')).toBeInTheDocument();
    expect(screen.getByText('WorldPop UN-adjusted 2020')).toBeInTheDocument();
    expect(screen.getByText('OpenStreetMap (OSM) Vector')).toBeInTheDocument();

    // IPCC Risk Formulation
    expect(screen.getByText(/2\. IPCC AR5 \/ AR6 Risk Formulation/i)).toBeInTheDocument();
    expect(screen.getByText(/Risk_i = H_i · E_i · V_i/i)).toBeInTheDocument();

    // Honest boundaries
    expect(screen.getByText(/What CLIMORA Defensibly Achieves/i)).toBeInTheDocument();
    expect(screen.getByText(/What CLIMORA Does Not Claim/i)).toBeInTheDocument();
  });

  it('ProjectBriefModal renders 13-section formal brief with verified numbers and sign-off lines', () => {
    const mockScenario = {
      scenario_id: 'SCEN-TEST-10M',
      project_id: 'PROJ-TEST',
      truth_layer: 'MODELED' as const,
      is_canonical: true,
      is_precomputed_benchmark: true,
      disclaimer: 'TEST',
      generated_at_utc: '2026-10-06T09:00:00Z',
      formulation_ratified: 'F-24.6',
      solver_engine: 'HiGHS (scipy.optimize.milp)',
      budget_inr: 10000000.0,
      total_allocated_cost_inr: 9992500.0,
      budget_slack_inr: 7500.0,
      budget_utilization_pct: 99.92,
      optimal_objective_value: 0.106048,
      objective_description: 'Cumulative Risk Reduction',
      solver_status: 'OPTIMAL',
      solver_duration_sec: 49.28,
      total_cells_treated: 28,
      allocations: [],
      summary_by_intervention: {
        street_tree_shade: {
          total_quantity: 2695,
          unit: 'tree_count',
          total_cost_inr: 9992500.0,
          cells_count: 28,
        },
      },
      multi_objective_metrics: {
        modeled_risk_reduction: 0.106048,
        population_protected: 118941,
        disadvantaged_equity_cells_count: 28,
        budget_slack_inr: 7500.0,
        budget_utilization_pct: 99.92,
      },
    };

    const handleClose = vi.fn();

    render(
      <ProjectBriefModal scenario={mockScenario} onClose={handleClose} />
    );

    expect(screen.getByText('Bankable Adaptation Project Brief')).toBeInTheDocument();
    expect(screen.getAllByText(/99,92,500/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/7,500/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText('2,695').length).toBeGreaterThan(0);
    expect(screen.getByText(/Dr. Rajesh Patil, IAS/i)).toBeInTheDocument();
    expect(screen.getByText(/CSR Climate Adaptation Lead/i)).toBeInTheDocument();
  });
});
