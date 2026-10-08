import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { ProjectPage } from '../pages/ProjectPage';
import { getCurrentActor, setCurrentActor } from '../services/api';

vi.mock('../services/api', async () => {
  const actual = await vi.importActual<any>('../services/api');
  let mockActorId = 'pmc_commissioner';
  const listeners = new Set<(id: string) => void>();

  return {
    ...actual,
    getCurrentActor: () => mockActorId,
    setCurrentActor: (newId: string) => {
      mockActorId = newId;
      listeners.forEach((fn) => fn(newId));
    },
    onActorChange: (fn: (id: string) => void) => {
      listeners.add(fn);
      return () => listeners.delete(fn);
    },
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
        allocations: [
          {
            h3_cell_id: '89608850003ffff',
            intervention_type: 'street_tree_shade',
            planned_quantity: 80,
            unit_cost: 3500,
            mobilization_fixed_cost: 20000,
            total_modeled_cost: 300000,
            population_in_cell: 4200,
          },
        ],
        provenance: {
          source_sha256: '2519473a32a2b4a3a22bc8beb43525c3f21dc404783168f1edd6de7bc4bb5555',
        },
      }),
      getBaseline: vi.fn().mockResolvedValue({
        cells: [
          {
            h3_cell_id: '89608850003ffff',
            metrics: {
              lst_2025: { value: 46.5 },
              lst_baseline_mean: { value: 41.2 },
              lst_anomaly_absolute: { value: 5.3 },
              ndvi_2025: { value: 0.12 },
              ndbi_2025: { value: 0.35 },
              lisa_quadrant: { value: 'High-High' },
            },
          },
        ],
      }),
    },
  };
});

describe('Phase 2D.1: Perspective Selector & Authorization Decoupling', () => {
  it('renders all 5 perspective lenses and explicit Demo Governance Persona indicator', async () => {
    render(
      <MemoryRouter initialEntries={['/projects/PROJ-PUNE-2025-BA225D6A']}>
        <Routes>
          <Route path="/projects/:id" element={<ProjectPage />} />
        </Routes>
      </MemoryRouter>
    );

    // Verify explicit Demo Governance Persona banner
    expect(await screen.findByText('DEMO GOVERNANCE PERSONA')).toBeInTheDocument();
    expect(screen.getByText(/Simulated actor for server-side Cedar evaluation/i)).toBeInTheDocument();

    // Verify 5 Perspective Lenses in selector
    expect(screen.getByRole('tab', { name: /Civic Transparency/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /Urban Planning/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /Municipal Sanction/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /Field Delivery/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /Independent MRV/i })).toBeInTheDocument();
  });

  it('proves Option A: changing perspective lens updates presentation without altering the active demo persona', async () => {
    setCurrentActor('pmc_commissioner');

    render(
      <MemoryRouter initialEntries={['/projects/PROJ-PUNE-2025-BA225D6A']}>
        <Routes>
          <Route path="/projects/:id" element={<ProjectPage />} />
        </Routes>
      </MemoryRouter>
    );

    expect(await screen.findByText('PROJ-PUNE-2025-BA225D6A')).toBeInTheDocument();

    // Initial actor is pmc_commissioner
    expect(getCurrentActor()).toBe('pmc_commissioner');

    // Click Civic Transparency lens
    const civicTab = screen.getByRole('tab', { name: /Civic Transparency/i });
    fireEvent.click(civicTab);

    // CRITICAL SECURITY INVARIANT: Perspective lens change did NOT mutate active actor!
    expect(getCurrentActor()).toBe('pmc_commissioner');

    // Click Urban Planning lens
    const planningTab = screen.getByRole('tab', { name: /Urban Planning/i });
    fireEvent.click(planningTab);

    // Still unchanged
    expect(getCurrentActor()).toBe('pmc_commissioner');
  });

  it('switches active demo persona explicitly via the Demo Actor selector', async () => {
    setCurrentActor('pmc_commissioner');

    render(
      <MemoryRouter initialEntries={['/projects/PROJ-PUNE-2025-BA225D6A']}>
        <Routes>
          <Route path="/projects/:id" element={<ProjectPage />} />
        </Routes>
      </MemoryRouter>
    );

    await screen.findByText('PROJ-PUNE-2025-BA225D6A');

    const select = screen.getByLabelText(/Active Actor:/i);
    fireEvent.change(select, { target: { value: 'citizen_viewer' } });

    // Explicit actor change updates the active principal for X-Climora-Actor
    expect(getCurrentActor()).toBe('citizen_viewer');
  });

  it('displays Civic Transparency mode de-emphasizing mutation actions and prioritizing public facts', async () => {
    render(
      <MemoryRouter initialEntries={['/projects/PROJ-PUNE-2025-BA225D6A']}>
        <Routes>
          <Route path="/projects/:id" element={<ProjectPage />} />
        </Routes>
      </MemoryRouter>
    );

    await screen.findByText('PROJ-PUNE-2025-BA225D6A');

    // Switch to Civic Transparency lens
    const civicLensBtn = screen.getByRole('tab', { name: /Civic Transparency/i });
    fireEvent.click(civicLensBtn);

    // Verify civic title and status
    expect(screen.getByText('Civic Transparency & Sanction Status')).toBeInTheDocument();
    expect(screen.getByText('Public Citizen View')).toBeInTheDocument();

    // Confirm that the direct tender sanction button is absent in civic view
    expect(screen.queryByText('Sanction project & issue tender')).not.toBeInTheDocument();
  });

  it('displays Municipal Sanction mode emphasizing statutory sanction controls', async () => {
    render(
      <MemoryRouter initialEntries={['/projects/PROJ-PUNE-2025-BA225D6A']}>
        <Routes>
          <Route path="/projects/:id" element={<ProjectPage />} />
        </Routes>
      </MemoryRouter>
    );

    await screen.findByText('PROJ-PUNE-2025-BA225D6A');

    // Switch to Municipal Sanction lens
    const sanctionLensBtn = screen.getByRole('tab', { name: /Municipal Sanction/i });
    fireEvent.click(sanctionLensBtn);

    // Verify municipal sanction button is prominent
    expect(screen.getByText('Sanction project & issue tender')).toBeInTheDocument();
    expect(screen.getByText(/Sanction authority reserved/i)).toBeInTheDocument();
  });

  it('renders the Green Finance Readiness & Capital Diligence case in the Budget tab', async () => {
    render(
      <MemoryRouter initialEntries={['/projects/PROJ-PUNE-2025-BA225D6A']}>
        <Routes>
          <Route path="/projects/:id" element={<ProjectPage />} />
        </Routes>
      </MemoryRouter>
    );

    await screen.findByText('PROJ-PUNE-2025-BA225D6A');

    // Navigate to Budget & Finance Readiness tab
    const budgetTabBtn = screen.getByRole('button', { name: /Budget & Finance Readiness/i });
    fireEvent.click(budgetTabBtn);

    // Verify Bankable Asset diligence case
    expect(screen.getByText('Green Finance Readiness & Capital Diligence Case')).toBeInTheDocument();
    expect(screen.getByText('Bankable Asset')).toBeInTheDocument();
    expect(screen.getByText('ISO 14064-2 Protocol')).toBeInTheDocument();
    expect(screen.getByText(/CLIMORA operates as a civic decision and governance instrument/i)).toBeInTheDocument();
  });
});
