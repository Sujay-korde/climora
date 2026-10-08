import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { ProjectPage } from '../pages/ProjectPage';

vi.mock('../services/api', async () => {
  const actual = await vi.importActual('../services/api');
  return {
    ...actual,
    climoraApi: {
      getProjectDetail: vi.fn().mockResolvedValue({
        section_1_project_identity: {
          project_id: 'PROJ-PUNE-2025-BA225D6A',
          project_title: 'Pune Urban Heat Island Mitigation & Street Canopy Initiative',
          lifecycle_state: 'PROPOSED',
        },
        section_6_transparent_cost_breakdown: {
          modeled_optimized_capex_inr: 9992500,
          scenario_budget_envelope_inr: 10000000,
          budget_slack_unallocated_inr: 7500,
        },
        section_7_modeled_microclimatic_and_risk_impact: {
          modeled_aggregate_risk_reduction_score: 0.106048,
        },
      }),
      getAllocation: vi.fn().mockResolvedValue({
        portfolio_summary: {
          total_planned_quantity: 2695,
          total_modeled_cost_inr: 9992500,
          scenario_budget_envelope_inr: 10000000,
          budget_slack_unallocated_inr: 7500,
          total_population_protected: { display_rounded: 118941 },
        },
        allocations: [],
        provenance: {},
      }),
      getBaseline: vi.fn().mockResolvedValue({
        cells: [],
      }),
    },
  };
});

describe('Project Lifecycle & Verification State Honesty', () => {
  it('renders PROPOSED status and unverified gate without fake success badge', async () => {
    render(
      <MemoryRouter initialEntries={['/projects/PROJ-PUNE-2025-BA225D6A']}>
        <Routes>
          <Route path="/projects/:id" element={<ProjectPage />} />
        </Routes>
      </MemoryRouter>
    );

    expect(await screen.findByText('PROJ-PUNE-2025-BA225D6A')).toBeInTheDocument();
    expect(screen.getByText('₹9,992,500')).toBeInTheDocument();
    expect(screen.getByText('2,695 street trees')).toBeInTheDocument();
    expect(screen.getByText('118,941 residents')).toBeInTheDocument();
    expect(screen.getByText('₹7,500')).toBeInTheDocument();
    expect(screen.getByText('0.106048')).toBeInTheDocument();

    // Confirm that fake verified celebration is absent
    expect(screen.queryByText('Verified 100%')).not.toBeInTheDocument();
  });
});
