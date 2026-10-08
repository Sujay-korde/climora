import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { AccessibleTable } from '../components/AccessibleTable';
import { BaselineCell, AllocationItem } from '../types/api';

describe('Accessibility & Alt+T Semantic Fallback', () => {
  const mockCells: BaselineCell[] = [
    {
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
    },
  ];

  const mockAllocations: AllocationItem[] = [
    {
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
    },
  ];

  it('renders semantic table with proper caption and column headers for screen readers', () => {
    render(
      <AccessibleTable
        cells={mockCells}
        allocations={mockAllocations}
        selectedCellId={null}
        onSelectCell={vi.fn()}
        onReturnToMap={vi.fn()}
      />
    );

    expect(screen.getByRole('table')).toBeInTheDocument();
    expect(screen.getByText(/Authoritative municipal decision dataset/i)).toBeInTheDocument();

    const columnHeaders = screen.getAllByRole('columnheader');
    expect(columnHeaders.length).toBeGreaterThan(5);

    const rowHeaders = screen.getAllByRole('rowheader');
    expect(rowHeaders[0]).toHaveTextContent('89608850003ffff');
  });

  it('allows keyboard action to return to map view', () => {
    const handleReturn = vi.fn();
    render(
      <AccessibleTable
        cells={mockCells}
        allocations={mockAllocations}
        selectedCellId={null}
        onSelectCell={vi.fn()}
        onReturnToMap={handleReturn}
      />
    );

    const returnBtn = screen.getByText(/Return to Spatial Map View/i);
    fireEvent.click(returnBtn);
    expect(handleReturn).toHaveBeenCalledTimes(1);
  });
});
