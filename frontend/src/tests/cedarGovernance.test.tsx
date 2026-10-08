import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { CedarGovernancePanel } from '../components/CedarGovernancePanel';

describe('Cedar Governance UI & Persona Switcher', () => {
  it('renders persona switcher and default municipal commissioner identity', async () => {
    render(
      <CedarGovernancePanel
        projectId="PROJ-PUNE-2025-BA225D6A"
        lifecycleState="PROPOSED"
      />
    );

    // Verify title and badges
    expect(await screen.findByText('Amazon Cedar Governance & Policy Enforcement')).toBeInTheDocument();
    expect(screen.getByText('Server-Side Authorizer')).toBeInTheDocument();

    // Verify default personas rendered
    expect(screen.getAllByText(/Dr. Rajesh Patil/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Pooja Deshmukh/i)).toBeInTheDocument();
    expect(screen.getByText(/Sharma Agro & Forestry Ltd/i)).toBeInTheDocument();
    expect(screen.getByText(/SGS Environmental Auditing/i)).toBeInTheDocument();
    expect(screen.getByText(/Ananya Joshi/i)).toBeInTheDocument();

    // Verify active policy rules card rendered
    expect(screen.getByText('@id("policy_universal_view")')).toBeInTheDocument();
    expect(screen.getByText('@id("policy_pm_propose_revision")')).toBeInTheDocument();
    expect(screen.getByText('@id("policy_officer_approve_project")')).toBeInTheDocument();
    expect(screen.getByText('@id("policy_contractor_record_impl")')).toBeInTheDocument();
    expect(screen.getByText('@id("policy_mrv_verify_impact")')).toBeInTheDocument();
    expect(screen.getByText('@id("policy_forbid_canonical_mutation")')).toBeInTheDocument();
  });

  it('allows switching active persona to Field Contractor', async () => {
    render(
      <CedarGovernancePanel
        projectId="PROJ-PUNE-2025-BA225D6A"
        lifecycleState="PROPOSED"
      />
    );

    const contractorBtn = await screen.findByText(/Sharma Agro & Forestry Ltd/i);
    fireEvent.click(contractorBtn);

    // Verify active persona role and description updated
    expect(screen.getByText(/Role::"field_contractor"/i)).toBeInTheDocument();
    expect(screen.getByText(/Responsible for ground sapling procurement/i)).toBeInTheDocument();
  });
});
