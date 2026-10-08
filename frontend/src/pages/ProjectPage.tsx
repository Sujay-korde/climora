import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { TruthBadge } from '../components/TruthBadge';
import { StateTransitionModal } from '../components/StateTransitionModal';
import { RevisionModal } from '../components/RevisionModal';
import { ProvenanceModal } from '../components/ProvenanceModal';
import { CedarGovernancePanel } from '../components/CedarGovernancePanel';
import { CANONICAL_PROJECT_ID, climoraApi, getCurrentActor, onActorChange, setCurrentActor } from '../services/api';
import {
  AllocationItem,
  BaselineCell,
  PortfolioSummary,
  ProjectLifecycleState,
} from '../types/api';

export type TabKey = 'overview' | 'governance' | 'allocation' | 'baseline' | 'budget' | 'verification' | 'provenance';

export type PerspectiveLens = 'civic' | 'planning' | 'sanction' | 'delivery' | 'mrv';

export interface PerspectiveDefinition {
  id: PerspectiveLens;
  name: string;
  tagline: string;
  suggestedPersonaId: string;
  suggestedPersonaName: string;
  suggestedRoleTitle: string;
  defaultTab: TabKey;
}

export const PERSPECTIVES: PerspectiveDefinition[] = [
  {
    id: 'civic',
    name: 'Civic Transparency',
    tagline: 'Public accountability, open spatial canopy allocations & verified cooling audit',
    suggestedPersonaId: 'citizen_viewer',
    suggestedPersonaName: 'Ananya Joshi',
    suggestedRoleTitle: 'Public Citizen Observer',
    defaultTab: 'overview',
  },
  {
    id: 'planning',
    name: 'Urban Planning',
    tagline: 'Spatial evidence, H3 cell prioritization & allocation branch revisions',
    suggestedPersonaId: 'urban_planner_lead',
    suggestedPersonaName: 'Pooja Deshmukh',
    suggestedRoleTitle: 'Lead Urban Climate Planner (PMC)',
    defaultTab: 'allocation',
  },
  {
    id: 'sanction',
    name: 'Municipal Sanction',
    tagline: 'Standing Committee capital budget sanction & statutory tender authorization',
    suggestedPersonaId: 'pmc_commissioner',
    suggestedPersonaName: 'Dr. Rajesh Patil',
    suggestedRoleTitle: 'Municipal Sanctioning Authority / Commissioner (PMC)',
    defaultTab: 'overview',
  },
  {
    id: 'delivery',
    name: 'Field Delivery',
    tagline: 'Licensed EPC sapling procurement, roadside digging & batch deployment',
    suggestedPersonaId: 'sharma_contractors',
    suggestedPersonaName: 'Sharma Agro & Forestry Ltd',
    suggestedRoleTitle: 'Licensed EPC Planting Contractor',
    defaultTab: 'allocation',
  },
  {
    id: 'mrv',
    name: 'Independent MRV',
    tagline: 'ISO 14064-2 accredited audit, Landsat satellite QA & Difference-in-Differences gates',
    suggestedPersonaId: 'sgs_environmental_auditor',
    suggestedPersonaName: 'SGS Environmental Auditing',
    suggestedRoleTitle: 'Accredited GHG/MRV Verifier',
    defaultTab: 'verification',
  },
];

const DEMO_PERSONAS = [
  { id: 'pmc_commissioner', name: 'Dr. Rajesh Patil', role: 'municipal_officer', displayRole: 'Municipal Sanctioning Authority / Commissioner (PMC)' },
  { id: 'urban_planner_lead', name: 'Pooja Deshmukh', role: 'project_manager', displayRole: 'Lead Urban Climate Planner (PMC)' },
  { id: 'sharma_contractors', name: 'Sharma Agro & Forestry Ltd', role: 'field_contractor', displayRole: 'Licensed EPC Contractor (PMC Vendor Registry)' },
  { id: 'sgs_environmental_auditor', name: 'SGS Environmental Auditing', role: 'mrv_verifier', displayRole: 'Accredited MRV Verifier (ISO 14064-2)' },
  { id: 'citizen_viewer', name: 'Ananya Joshi', role: 'viewer', displayRole: 'Public Citizen Observer (Pune Civic Forum)' },
];

