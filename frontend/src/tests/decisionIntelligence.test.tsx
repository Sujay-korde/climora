import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ScenarioControlCard } from '../components/ScenarioControlCard';
import { CellInspector } from '../components/CellInspector';
import { RiskSurfaceCell, ScenarioAllocationItem } from '../types/api';


describe('Phase 2E.1: Decision Intelligence & Scenario Optimization Controls', () => {
  const mockScenarioResult = {
    scenario_id: 'SCEN-PUNE-2025-5M-BENCHMARK',
    project_id: 'PROJ-PUNE-2025-BA225D6A',
    truth_layer: 'MODELED' as const,
    is_canonical: false,
    is_precomputed_benchmark: true,
    disclaimer: 'MODELED SCENARIO ONLY',
    generated_at_utc: '2026-10-06T06:00:00Z',
    formulation_ratified: 'F-24.6',
    solver_engine: 'HiGHS (scipy.optimize.milp)',
    budget_inr: 5000000.0,
    total_allocated_cost_inr: 4950500.0,
    budget_slack_inr: 49500.0,
    budget_utilization_pct: 99.01,
    optimal_objective_value: 0.055865,
    objective_description: 'Modeled optimization objective',
    solver_status: 'OPTIMAL',
    solver_duration_sec: 57.23,
    total_cells_treated: 16,
    allocations: [
      {
        h3_cell_id: '8960145a4a7ffff',
        intervention_type: 'street_tree_shade',
        quantity: 82.0,
        unit: 'tree_count',
        unit_cost: 3500.0,
        fixed_cost: 20000.0,
        total_cost: 307000.0,
        modeled_cooling_degC: 0.0586,
        marginal_risk_reduction: 0.00346,
        baseline_risk: 0.321,
        population_2020: 4120.0,
      },
    ],
    summary_by_intervention: {
      street_tree_shade: {
        total_quantity: 1323.0,
        unit: 'tree_count',
        total_cost_inr: 4950500.0,
        cells_count: 16,
      },
    },
  };

  it('renders all 4 budget presets and clicking a preset triggers scenario execution', () => {
    const handleBudgetChange = vi.fn();
    const handleRunScenario = vi.fn();

    render(
      <ScenarioControlCard
        currentBudget={5000000}
        onBudgetChange={handleBudgetChange}
        onRunScenario={handleRunScenario}
        isOptimizing={false}
        scenarioResult={null}
        onClearScenario={vi.fn()}
        error={null}
        showScenarioOverlay={true}
        onToggleScenarioOverlay={vi.fn()}
      />
    );

    // Verify all 4 preset buttons exist
    expect(screen.getByText('₹2.5M')).toBeInTheDocument();
    expect(screen.getByText('₹5.0M')).toBeInTheDocument();
    expect(screen.getByText('₹7.5M')).toBeInTheDocument();
    expect(screen.getByText('₹10.0M')).toBeInTheDocument();

    // Click ₹2.5M preset
    fireEvent.click(screen.getByText('₹2.5M'));
    expect(handleBudgetChange).toHaveBeenCalledWith(2500000);
    expect(handleRunScenario).toHaveBeenCalledWith(2500000);
  });

  it('displays optimization loading state when solver is executing', () => {
    render(
      <ScenarioControlCard
        currentBudget={5000000}
        onBudgetChange={vi.fn()}
        onRunScenario={vi.fn()}
        isOptimizing={true}
        scenarioResult={null}
        onClearScenario={vi.fn()}
        error={null}
        showScenarioOverlay={true}
        onToggleScenarioOverlay={vi.fn()}
      />
    );

    expect(screen.getByText(/Optimizing with HiGHS MILP \(SciPy\)\.\.\./)).toBeInTheDocument();
  });

  it('displays modeled scenario output metrics accurately when solved', () => {
    const handleClear = vi.fn();

    render(
      <ScenarioControlCard
        currentBudget={5000000}
        onBudgetChange={vi.fn()}
        onRunScenario={vi.fn()}
        isOptimizing={false}
        scenarioResult={mockScenarioResult}
        onClearScenario={handleClear}
        error={null}
        showScenarioOverlay={true}
        onToggleScenarioOverlay={vi.fn()}
      />
    );

    expect(screen.getByText('Modeled Scenario Result')).toBeInTheDocument();
    expect(screen.getByText('OPTIMAL')).toBeInTheDocument();
    expect(screen.getByText('₹4,950,500')).toBeInTheDocument();
    expect(screen.getByText('16 H3 cells')).toBeInTheDocument();
    expect(screen.getByText('1,323 trees')).toBeInTheDocument();
    expect(screen.getByText('0.0559')).toBeInTheDocument();

    // Clear scenario
    fireEvent.click(screen.getByText('Clear'));
    expect(handleClear).toHaveBeenCalled();
  });

  it('renders CellInspector with full risk surface and scenario evidence', () => {
    const mockRiskCell: RiskSurfaceCell = {
      h3_cell_id: '8960145a4a7ffff',
      risk_i: 0.3214,
      H_i: 0.582,
      E_i: 0.741,
      V_i: 0.912,
      lst_2025: 47.2,
      lst_anomaly: 1.45,
      population_2020: 4120.0,
      lisa_cluster: 'High-High Priority Hotspot',
      is_eligible: true,
    };

    const mockScenarioAlloc: ScenarioAllocationItem = {
      h3_cell_id: '8960145a4a7ffff',
      intervention_type: 'street_tree_shade',
      quantity: 82.0,
      unit: 'tree_count',
      unit_cost: 3500.0,
      fixed_cost: 20000.0,
      total_cost: 307000.0,
      modeled_cooling_degC: 0.0586,
      marginal_risk_reduction: 0.00346,
      baseline_risk: 0.3214,
      population_2020: 4120.0,
    };

    render(
      <CellInspector
        cellId="8960145a4a7ffff"
        riskCell={mockRiskCell}
        scenarioAllocation={mockScenarioAlloc}
        isOpen={true}
        onClose={vi.fn()}
        onOpenProvenance={vi.fn()}
      />
    );

    // Verify decision metrics
    expect(screen.getByText('47.2°C')).toBeInTheDocument();
    expect(screen.getByText('0.3214')).toBeInTheDocument();

    // Verify HEV component decomposition
    expect(screen.getByText('0.582')).toBeInTheDocument();
    expect(screen.getByText('0.741')).toBeInTheDocument();
    expect(screen.getByText('0.912')).toBeInTheDocument();

    // Verify scenario allocation card
    expect(screen.getByText('Active Scenario Allocation')).toBeInTheDocument();
    expect(screen.getByText('82 street trees')).toBeInTheDocument();
    expect(screen.getByText('Scenario cost: ₹307,000')).toBeInTheDocument();
    expect(screen.getByText('High-High Priority Hotspot')).toBeInTheDocument();
  });
});
