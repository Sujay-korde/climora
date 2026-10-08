import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { CellInspector } from '../components/CellInspector';
import { SelectionSummaryCard } from '../components/SelectionSummaryCard';
import { AllocationItem, BaselineCell } from '../types/api';

describe('Data Honesty & Anti-Placeholder Enforcement', () => {
  const canonicalCell: BaselineCell = {
    h3_cell_id: '89608850003ffff',
    ward_id: 'PMC_DECOUPLED',
    metrics: {
      lst_2025: { value: 46.27, unit: 'degC', truth_layer: 'OBSERVED' },
      lst_baseline_mean: { value: 45.96, unit: 'degC', truth_layer: 'DERIVED' },
      lst_anomaly_absolute: { value: 0.31, unit: 'degC', truth_layer: 'DERIVED' },
      lst_persistence: { value: 0.8, unit: 'fraction', truth_layer: 'DERIVED' },
      lst_recurrence_ge45: { value: 4.0, unit: 'years_count', truth_layer: 'DERIVED' },
      ndvi_2025: { value: 0.3303, unit: 'index', truth_layer: 'OBSERVED' },
      ndbi_2025: { value: -0.0363, unit: 'index', truth_layer: 'OBSERVED' },
      population_2020: { value: 4756.94, unit: 'persons', truth_layer: 'OBSERVED' },
      population_density_2020: { value: 48221.4, unit: 'persons_per_km2', truth_layer: 'DERIVED' },
      road_length_m: { value: 577.25, unit: 'meters', truth_layer: 'OBSERVED' },
      H_i: { value: 0.6241, unit: 'score', truth_layer: 'MODELED' },
      E_i: { value: 0.9178, unit: 'score', truth_layer: 'MODELED' },
      V_i: { value: 0.4089, unit: 'score', truth_layer: 'MODELED' },
      risk_i: { value: 0.2345, unit: 'score', truth_layer: 'MODELED' },
      lisa_quadrant: { value: 'High-High', unit: 'category', truth_layer: 'DERIVED' },
      local_moran_i: { value: 0.7814, unit: 'statistic', truth_layer: 'DERIVED' },
      lisa_cluster: { value: 'High-High Priority Hotspot', unit: 'category', truth_layer: 'DERIVED' },
    },
  };

  const canonicalAllocation: AllocationItem = {
    h3_cell_id: '89608850003ffff',
    intervention_type: 'street_tree_shade',
    activation: 1,
    planned_quantity: 76.0,
    unit: 'tree_count',
    unit_cost: 3500.0,
    mobilization_fixed_cost: 20000.0,
    total_modeled_cost: 286000.0,
    modeled_cooling_degC: 0.0543,
    modeled_risk_reduction: 0.0031,
    baseline_cell_risk: 0.2345,
    population_in_cell: 4756.94,
    truth_layer: 'MODELED',
    optimization_run_id: 'OPT-PUNE-2025-SCENARIO-BA225D6A',
  };

  it('renders canonical API values and guarantees illustrative wireframe placeholders are absent', () => {
    render(
      <CellInspector
        cellId="89608850003ffff"
        allocation={canonicalAllocation}
        baseline={canonicalCell}
        isOpen={true}
        onClose={vi.fn()}
        onOpenProvenance={vi.fn()}
      />
    );

    // Verify canonical API values are displayed
    expect(screen.getByText('46.27°C')).toBeInTheDocument();
    expect(screen.getByText('76 street trees')).toBeInTheDocument();
    expect(screen.getByText('₹286,000')).toBeInTheDocument();
    expect(screen.getByText('4,757 residents')).toBeInTheDocument();

    // Verify illustrative wireframe numbers are explicitly absent
    expect(screen.queryByText('46.69°C')).not.toBeInTheDocument();
    expect(screen.queryByText('110 street trees')).not.toBeInTheDocument();
    expect(screen.queryByText('₹405,000')).not.toBeInTheDocument();
    expect(screen.queryByText('4,281 residents')).not.toBeInTheDocument();
  });

  it('SelectionSummaryCard displays canonical values dynamically without hardcoded constants', () => {
    render(
      <SelectionSummaryCard
        cellId="89608850003ffff"
        allocation={canonicalAllocation}
        baseline={canonicalCell}
        onOpenInspector={vi.fn()}
        onClose={vi.fn()}
      />
    );

    expect(screen.getByText('46.27°C')).toBeInTheDocument();
    expect(screen.getByText('76 trees · ₹286,000')).toBeInTheDocument();
    expect(screen.queryByText('110 trees')).not.toBeInTheDocument();
    expect(screen.queryByText('₹405,000')).not.toBeInTheDocument();
  });
});