export const ProjectPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const projectId = id || CANONICAL_PROJECT_ID;

  // Presentation State: Perspective Lens (Presentation emphasis only; does not grant authority)
  const [selectedLens, setSelectedLens] = useState<PerspectiveLens>('sanction');

  // Authorization Principal State: Demo Governance Persona (controls X-Climora-Actor header)
  const [currentActor, setCurrentActorState] = useState<string>(getCurrentActor());

  const [activeTab, setActiveTab] = useState<TabKey>('overview');
  const [projectData, setProjectData] = useState<any>(null);
  const [portfolioSummary, setPortfolioSummary] = useState<PortfolioSummary | null>(null);
  const [allocations, setAllocations] = useState<AllocationItem[]>([]);
  const [baselineCells, setBaselineCells] = useState<BaselineCell[]>([]);
  const [provenanceData, setProvenanceData] = useState<any>(null);
  const [lifecycleState, setLifecycleState] = useState<ProjectLifecycleState>('PROPOSED');

  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Modals
  const [isSanctionModalOpen, setIsSanctionModalOpen] = useState(false);
  const [isRevisionModalOpen, setIsRevisionModalOpen] = useState(false);
  const [targetRevisionCell, setTargetRevisionCell] = useState('');
  const [isProvenanceModalOpen, setIsProvenanceModalOpen] = useState(false);

  // Sync with global actor changes from CedarGovernancePanel or elsewhere
  useEffect(() => {
    const unsub = onActorChange((actorId) => {
      setCurrentActorState(actorId);
    });
    return unsub;
  }, []);

  useEffect(() => {
    setIsLoading(true);
    setErrorMsg(null);

    Promise.all([
      climoraApi.getProjectDetail(projectId),
      climoraApi.getAllocation(projectId),
      climoraApi.getBaseline(projectId),
    ])
      .then(([proj, alloc, base]) => {
        setProjectData(proj);
        setLifecycleState(proj?.section_1_project_identity?.lifecycle_state || 'PROPOSED');
        setPortfolioSummary(alloc.portfolio_summary);
        setAllocations(alloc.allocations);
        setBaselineCells(base.cells);
        setProvenanceData(alloc.provenance);
        setIsLoading(false);
      })
      .catch((err) => {
        setErrorMsg(err.message || 'Unable to retrieve canonical project data.');
        setIsLoading(false);
      });
  }, [projectId]);

  // Option A Invariant: Switching Perspective Lens changes presentation only, NOT the active Demo Persona
  const handleLensChange = (lensId: PerspectiveLens) => {
    setSelectedLens(lensId);
    const def = PERSPECTIVES.find((p) => p.id === lensId);
    if (def) {
      setActiveTab(def.defaultTab);
    }
  };

  // Changing Demo Governance Persona explicitly modifies the simulated identity (X-Climora-Actor)
  const handleActorSelect = (actorId: string) => {
    setCurrentActorState(actorId);
    setCurrentActor(actorId);
  };

  const currentLensDef = PERSPECTIVES.find((p) => p.id === selectedLens) || PERSPECTIVES[0];
  const activePersonaObj = DEMO_PERSONAS.find((p) => p.id === currentActor) || DEMO_PERSONAS[0];
  const isPersonaAlignedWithLens = currentActor === currentLensDef.suggestedPersonaId;

  if (isLoading) {
    return (
      <div style={{ maxWidth: '1080px', margin: '48px auto', padding: '0 32px', color: 'var(--ink-secondary)', fontSize: '13px' }}>
        Loading canonical municipal decision suite...
      </div>
    );
  }

  if (errorMsg || !projectData) {
    return (
      <div style={{ maxWidth: '1080px', margin: '48px auto', padding: '32px', backgroundColor: 'var(--bg-panel)', border: '1px solid var(--border-hairline)', borderRadius: '6px' }}>
        <h2 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--ink-primary)' }}>Project Not Found</h2>
        <p style={{ fontSize: '13px', color: 'var(--ink-secondary)', marginTop: '8px' }}>
          {errorMsg || `Project identifier "${projectId}" is not registered in the canonical data lake.`}
        </p>
      </div>
    );
  }

  const sec1 = projectData.section_1_project_identity || {};
  const sec6 = projectData.section_6_transparent_cost_breakdown || {};
  const sec7 = projectData.section_7_modeled_microclimatic_and_risk_impact || {};

  const totalCost = portfolioSummary?.total_modeled_cost_inr || sec6.modeled_optimized_capex_inr || 9992500;
  const budgetEnvelope = portfolioSummary?.scenario_budget_envelope_inr || sec6.scenario_budget_envelope_inr || 10000000;
  const budgetSlack = portfolioSummary?.budget_slack_unallocated_inr || sec6.budget_slack_unallocated_inr || 7500;
  const totalTrees = portfolioSummary?.total_planned_quantity || 2695;
  const cellCount = allocations.length || 28;
  const popCount = portfolioSummary?.total_population_protected?.display_rounded || 118941;
  const objectiveScore = sec7.modeled_aggregate_risk_reduction_score || 0.106048;

  return (
    <div style={{ maxWidth: '1120px', margin: '0 auto', padding: '32px 32px 96px', display: 'flex', flexDirection: 'column', gap: '28px' }}>
      
      {/* 1. DEMO GOVERNANCE PERSONA BAR (Simulated Identity · Decoupled from Lens) */}
      <aside aria-label="Demo Governance Persona" style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '10px 16px',
        backgroundColor: 'var(--bg-elevated)',
        border: '1px solid var(--border-hairline)',
        borderRadius: '6px',
        fontSize: '12px',
        flexWrap: 'wrap',
        gap: '12px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <span style={{
            fontSize: '10px',
            fontWeight: 700,
            letterSpacing: '0.06em',
            textTransform: 'uppercase',
            padding: '2px 7px',
            borderRadius: '3px',
            backgroundColor: 'rgba(200, 255, 59, 0.1)',
            color: 'var(--accent-focal)',
            border: '1px solid rgba(200, 255, 59, 0.25)',
          }}>
            DEMO GOVERNANCE PERSONA
          </span>
          <span style={{ color: 'var(--ink-secondary)' }}>
            Simulated actor for server-side Cedar evaluation · Not production authentication
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <label htmlFor="demo-persona-select" style={{ color: 'var(--ink-secondary)', fontSize: '11px', fontWeight: 500 }}>
            Active Actor:
          </label>
          <select
            id="demo-persona-select"
            value={currentActor}
            onChange={(e) => handleActorSelect(e.target.value)}
            style={{
              padding: '5px 10px',
              backgroundColor: 'var(--bg-panel)',
              color: 'var(--ink-primary)',
              border: '1px solid var(--border-hairline)',
              borderRadius: '4px',
              fontSize: '12px',
              fontWeight: 500,
              cursor: 'pointer',
            }}
          >
            {DEMO_PERSONAS.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} — {p.displayRole}
              </option>
            ))}
          </select>
          <span className="font-tabular" style={{ fontSize: '11px', color: 'var(--accent-focal)', padding: '2px 6px', backgroundColor: 'var(--bg-card)', borderRadius: '3px', border: '1px solid var(--border-hairline-subtle)' }}>
            Role::"{activePersonaObj.role}"
          </span>
        </div>
      </aside>

      {/* 2. PROJECT IDENTITY HEADER */}
      <header style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span className="font-tabular" style={{ fontSize: '12px', color: 'var(--ink-secondary)' }}>
            {sec1.project_id || projectId}
          </span>
          <TruthBadge layer={lifecycleState} />
        </div>
        <h1 style={{ fontSize: '26px', fontWeight: 600, color: 'var(--ink-primary)', letterSpacing: '-0.01em' }}>
          {sec1.project_title || 'Pune Urban Heat Island Mitigation & Street Canopy Initiative'}
        </h1>
      </header>

      {/* 3. PERSPECTIVE LENS SELECTOR (Presentation Filter · Option A Invariant) */}
      <section aria-label="Perspective Lens Selector" style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--ink-secondary)', fontWeight: 600 }}>
              Perspective Lens (Presentation Filter)
            </span>
            <span style={{ fontSize: '11px', color: 'var(--ink-tertiary)' }}>
              Select to adjust presentation & action emphasis · Cedar authorization remains independent
            </span>
          </div>

          {!isPersonaAlignedWithLens && (
            <button
              onClick={() => handleActorSelect(currentLensDef.suggestedPersonaId)}
              style={{
                fontSize: '11px',
                color: 'var(--accent-focal)',
                backgroundColor: 'transparent',
                border: 'none',
                textDecoration: 'underline',
                cursor: 'pointer',
                padding: 0,
              }}
            >
              Align simulated persona to {currentLensDef.suggestedPersonaName} →
            </button>
          )}
        </div>

        <div
          role="tablist"
          aria-label="Perspective Lenses"
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '8px',
          }}
        >
          {PERSPECTIVES.map((lens) => {
            const isSelected = selectedLens === lens.id;
            return (
              <button
                key={lens.id}
                role="tab"
                aria-selected={isSelected}
                onClick={() => handleLensChange(lens.id)}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'flex-start',
                  textAlign: 'left',
                  padding: '12px 14px',
                  backgroundColor: isSelected ? 'var(--bg-elevated)' : 'var(--bg-panel)',
                  border: isSelected ? '1px solid var(--accent-focal)' : '1px solid var(--border-hairline)',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                  position: 'relative',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center' }}>
                  <span style={{
                    fontSize: '13px',
                    fontWeight: isSelected ? 600 : 500,
                    color: isSelected ? 'var(--ink-primary)' : 'var(--ink-secondary)',
                  }}>
                    {lens.name}
                  </span>
                  {isSelected && (
                    <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--accent-focal)' }} />
                  )}
                </div>
                <span style={{ fontSize: '11px', color: 'var(--ink-tertiary)', marginTop: '4px', lineHeight: 1.3 }}>
                  {lens.tagline}
                </span>
              </button>
            );
          })}
        </div>

        {/* Quiet Contextual Lens Note */}
        <div style={{
          padding: '8px 12px',
          backgroundColor: 'var(--bg-panel)',
          border: '1px solid var(--border-hairline-subtle)',
          borderRadius: '4px',
          fontSize: '11px',
          color: 'var(--ink-secondary)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '8px',
        }}>
          <div>
            <strong>Active Presentation Focus:</strong> {currentLensDef.name}. {currentLensDef.tagline}.
          </div>
          <div style={{ color: 'var(--ink-tertiary)' }}>
            Actions evaluated under server-side principal: <strong style={{ color: 'var(--ink-primary)' }}>{activePersonaObj.name}</strong> ({activePersonaObj.role})
          </div>
        </div>
      </section>

      {/* 4. TAB NAVIGATION */}
      <nav aria-label="Project Tabs" style={{ display: 'flex', gap: '24px', borderBottom: '1px solid var(--border-hairline)', overflowX: 'auto' }}>
        {(['overview', 'governance', 'allocation', 'baseline', 'budget', 'verification', 'provenance'] as TabKey[]).map((tab) => {
          const isActive = activeTab === tab;
          let label = tab as string;
          if (tab === 'governance') label = 'Governance (Cedar)';
          if (tab === 'budget') label = 'Budget & Finance Readiness';
          return (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                padding: '10px 0',
                fontSize: '13px',
                fontWeight: isActive ? 600 : 400,
                color: isActive ? 'var(--ink-primary)' : 'var(--ink-secondary)',
                borderBottom: isActive ? '2px solid var(--accent-focal)' : '2px solid transparent',
                textTransform: (tab === 'governance' || tab === 'budget') ? 'none' : 'capitalize',
                transition: 'color 0.15s ease',
                whiteSpace: 'nowrap',
                background: 'none',
                borderTop: 'none',
                borderLeft: 'none',
                borderRight: 'none',
                cursor: 'pointer',
              }}
            >
              {label}
            </button>
          );
        })}
      </nav>

      {/* 5. TAB CONTENT */}

      {/* 5.1 OVERVIEW TAB */}
      {activeTab === 'overview' && (
        <section style={{ display: 'flex', flexDirection: 'column', gap: '40px' }}>
          {/* Dominant Capital Figure */}
          <div style={{ padding: '24px 0', borderBottom: '1px solid var(--border-hairline)' }}>
            <span style={{ fontSize: '12px', color: 'var(--ink-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Modeled Capital Expenditure
            </span>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '16px', marginTop: '6px' }}>
              <p className="font-tabular" style={{ fontSize: '42px', fontWeight: 600, color: 'var(--ink-primary)' }}>
                ₹{totalCost.toLocaleString('en-US')}
              </p>
              <span style={{ fontSize: '13px', color: 'var(--ink-secondary)' }}>
                Under ₹{budgetEnvelope.toLocaleString('en-US')} statutory envelope
              </span>
            </div>
            <div style={{ marginTop: '8px' }}>
              <TruthBadge layer="MODELED" detail="Canonical HiGHS MILP Allocation" />
            </div>
          </div>

          {/* Structured Stats Grid (Two Tiers) */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '24px' }}>
            <div>
              <span style={{ fontSize: '11px', color: 'var(--ink-secondary)', textTransform: 'uppercase' }}>Physical Scope</span>
              <p className="font-tabular" style={{ fontSize: '22px', fontWeight: 600, color: 'var(--ink-primary)', marginTop: '4px' }}>
                {totalTrees.toLocaleString('en-US')} street trees
              </p>
              <span style={{ fontSize: '11px', color: 'var(--ink-tertiary)' }}>15.0m roadside interval</span>
            </div>

            <div>
              <span style={{ fontSize: '11px', color: 'var(--ink-secondary)', textTransform: 'uppercase' }}>Prioritized Area</span>
              <p className="font-tabular" style={{ fontSize: '22px', fontWeight: 600, color: 'var(--ink-primary)', marginTop: '4px' }}>
                {cellCount} H3 cells
              </p>
              <span style={{ fontSize: '11px', color: 'var(--ink-tertiary)' }}>9.86 ha/cell · ~2.76 km²</span>
            </div>

            <div>
              <span style={{ fontSize: '11px', color: 'var(--ink-secondary)', textTransform: 'uppercase' }}>Beneficiary Population</span>
              <p className="font-tabular" style={{ fontSize: '22px', fontWeight: 600, color: 'var(--ink-primary)', marginTop: '4px' }}>
                {popCount.toLocaleString('en-US')} residents
              </p>
              <span style={{ fontSize: '11px', color: 'var(--ink-tertiary)' }}>WorldPop 2020 dasymetric</span>
            </div>

            <div>
              <span style={{ fontSize: '11px', color: 'var(--ink-secondary)', textTransform: 'uppercase' }}>Remaining Slack</span>
              <p className="font-tabular" style={{ fontSize: '22px', fontWeight: 600, color: 'var(--ink-primary)', marginTop: '4px' }}>
                ₹{budgetSlack.toLocaleString('en-US')}
              </p>
              <span style={{ fontSize: '11px', color: 'var(--ink-tertiary)' }}>Retained municipal surplus</span>
            </div>
          </div>

          {/* Objective Score Disclaimed Elegantly */}
          <div style={{ padding: '16px 20px', backgroundColor: 'var(--bg-panel)', border: '1px solid var(--border-hairline)', borderRadius: '6px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span style={{ fontSize: '11px', color: 'var(--ink-secondary)' }}>Objective Score (F-24.4)</span>
                <p className="font-tabular" style={{ fontSize: '18px', fontWeight: 600, color: 'var(--ink-primary)' }}>
                  {objectiveScore.toFixed(6)}
                </p>
                <span style={{ fontSize: '11px', color: 'var(--ink-secondary)' }}>
                  Modeled aggregate objective reduction achieved under ₹10M budget formulation; not a percentage cooling claim.
                </span>
              </div>
              <TruthBadge layer="MODELED" />
            </div>
          </div>

          {/* Contextual Action Panel: Municipal Sanction Governance (Tailored per Perspective Lens) */}
          {selectedLens === 'civic' ? (
            /* Civic Transparency Mode: Public accountability, mutation button de-emphasized */
            <div style={{ padding: '24px', backgroundColor: 'var(--bg-panel)', border: '1px solid var(--border-hairline)', borderRadius: '6px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--ink-primary)' }}>Civic Transparency & Sanction Status</h3>
                  <span style={{ fontSize: '11px', padding: '1px 6px', borderRadius: '3px', backgroundColor: 'var(--bg-elevated)', color: 'var(--ink-secondary)', border: '1px solid var(--border-hairline)' }}>
                    Public Citizen View
                  </span>
                </div>
                <p style={{ fontSize: '12px', color: 'var(--ink-secondary)', marginTop: '4px' }}>
                  Project currently in <strong>{lifecycleState}</strong> state. Capital expenditure approval requires official sanction from the Municipal Sanctioning Authority / Commissioner. All evidence, cost allocations, and baselines are open for civic verification.
                </p>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <button
                  onClick={() => setActiveTab('governance')}
                  style={{
                    padding: '8px 14px',
                    backgroundColor: 'var(--bg-elevated)',
                    border: '1px solid var(--border-hairline)',
                    borderRadius: '4px',
                    fontSize: '12px',
                    color: 'var(--ink-primary)',
                    cursor: 'pointer',
                  }}
                >
                  Inspect Cedar Governance Trail →
                </button>
              </div>
            </div>
          ) : (
            /* Institutional Modes: Municipal Sanction Action Panel */
            <div style={{
              padding: '24px',
              backgroundColor: 'var(--bg-panel)',
              border: selectedLens === 'sanction' ? '1px solid var(--accent-focal)' : '1px solid var(--border-hairline)',
              borderRadius: '6px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '16px',
            }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--ink-primary)' }}>
                    Municipal Sanction Governance
                  </h3>
                  <span style={{ fontSize: '11px', padding: '1px 6px', borderRadius: '3px', backgroundColor: 'rgba(200, 255, 59, 0.1)', color: 'var(--accent-focal)', border: '1px solid rgba(200, 255, 59, 0.25)', fontWeight: 500 }}>
                    Cedar Gated
                  </span>
                </div>
                <p style={{ fontSize: '12px', color: 'var(--ink-secondary)', marginTop: '4px' }}>
                  Sanction authority reserved for <strong>Municipal Sanctioning Authority / Commissioner</strong> to transition project from <strong>PROPOSED</strong> to <strong>FUNDED</strong>.
                  Enforced via Amazon Cedar policy <code>@id("policy_officer_approve_project")</code>.
                </p>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <button
                  onClick={() => setActiveTab('governance')}
                  style={{
                    padding: '8px 14px',
                    backgroundColor: 'var(--bg-elevated)',
                    border: '1px solid var(--border-hairline)',
                    borderRadius: '4px',
                    fontSize: '12px',
                    color: 'var(--ink-primary)',
                    cursor: 'pointer',
                  }}
                >
                  Inspect Cedar Policies →
                </button>
                {lifecycleState === 'PROPOSED' ? (
                  <button
                    onClick={() => setIsSanctionModalOpen(true)}
                    style={{
                      padding: '10px 20px',
                      backgroundColor: 'var(--truth-modeled-ink)',
                      border: 'none',
                      borderRadius: '4px',
                      fontSize: '13px',
                      fontWeight: 600,
                      color: '#121413',
                      cursor: 'pointer',
                    }}
                  >
                    Sanction project & issue tender
                  </button>
                ) : (
                  <span style={{ padding: '8px 16px', backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-hairline)', borderRadius: '4px', fontSize: '12px', color: 'var(--truth-modeled-ink)' }}>
                    Project Sanctioned ({lifecycleState})
                  </span>
                )}
              </div>
            </div>
          )}
        </section>
      )}

      {/* 5.2 CEDAR GOVERNANCE TAB */}
      {activeTab === 'governance' && (
        <section style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <CedarGovernancePanel
            projectId={projectId}
            lifecycleState={lifecycleState}
            onStateChanged={(newState) => setLifecycleState(newState)}
            onOpenSanctionModal={() => setIsSanctionModalOpen(true)}
            onOpenRevisionModal={() => {
              setTargetRevisionCell(allocations[0]?.h3_cell_id || '89608850003ffff');
              setIsRevisionModalOpen(true);
            }}
          />
        </section>
      )}

      {/* 5.3 ALLOCATION TAB */}
      {activeTab === 'allocation' && (
        <section style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h2 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--ink-primary)' }}>
                Canonical Allocation Blueprint
              </h2>
              <p style={{ fontSize: '12px', color: 'var(--ink-secondary)', marginTop: '2px' }}>
                Immutable spatial allocation across all {allocations.length} prioritized H3 Resolution 9 cells.
              </p>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ fontSize: '11px', color: 'var(--ink-tertiary)', border: '1px solid var(--border-hairline)', padding: '4px 8px', borderRadius: '3px' }}>
                Canonical allocation is immutable
              </span>

              {/* Show Propose Revision button when not in Civic Transparency view */}
              {selectedLens !== 'civic' ? (
                <button
                  onClick={() => {
                    setTargetRevisionCell(allocations[0]?.h3_cell_id || '');
                    setIsRevisionModalOpen(true);
                  }}
                  style={{
                    padding: '6px 14px',
                    backgroundColor: selectedLens === 'planning' ? 'var(--truth-modeled-ink)' : 'var(--bg-elevated)',
                    border: '1px solid var(--border-hairline)',
                    borderRadius: '4px',
                    fontSize: '12px',
                    color: selectedLens === 'planning' ? '#121413' : 'var(--ink-primary)',
                    fontWeight: selectedLens === 'planning' ? 600 : 400,
                    cursor: 'pointer',
                  }}
                >
                  Propose revision
                </button>
              ) : (
                <span style={{ fontSize: '11px', color: 'var(--ink-tertiary)' }}>
                  Public Record (Read-Only)
                </span>
              )}
            </div>
          </div>

          <div style={{ overflowX: 'auto', border: '1px solid var(--border-hairline)', borderRadius: '6px' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px', backgroundColor: 'var(--bg-panel)' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-hairline)', color: 'var(--ink-secondary)', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  <th style={{ padding: '12px 16px' }}>H3 Cell</th>
                  <th style={{ padding: '12px 16px' }}>Street Trees</th>
                  <th style={{ padding: '12px 16px' }}>Direct Cost (₹3,500/tree)</th>
                  <th style={{ padding: '12px 16px' }}>Mobilization (Fixed)</th>
                  <th style={{ padding: '12px 16px' }}>Total Cost</th>
                  <th style={{ padding: '12px 16px' }}>In-Scope Population</th>
                  <th style={{ padding: '12px 16px' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {allocations.map((a) => (
                  <tr key={a.h3_cell_id} style={{ borderBottom: '1px solid var(--border-hairline-subtle)' }}>
                    <td className="font-tabular" style={{ padding: '12px 16px', fontWeight: 600 }}>
                      {a.h3_cell_id}
                    </td>
                    <td className="font-tabular" style={{ padding: '12px 16px' }}>
                      {a.planned_quantity}
                    </td>
                    <td className="font-tabular" style={{ padding: '12px 16px' }}>
                      ₹{(a.planned_quantity * a.unit_cost).toLocaleString('en-US')}
                    </td>
                    <td className="font-tabular" style={{ padding: '12px 16px' }}>
                      ₹{a.mobilization_fixed_cost.toLocaleString('en-US')}
                    </td>
                    <td className="font-tabular" style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--truth-modeled-ink)' }}>
                      ₹{a.total_modeled_cost.toLocaleString('en-US')}
                    </td>
                    <td className="font-tabular" style={{ padding: '12px 16px' }}>
                      {Math.round(a.population_in_cell).toLocaleString('en-US')}
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      {selectedLens !== 'civic' ? (
                        <button
                          onClick={() => {
                            setTargetRevisionCell(a.h3_cell_id);
                            setIsRevisionModalOpen(true);
                          }}
                          style={{ fontSize: '11px', color: 'var(--truth-derived-ink)', textDecoration: 'underline', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
                        >
                          Branch revision
                        </button>
                      ) : (
                        <span style={{ fontSize: '11px', color: 'var(--ink-tertiary)' }}>
                          Ratified Cell
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* 5.4 BASELINE EVIDENCE TAB */}
      {activeTab === 'baseline' && (
        <section style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div>
            <h2 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--ink-primary)' }}>
              Multi-Year Thermal & Biophysical Baseline
            </h2>
            <p style={{ fontSize: '12px', color: 'var(--ink-secondary)', marginTop: '2px' }}>
              Observed and derived remote sensing evidence across all {baselineCells.length} prioritized cells.
            </p>
          </div>

          <div style={{ overflowX: 'auto', border: '1px solid var(--border-hairline)', borderRadius: '6px' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px', backgroundColor: 'var(--bg-panel)' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-hairline)', color: 'var(--ink-secondary)', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  <th style={{ padding: '12px 16px' }}>H3 Cell</th>
                  <th style={{ padding: '12px 16px' }}>2025 LST (Observed)</th>
                  <th style={{ padding: '12px 16px' }}>5-Yr Baseline Mean</th>
                  <th style={{ padding: '12px 16px' }}>Thermal Anomaly</th>
                  <th style={{ padding: '12px 16px' }}>Canopy Cover (NDVI)</th>
                  <th style={{ padding: '12px 16px' }}>Built-Up Index (NDBI)</th>
                  <th style={{ padding: '12px 16px' }}>Cluster Type</th>
                </tr>
              </thead>
              <tbody>
                {baselineCells.map((c) => {
                  const m = c.metrics;
                  return (
                    <tr key={c.h3_cell_id} style={{ borderBottom: '1px solid var(--border-hairline-subtle)' }}>
                      <td className="font-tabular" style={{ padding: '12px 16px', fontWeight: 600 }}>
                        {c.h3_cell_id}
                      </td>
                      <td className="font-tabular" style={{ padding: '12px 16px' }}>
                        {m?.lst_2025?.value}°C
                      </td>
                      <td className="font-tabular" style={{ padding: '12px 16px', color: 'var(--ink-secondary)' }}>
                        {m?.lst_baseline_mean?.value}°C
                      </td>
                      <td className="font-tabular" style={{ padding: '12px 16px', color: 'var(--ink-secondary)' }}>
                        +{m?.lst_anomaly_absolute?.value}°C
                      </td>
                      <td className="font-tabular" style={{ padding: '12px 16px' }}>
                        {m?.ndvi_2025?.value?.toFixed(4)}
                      </td>
                      <td className="font-tabular" style={{ padding: '12px 16px' }}>
                        {m?.ndbi_2025?.value?.toFixed(4)}
                      </td>
                      <td style={{ padding: '12px 16px' }}>
                        <span style={{ fontSize: '11px', color: 'var(--ink-secondary)' }}>
                          {m?.lisa_quadrant?.value || 'High-High'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* 5.5 BUDGET & FINANCE READINESS TAB (Section 9 Compliance) */}
      {activeTab === 'budget' && (
        <section style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
          <div>
            <h2 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--ink-primary)' }}>
              Institutional Financial Memorandum & Bankability Case
            </h2>
            <p style={{ fontSize: '12px', color: 'var(--ink-secondary)', marginTop: '2px' }}>
              Transparent capital composition, unit economics, and statutory allocation under the ₹10,000,000 envelope.
            </p>
          </div>

          {/* Three Macro Figures */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px' }}>
            <div style={{ padding: '20px', backgroundColor: 'var(--bg-panel)', border: '1px solid var(--border-hairline)', borderRadius: '6px' }}>
              <span style={{ fontSize: '11px', color: 'var(--ink-secondary)', textTransform: 'uppercase' }}>Budget Envelope</span>
              <p className="font-tabular" style={{ fontSize: '26px', fontWeight: 600, color: 'var(--ink-primary)', marginTop: '4px' }}>
                ₹{budgetEnvelope.toLocaleString('en-US')}
              </p>
              <span style={{ fontSize: '11px', color: 'var(--ink-tertiary)' }}>Statutory municipal allocation</span>
            </div>

            <div style={{ padding: '20px', backgroundColor: 'var(--bg-panel)', border: '1px solid var(--border-hairline)', borderRadius: '6px' }}>
              <span style={{ fontSize: '11px', color: 'var(--ink-secondary)', textTransform: 'uppercase' }}>Allocated Capital</span>
              <p className="font-tabular" style={{ fontSize: '26px', fontWeight: 600, color: 'var(--truth-modeled-ink)', marginTop: '4px' }}>
                ₹{totalCost.toLocaleString('en-US')}
              </p>
              <span style={{ fontSize: '11px', color: 'var(--ink-tertiary)' }}>99.925% budget utilization</span>
            </div>

            <div style={{ padding: '20px', backgroundColor: 'var(--bg-panel)', border: '1px solid var(--border-hairline)', borderRadius: '6px' }}>
              <span style={{ fontSize: '11px', color: 'var(--ink-secondary)', textTransform: 'uppercase' }}>Unallocated Slack</span>
              <p className="font-tabular" style={{ fontSize: '26px', fontWeight: 600, color: 'var(--ink-primary)', marginTop: '4px' }}>
                ₹{budgetSlack.toLocaleString('en-US')}
              </p>
              <span style={{ fontSize: '11px', color: 'var(--ink-tertiary)' }}>Retained in municipal treasury</span>
            </div>
          </div>

          {/* Green Finance Readiness & Bankability Diligence Card */}
          <div style={{
            padding: '24px',
            backgroundColor: 'var(--bg-panel)',
            border: '1px solid var(--border-hairline)',
            borderRadius: '6px',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--ink-primary)' }}>
                    Green Finance Readiness & Capital Diligence Case
                  </h3>
                  <span style={{ fontSize: '10px', textTransform: 'uppercase', padding: '2px 6px', borderRadius: '3px', backgroundColor: 'rgba(92, 184, 92, 0.1)', color: '#5CB85C', border: '1px solid rgba(92, 184, 92, 0.25)', fontWeight: 600 }}>
                    Bankable Asset
                  </span>
                </div>
                <p style={{ fontSize: '12px', color: 'var(--ink-secondary)', marginTop: '4px' }}>
                  Pre-structured environmental investment diligence metrics for municipal green bonds and climate finance partners.
                </p>
              </div>
              <span style={{ fontSize: '11px', color: 'var(--ink-tertiary)', border: '1px solid var(--border-hairline)', padding: '4px 8px', borderRadius: '4px' }}>
                Statutory Price Basis: 2025 INR
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', borderTop: '1px solid var(--border-hairline-subtle)', paddingTop: '16px', fontSize: '12px' }}>
              <div>
                <span style={{ color: 'var(--ink-secondary)' }}>Statutory Capital Envelope</span>
                <p className="font-tabular" style={{ fontSize: '18px', fontWeight: 600, color: 'var(--ink-primary)', marginTop: '2px' }}>
                  ₹{budgetEnvelope.toLocaleString('en-US')}
                </p>
                <span style={{ fontSize: '10px', color: 'var(--ink-tertiary)' }}>PMC Annual Heat Mitigation Scheme</span>
              </div>

              <div>
                <span style={{ color: 'var(--ink-secondary)' }}>Beneficiary Population Scale</span>
                <p className="font-tabular" style={{ fontSize: '18px', fontWeight: 600, color: 'var(--ink-primary)', marginTop: '2px' }}>
                  {popCount.toLocaleString('en-US')} residents
                </p>
                <span style={{ fontSize: '10px', color: 'var(--ink-tertiary)' }}>WorldPop 2020 dasymetric screening</span>
              </div>

              <div>
                <span style={{ color: 'var(--ink-secondary)' }}>Capex Per Beneficiary</span>
                <p className="font-tabular" style={{ fontSize: '18px', fontWeight: 600, color: 'var(--accent-focal)', marginTop: '2px' }}>
                  ₹{(totalCost / popCount).toFixed(2)} / person
                </p>
                <span style={{ fontSize: '10px', color: 'var(--ink-tertiary)' }}>Cost-effective urban climate intervention</span>
              </div>

              <div>
                <span style={{ color: 'var(--ink-secondary)' }}>Third-Party MRV Standard</span>
                <p style={{ fontSize: '14px', fontWeight: 600, color: 'var(--ink-primary)', marginTop: '4px' }}>
                  ISO 14064-2 Protocol
                </p>
                <span style={{ fontSize: '10px', color: 'var(--ink-tertiary)' }}>Empirical Difference-in-Differences audit</span>
              </div>
            </div>

            <div style={{ padding: '12px 16px', backgroundColor: 'var(--bg-elevated)', borderRadius: '4px', border: '1px solid var(--border-hairline-subtle)', fontSize: '11px', color: 'var(--ink-secondary)', lineHeight: 1.4 }}>
              <strong style={{ color: 'var(--ink-primary)' }}>Governance & Transparency Distinction:</strong> This Finance Readiness view exposes pre-calculated municipal capital diligence metrics. CLIMORA operates as a civic decision and governance instrument; it does not process commercial lending transactions or debt disbursements.
            </div>
          </div>

          {/* Transparent Cost Arithmetic */}
          <div style={{ padding: '24px', backgroundColor: 'var(--bg-panel)', border: '1px solid var(--border-hairline)', borderRadius: '6px' }}>
            <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--ink-primary)', marginBottom: '16px' }}>
              Line-Item Cost Composition
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '13px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-hairline-subtle)', paddingBottom: '10px' }}>
                <div>
                  <strong>Direct Tree Procurement & Planting</strong>
                  <p style={{ fontSize: '11px', color: 'var(--ink-secondary)' }}>2,695 saplings × ₹3,500/tree (indigenous species + 2m guard)</p>
                </div>
                <span className="font-tabular" style={{ fontWeight: 600 }}>₹9,432,500</span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-hairline-subtle)', paddingBottom: '10px' }}>
                <div>
                  <strong>Cell Mobilization & Utilities</strong>
                  <p style={{ fontSize: '11px', color: 'var(--ink-secondary)' }}>28 cell clusters × ₹20,000/cell (recon, logistics, utility clearance)</p>
                </div>
                <span className="font-tabular" style={{ fontWeight: 600 }}>₹560,000</span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '4px' }}>
                <div>
                  <strong>Total Modeled CapEx</strong>
                </div>
                <span className="font-tabular" style={{ fontSize: '16px', fontWeight: 700, color: 'var(--truth-modeled-ink)' }}>₹9,992,500</span>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* 5.6 VERIFICATION TAB */}
      {activeTab === 'verification' && (
        <section style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
          <div>
            <h2 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--ink-primary)' }}>
              Independent MRV & Verification Gateway
            </h2>
            <p style={{ fontSize: '12px', color: 'var(--ink-secondary)', marginTop: '2px' }}>
              Post-implementation satellite difference-in-differences audit protocol (ISO 14064-2 aligned).
            </p>
          </div>

          {/* Lifecycle State Stepper */}
          <div style={{ padding: '20px', backgroundColor: 'var(--bg-panel)', border: '1px solid var(--border-hairline)', borderRadius: '6px' }}>
            <span style={{ fontSize: '11px', color: 'var(--ink-secondary)', textTransform: 'uppercase' }}>Lifecycle State</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginTop: '12px', flexWrap: 'wrap', fontSize: '12px' }}>
              {['Proposed', 'Funded', 'Implementing', 'Implemented', 'Monitoring', 'Verified'].map((step, idx) => {
                const isCurrent = lifecycleState.toUpperCase() === step.toUpperCase();
                return (
                  <div key={step} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span
                      style={{
                        padding: '4px 10px',
                        borderRadius: '4px',
                        backgroundColor: isCurrent ? 'var(--bg-elevated)' : 'transparent',
                        border: isCurrent ? '1px solid var(--truth-modeled-ink)' : '1px solid var(--border-hairline)',
                        color: isCurrent ? 'var(--ink-primary)' : 'var(--ink-tertiary)',
                        fontWeight: isCurrent ? 600 : 400,
                      }}
                    >
                      {step}
                    </span>
                    {idx < 5 && <span style={{ color: 'var(--ink-tertiary)' }}>→</span>}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Honest Verification Gate */}
          <div style={{ padding: '24px', backgroundColor: 'var(--bg-panel)', border: '1px solid var(--border-hairline)', borderRadius: '6px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--ink-primary)' }}>Verification Audit Status</h3>
                <p style={{ fontSize: '12px', color: 'var(--ink-secondary)', marginTop: '2px' }}>
                  Project currently in {lifecycleState} stage. Empirical cooling can only be certified post-implementation by an accredited verifier.
                </p>
              </div>
              <TruthBadge layer="NOT_YET_VERIFIED" />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', borderTop: '1px solid var(--border-hairline)', paddingTop: '16px', fontSize: '12px' }}>
              <div>
                <span style={{ color: 'var(--ink-secondary)' }}>Measured Empirical Cooling:</span>
                <p className="font-tabular" style={{ fontSize: '18px', fontWeight: 600, color: 'var(--ink-tertiary)', marginTop: '4px' }}>
                  —
                </p>
                <span style={{ fontSize: '10px', color: 'var(--ink-tertiary)' }}>Awaiting post-deployment Landsat overpasses</span>
              </div>

              <div>
                <span style={{ color: 'var(--ink-secondary)' }}>Difference-in-Differences Evaluation:</span>
                <p style={{ fontSize: '16px', fontWeight: 500, color: 'var(--ink-primary)', marginTop: '4px' }}>
                  Planned
                </p>
                <span style={{ fontSize: '10px', color: 'var(--ink-tertiary)' }}>Matched control cells designated in data lake</span>
              </div>
            </div>

            <div style={{ padding: '12px', backgroundColor: 'var(--bg-card)', borderRadius: '4px', border: '1px solid var(--border-hairline-subtle)', fontSize: '11px', color: 'var(--ink-tertiary)' }}>
              <strong>Scientific & Governance Invariant:</strong> Sentinel-2 optical imagery cannot be substituted for Landsat-9 TIRS thermal observations. Synthetic demo fixtures are strictly barred from certifying canonical projects.
            </div>
          </div>
        </section>
      )}

      {/* 5.7 PROVENANCE TAB */}
      {activeTab === 'provenance' && (
        <section style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div>
            <h2 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--ink-primary)' }}>
              Data Lake Lineage & Mathematical Formulations
            </h2>
            <p style={{ fontSize: '12px', color: 'var(--ink-secondary)', marginTop: '2px' }}>
              Cryptographic integrity verification and algorithmic reproducibility parameters.
            </p>
          </div>

          <div style={{ padding: '24px', backgroundColor: 'var(--bg-panel)', border: '1px solid var(--border-hairline)', borderRadius: '6px', display: 'flex', flexDirection: 'column', gap: '16px', fontSize: '12px' }}>
            <div>
              <span style={{ color: 'var(--ink-secondary)' }}>Optimization Solver Runtime</span>
              <p className="font-tabular" style={{ fontSize: '16px', fontWeight: 600, color: 'var(--ink-primary)', marginTop: '2px' }}>
                70.13 seconds (HiGHS Branch-and-Cut, scipy.optimize.milp)
              </p>
            </div>

            <div style={{ borderTop: '1px solid var(--border-hairline)', paddingTop: '12px' }}>
              <span style={{ color: 'var(--ink-secondary)' }}>Evaluated Candidate Pairs</span>
              <p className="font-tabular" style={{ fontSize: '16px', fontWeight: 600, color: 'var(--ink-primary)', marginTop: '2px' }}>
                7,115 candidate H3 cell pairs
              </p>
            </div>

            <div style={{ borderTop: '1px solid var(--border-hairline)', paddingTop: '12px' }}>
              <span style={{ color: 'var(--ink-secondary)' }}>Ratified Formulation Set</span>
              <p className="font-tabular" style={{ fontSize: '13px', color: 'var(--truth-derived-ink)', marginTop: '2px' }}>
                F-19, F-20, F-21, F-22, F-23.1, F-24.1, F-24.2, F-24.3, F-24.4, F-24.5, F-24.6, F-25.1
              </p>
            </div>

            <div style={{ borderTop: '1px solid var(--border-hairline)', paddingTop: '12px' }}>
              <span style={{ color: 'var(--ink-secondary)' }}>Allocation Parquet SHA-256</span>
              <p className="font-tabular" style={{ fontSize: '11px', color: 'var(--ink-primary)', marginTop: '2px', wordBreak: 'break-all' }}>
                {provenanceData?.source_sha256 || '2519473a32a2b4a3a22bc8beb43525c3f21dc404783168f1edd6de7bc4bb5555'}
              </p>
            </div>

            <button
              onClick={() => setIsProvenanceModalOpen(true)}
              style={{
                alignSelf: 'flex-start',
                marginTop: '8px',
                padding: '8px 16px',
                backgroundColor: 'var(--bg-elevated)',
                border: '1px solid var(--border-hairline)',
                borderRadius: '4px',
                fontSize: '12px',
                color: 'var(--ink-primary)',
                cursor: 'pointer',
              }}
            >
              Open Full Cryptographic Modal →
            </button>
          </div>
        </section>
      )}

      {/* State Transition & Revision Modals */}
      <StateTransitionModal
        projectId={projectId}
        isOpen={isSanctionModalOpen}
        onClose={() => setIsSanctionModalOpen(false)}
        onSuccess={(newState) => setLifecycleState(newState as ProjectLifecycleState)}
      />

      <RevisionModal
        projectId={projectId}
        initialCellId={targetRevisionCell}
        isOpen={isRevisionModalOpen}
        onClose={() => setIsRevisionModalOpen(false)}
        onSuccess={(rev) => {
          alert(`Revision proposed successfully for cell ${rev.h3_cell_id}. Revision ID: ${rev.revision_id}`);
        }}
      />

      <ProvenanceModal
        isOpen={isProvenanceModalOpen}
        onClose={() => setIsProvenanceModalOpen(false)}
        provenanceData={provenanceData}
      />
    </div>
  );
};
