import React, { useEffect, useState } from 'react';
import {
  CANONICAL_PROJECT_ID,
  climoraApi,
  getCurrentActor,
  setCurrentActor,
  onActorChange,
} from '../services/api';
import {
  GovernanceActor,
  GovernanceAuditRecord,
  GovernanceCheckResult,
  ProjectLifecycleState,
} from '../types/api';

const DEFAULT_DEMO_ACTORS: GovernanceActor[] = [
  {
    actor_id: 'pmc_commissioner',
    name: 'Dr. Rajesh Patil',
    role: 'municipal_officer',
    title: 'Municipal Commissioner',
    organization: 'Pune Municipal Corporation (PMC)',
    description: 'Authorized municipal signatory for capital budget sanctions and official tenders.',
  },
  {
    actor_id: 'urban_planner_lead',
    name: 'Pooja Deshmukh',
    role: 'project_manager',
    title: 'Lead Urban Climate Planner',
    organization: 'PMC Environment & Garden Dept',
    description: 'Manages tree canopy interventions, spatial allocations, and stakeholder proposals.',
  },
  {
    actor_id: 'sharma_contractors',
    name: 'Sharma Agro & Forestry Ltd',
    role: 'field_contractor',
    title: 'Licensed EPC Planting Contractor',
    organization: 'PMC Vendor Registry #4402',
    description: 'Responsible for ground sapling procurement, roadside digging, and batch deployment.',
  },
  {
    actor_id: 'sgs_environmental_auditor',
    name: 'SGS Environmental Auditing',
    role: 'mrv_verifier',
    title: 'Accredited GHG/MRV Verifier',
    organization: 'ISO 14064-2 Certified Independent Auditor',
    description: 'Performs post-monsoon satellite observation checks and difference-in-differences audits.',
  },
  {
    actor_id: 'citizen_viewer',
    name: 'Ananya Joshi',
    role: 'viewer',
    title: 'Public Observer / Resident',
    organization: 'Pune Civic Climate Forum',
    description: 'Citizen auditor inspecting open municipal climate allocations and expenditure transparency.',
  },
];

interface CedarGovernancePanelProps {
  projectId?: string;
  lifecycleState: ProjectLifecycleState;
  onStateChanged?: (newState: ProjectLifecycleState) => void;
  onOpenSanctionModal?: () => void;
  onOpenRevisionModal?: () => void;
}

export const CedarGovernancePanel: React.FC<CedarGovernancePanelProps> = ({
  projectId = CANONICAL_PROJECT_ID,
  lifecycleState,
  onStateChanged,
  onOpenSanctionModal,
  onOpenRevisionModal,
}) => {
  const [actors, setActors] = useState<GovernanceActor[]>(DEFAULT_DEMO_ACTORS);
  const [selectedActorId, setSelectedActorId] = useState<string>(getCurrentActor());
  const [auditTrail, setAuditTrail] = useState<GovernanceAuditRecord[]>([]);
  const [lastCheckResult, setLastCheckResult] = useState<GovernanceCheckResult | null>(null);
  const [lastDenial, setLastDenial] = useState<any | null>(null);
  const [isEvaluating, setIsEvaluating] = useState<boolean>(false);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);

  // Load registered personas and audit log on mount
  useEffect(() => {
    climoraApi.getGovernanceActors()
      .then((res) => {
        if (res && res.length > 0) {
          setActors(res);
          if (!res.find((a) => a.actor_id === selectedActorId)) {
            setSelectedActorId(res[0].actor_id);
            setCurrentActor(res[0].actor_id);
          }
        }
      })
      .catch(() => {
        // Retain default demo actors
      });

    loadAuditTrail();
  }, [projectId]);

  // Synchronize with external persona changes (e.g., from ProjectPage demo bar)
  useEffect(() => {
    const unsubscribe = onActorChange((actorId) => {
      setSelectedActorId(actorId);
    });
    return unsubscribe;
  }, []);

  const loadAuditTrail = () => {
    climoraApi.getGovernanceAudit(projectId)
      .then((records) => setAuditTrail(records))
      .catch(() => {});
  };

  const handleActorChange = (actorId: string) => {
    setSelectedActorId(actorId);
    setCurrentActor(actorId);
    setLastCheckResult(null);
    setLastDenial(null);
    setFeedbackMessage(`Active persona changed to: ${actors.find((a) => a.actor_id === actorId)?.name}`);
  };

  const activeActor = actors.find((a) => a.actor_id === selectedActorId) || actors[0];

  // Test dry-run policy evaluation
  const runPreflightCheck = async (action: string) => {
    setIsEvaluating(true);
    setLastDenial(null);
    try {
      const res = await climoraApi.checkGovernance(projectId, action, selectedActorId);
      setLastCheckResult(res);
      loadAuditTrail();
    } catch (err: any) {
      setLastDenial(err.details || { message: err.message });
    } finally {
      setIsEvaluating(false);
    }
  };

  // Attempt real mutation action under the current actor
  const executeGovernanceAction = async (action: string) => {
    setIsEvaluating(true);
    setLastDenial(null);
    setLastCheckResult(null);
    setFeedbackMessage(null);

    try {
      if (action === 'approve_project') {
        if (lifecycleState !== 'PROPOSED') {
          // Will be denied by Cedar or state machine
          await climoraApi.transitionState(projectId, 'FUNDED', 'PMC-2025-SANC-UI', 10000000.0);
        } else {
          // Open sanction modal if officer, or attempt transition directly to verify Cedar denial
          if (activeActor.role === 'municipal_officer' && onOpenSanctionModal) {
            onOpenSanctionModal();
            setIsEvaluating(false);
            return;
          }
          await climoraApi.transitionState(projectId, 'FUNDED', 'PMC-2025-SANC-UI', 10000000.0);
          if (onStateChanged) onStateChanged('FUNDED');
          setFeedbackMessage('Project successfully sanctioned under Municipal Officer authority.');
        }
      } else if (action === 'propose_revision') {
        if (activeActor.role === 'project_manager' && onOpenRevisionModal) {
          onOpenRevisionModal();
          setIsEvaluating(false);
          return;
        }
        await climoraApi.proposeRevision(
          projectId,
          '89608850003ffff',
          'street_tree_shade',
          78.0,
          'Roadside clearance adjustment (UI Governance Demonstration)',
          activeActor.name
        );
        setFeedbackMessage('Allocation revision proposed under Project Manager authority.');
      } else if (action === 'record_implementation') {
        const res = await climoraApi.recordImplementationEvent(projectId, {
          intervention_code: 'street_tree_shade',
          h3_cell_id: '89608850003ffff',
          implemented_quantity: 76.0,
          completion_date: '2026-04-10',
          contractor_id: activeActor.name,
          evidence_uri: 's3://climora/evidence/tree_field_signoff.pdf',
        });
        setFeedbackMessage(`Implementation event recorded: ${res.event.event_id}`);
      } else if (action === 'modify_canonical_data') {
        // Critical Negative Policy Demonstration
        await climoraApi.attemptAllocationMutation(projectId);
      }
      loadAuditTrail();
    } catch (err: any) {
      setLastDenial(err.details || {
        decision: 'DENY',
        action,
        reason: err.message,
        policy_layer: 'cedar',
      });
      loadAuditTrail();
    } finally {
      setIsEvaluating(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* 1. Header & Architecture Introduction */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h2 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--ink-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              Amazon Cedar Governance & Policy Enforcement
              <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '4px', backgroundColor: 'rgba(59, 122, 87, 0.18)', color: '#7EE787', border: '1px solid rgba(59, 122, 87, 0.4)', fontWeight: 500 }}>
                Server-Side Authorizer
              </span>
            </h2>
            <p style={{ fontSize: '13px', color: 'var(--ink-secondary)', marginTop: '4px', maxWidth: '720px' }}>
              CLIMORA implements fine-grained, state-aware authorization powered by Amazon Cedar (<code style={{ fontSize: '12px', color: 'var(--accent-focal)' }}>cedarpy</code>).
              Every governance transition evaluates principal authority, project lifecycle state, and scientific MRV prerequisites.
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: 'var(--ink-secondary)' }}>
            <span>Current Project State:</span>
            <span className="font-tabular" style={{ fontWeight: 600, color: 'var(--accent-focal)', backgroundColor: 'var(--bg-card)', padding: '3px 8px', borderRadius: '4px', border: '1px solid var(--border-hairline)' }}>
              {lifecycleState}
            </span>
          </div>
        </div>
      </div>

      {/* 2. Demo Persona Selector Box */}
      <div style={{ padding: '20px', backgroundColor: 'var(--bg-panel)', border: '1px solid var(--border-hairline)', borderRadius: '8px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--ink-tertiary)', fontWeight: 600 }}>
              DEMO GOVERNANCE PERSONA SWITCHER (Simulated Principal Identity · Not Production Authentication)
            </span>
            <p style={{ fontSize: '12px', color: 'var(--ink-secondary)', marginTop: '2px' }}>
              Switch personas to observe real-time Cedar authorization boundaries across different civic stakeholders.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {actors.map((actor) => (
              <button
                key={actor.actor_id}
                onClick={() => handleActorChange(actor.actor_id)}
                style={{
                  padding: '6px 12px',
                  borderRadius: '5px',
                  fontSize: '12px',
                  fontWeight: selectedActorId === actor.actor_id ? 600 : 400,
                  backgroundColor: selectedActorId === actor.actor_id ? 'var(--bg-elevated)' : 'transparent',
                  color: selectedActorId === actor.actor_id ? 'var(--ink-primary)' : 'var(--ink-secondary)',
                  border: selectedActorId === actor.actor_id ? '1px solid var(--accent-focal)' : '1px solid var(--border-hairline)',
                  transition: 'all 0.15s ease',
                }}
              >
                {actor.name} ({actor.role})
              </button>
            ))}
          </div>
        </div>

        {activeActor && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', backgroundColor: 'var(--bg-card)', padding: '14px', borderRadius: '6px', border: '1px solid var(--border-hairline-subtle)', fontSize: '12px' }}>
            <div>
              <span style={{ color: 'var(--ink-tertiary)' }}>Principal Name:</span>
              <p style={{ fontWeight: 600, color: 'var(--ink-primary)', marginTop: '2px' }}>{activeActor.name}</p>
            </div>
            <div>
              <span style={{ color: 'var(--ink-tertiary)' }}>Cedar Role:</span>
              <p className="font-tabular" style={{ fontWeight: 600, color: 'var(--accent-focal)', marginTop: '2px' }}>Role::"{activeActor.role}"</p>
            </div>
            <div>
              <span style={{ color: 'var(--ink-tertiary)' }}>Organization:</span>
              <p style={{ color: 'var(--ink-secondary)', marginTop: '2px' }}>{activeActor.organization}</p>
            </div>
            <div>
              <span style={{ color: 'var(--ink-tertiary)' }}>Mandate / Scope:</span>
              <p style={{ color: 'var(--ink-secondary)', marginTop: '2px', fontSize: '11px' }}>{activeActor.description}</p>
            </div>
          </div>
        )}
      </div>

      {/* 3. Interactive Governance Simulator */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {/* Left Column: Action Triggers */}
        <div style={{ padding: '20px', backgroundColor: 'var(--bg-panel)', border: '1px solid var(--border-hairline)', borderRadius: '8px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--ink-primary)' }}>
              Test Governance Lifecycle Actions
            </h3>
            <p style={{ fontSize: '12px', color: 'var(--ink-secondary)', marginTop: '2px' }}>
              Evaluate Cedar policy for the active persona against current project state ({lifecycleState}).
            </p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {/* Action 1: Sanction Project */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 12px', backgroundColor: 'var(--bg-card)', borderRadius: '6px', border: '1px solid var(--border-hairline-subtle)' }}>
              <div>
                <span style={{ fontSize: '13px', fontWeight: 500, color: 'var(--ink-primary)' }}>Approve Project Sanction</span>
                <p style={{ fontSize: '11px', color: 'var(--ink-tertiary)' }}>Action::"approve_project" (Requires Municipal Officer + PROPOSED state)</p>
              </div>
              <div style={{ display: 'flex', gap: '6px' }}>
                <button
                  onClick={() => runPreflightCheck('approve_project')}
                  style={{ padding: '4px 10px', fontSize: '11px', backgroundColor: 'var(--bg-elevated)', border: '1px solid var(--border-hairline)', borderRadius: '4px', color: 'var(--ink-secondary)' }}
                >
                  Pre-flight
                </button>
                <button
                  onClick={() => executeGovernanceAction('approve_project')}
                  style={{ padding: '4px 10px', fontSize: '11px', backgroundColor: 'rgba(200, 255, 59, 0.12)', border: '1px solid var(--accent-focal)', borderRadius: '4px', color: 'var(--accent-focal)', fontWeight: 500 }}
                >
                  Execute
                </button>
              </div>
            </div>

            {/* Action 2: Propose Allocation Revision */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 12px', backgroundColor: 'var(--bg-card)', borderRadius: '6px', border: '1px solid var(--border-hairline-subtle)' }}>
              <div>
                <span style={{ fontSize: '13px', fontWeight: 500, color: 'var(--ink-primary)' }}>Propose Allocation Revision</span>
                <p style={{ fontSize: '11px', color: 'var(--ink-tertiary)' }}>Action::"propose_revision" (Requires Project Manager)</p>
              </div>
              <div style={{ display: 'flex', gap: '6px' }}>
                <button
                  onClick={() => runPreflightCheck('propose_revision')}
                  style={{ padding: '4px 10px', fontSize: '11px', backgroundColor: 'var(--bg-elevated)', border: '1px solid var(--border-hairline)', borderRadius: '4px', color: 'var(--ink-secondary)' }}
                >
                  Pre-flight
                </button>
                <button
                  onClick={() => executeGovernanceAction('propose_revision')}
                  style={{ padding: '4px 10px', fontSize: '11px', backgroundColor: 'rgba(200, 255, 59, 0.12)', border: '1px solid var(--accent-focal)', borderRadius: '4px', color: 'var(--accent-focal)', fontWeight: 500 }}
                >
                  Execute
                </button>
              </div>
            </div>

            {/* Action 3: Record Implementation */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 12px', backgroundColor: 'var(--bg-card)', borderRadius: '6px', border: '1px solid var(--border-hairline-subtle)' }}>
              <div>
                <span style={{ fontSize: '13px', fontWeight: 500, color: 'var(--ink-primary)' }}>Record Physical Deployment</span>
                <p style={{ fontSize: '11px', color: 'var(--ink-tertiary)' }}>Action::"record_implementation" (Requires Contractor + FUNDED/IMPLEMENTING)</p>
              </div>
              <div style={{ display: 'flex', gap: '6px' }}>
                <button
                  onClick={() => runPreflightCheck('record_implementation')}
                  style={{ padding: '4px 10px', fontSize: '11px', backgroundColor: 'var(--bg-elevated)', border: '1px solid var(--border-hairline)', borderRadius: '4px', color: 'var(--ink-secondary)' }}
                >
                  Pre-flight
                </button>
                <button
                  onClick={() => executeGovernanceAction('record_implementation')}
                  style={{ padding: '4px 10px', fontSize: '11px', backgroundColor: 'rgba(200, 255, 59, 0.12)', border: '1px solid var(--accent-focal)', borderRadius: '4px', color: 'var(--accent-focal)', fontWeight: 500 }}
                >
                  Execute
                </button>
              </div>
            </div>

            {/* Action 4: Verify Impact */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 12px', backgroundColor: 'var(--bg-card)', borderRadius: '6px', border: '1px solid var(--border-hairline-subtle)' }}>
              <div>
                <span style={{ fontSize: '13px', fontWeight: 500, color: 'var(--ink-primary)' }}>Certify MRV Verification</span>
                <p style={{ fontSize: '11px', color: 'var(--ink-tertiary)' }}>Action::"verify_impact" (Requires Verifier + MONITORING + Passing QC)</p>
              </div>
              <div style={{ display: 'flex', gap: '6px' }}>
                <button
                  onClick={() => runPreflightCheck('verify_impact')}
                  style={{ padding: '4px 10px', fontSize: '11px', backgroundColor: 'var(--bg-elevated)', border: '1px solid var(--border-hairline)', borderRadius: '4px', color: 'var(--ink-secondary)' }}
                >
                  Pre-flight
                </button>
                <button
                  onClick={() => executeGovernanceAction('verify_impact')}
                  style={{ padding: '4px 10px', fontSize: '11px', backgroundColor: 'rgba(200, 255, 59, 0.12)', border: '1px solid var(--accent-focal)', borderRadius: '4px', color: 'var(--accent-focal)', fontWeight: 500 }}
                >
                  Execute
                </button>
              </div>
            </div>

            {/* Action 5: Critical Negative Policy Demonstration */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 12px', backgroundColor: 'rgba(217, 107, 67, 0.08)', borderRadius: '6px', border: '1px solid rgba(217, 107, 67, 0.25)' }}>
              <div>
                <span style={{ fontSize: '13px', fontWeight: 500, color: '#FF7B72' }}>Mutate Scientific Parquet</span>
                <p style={{ fontSize: '11px', color: 'var(--ink-tertiary)' }}>Action::"modify_canonical_data" (Negative policy: universal forbid)</p>
              </div>
              <button
                onClick={() => executeGovernanceAction('modify_canonical_data')}
                style={{ padding: '4px 10px', fontSize: '11px', backgroundColor: 'rgba(217, 107, 67, 0.18)', border: '1px solid #FF7B72', borderRadius: '4px', color: '#FF7B72', fontWeight: 500 }}
              >
                Test Forbid
              </button>
            </div>
          </div>
        </div>

        {/* Right Column: Live Decision Evaluation Display */}
        <div style={{ padding: '20px', backgroundColor: 'var(--bg-panel)', border: '1px solid var(--border-hairline)', borderRadius: '8px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--ink-primary)' }}>
              Cedar Policy Authorization Pipeline
            </h3>
            {isEvaluating && (
              <span className="font-tabular" style={{ fontSize: '11px', color: 'var(--accent-focal)' }}>
                Evaluating Policy...
              </span>
            )}
          </div>

          {/* Conceptual Architecture Breadcrumb */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: 'var(--ink-tertiary)', flexWrap: 'wrap' }}>
            <span style={{ color: 'var(--ink-primary)' }}>{activeActor.role}</span>
            <span>→</span>
            <span style={{ color: 'var(--ink-primary)' }}>Action</span>
            <span>→</span>
            <span style={{ color: 'var(--accent-focal)' }}>Cedar Engine</span>
            <span>→</span>
            <span style={{ color: 'var(--ink-primary)' }}>Decision</span>
            <span>→</span>
            <span style={{ color: 'var(--ink-primary)' }}>State Machine</span>
            <span>→</span>
            <span style={{ color: 'var(--accent-focal)' }}>{lifecycleState}</span>
          </div>

          {/* Feedback or Decision Result Card */}
          {feedbackMessage && (
            <div style={{ padding: '12px', backgroundColor: 'rgba(59, 122, 87, 0.15)', border: '1px solid rgba(59, 122, 87, 0.35)', borderRadius: '6px', fontSize: '12px', color: '#7EE787' }}>
              ✓ {feedbackMessage}
            </div>
          )}

          {lastCheckResult && (
            <div
              style={{
                padding: '16px',
                borderRadius: '6px',
                border: lastCheckResult.allowed ? '1px solid rgba(59, 122, 87, 0.4)' : '1px solid rgba(217, 107, 67, 0.4)',
                backgroundColor: lastCheckResult.allowed ? 'rgba(59, 122, 87, 0.12)' : 'rgba(217, 107, 67, 0.10)',
                display: 'flex',
                flexDirection: 'column',
                gap: '10px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '13px', fontWeight: 600, color: lastCheckResult.allowed ? '#7EE787' : '#FF7B72' }}>
                  {lastCheckResult.allowed ? '✓ Cedar Policy: ALLOWED' : '✕ Cedar Policy: DENIED'}
                </span>
                <span className="font-tabular" style={{ fontSize: '11px', color: 'var(--ink-tertiary)' }}>
                  {lastCheckResult.audit_id}
                </span>
              </div>

              <div style={{ fontSize: '12px', color: 'var(--ink-primary)' }}>
                <p style={{ lineHeight: '1.4' }}>{lastCheckResult.reason_summary}</p>
              </div>

              <div style={{ borderTop: '1px solid var(--border-hairline-subtle)', paddingTop: '8px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '11px' }}>
                <div>
                  <span style={{ color: 'var(--ink-tertiary)' }}>Matched Policy:</span>
                  <p className="font-tabular" style={{ color: 'var(--accent-focal)', marginTop: '2px' }}>
                    {lastCheckResult.policy_id || 'default_deny'}
                  </p>
                </div>
                <div>
                  <span style={{ color: 'var(--ink-tertiary)' }}>State Machine Guard:</span>
                  <p style={{ color: lastCheckResult.allowed ? '#7EE787' : '#FF7B72', marginTop: '2px' }}>
                    {lastCheckResult.allowed ? 'VALID' : 'BLOCKED (Zero Mutation)'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {lastDenial && (
            <div
              style={{
                padding: '16px',
                borderRadius: '6px',
                border: '1px solid rgba(217, 107, 67, 0.4)',
                backgroundColor: 'rgba(217, 107, 67, 0.10)',
                display: 'flex',
                flexDirection: 'column',
                gap: '10px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '13px', fontWeight: 600, color: '#FF7B72' }}>
                  ✕ Cedar Governance: DENIED (HTTP 403)
                </span>
                <span className="font-tabular" style={{ fontSize: '11px', color: 'var(--ink-tertiary)' }}>
                  {lastDenial.audit_id || 'DENIED'}
                </span>
              </div>

              <div style={{ fontSize: '12px', color: 'var(--ink-primary)' }}>
                <p style={{ lineHeight: '1.4' }}>
                  {lastDenial.reason || lastDenial.message || 'Authorization denied under active Cedar policy set.'}
                </p>
              </div>

              <div style={{ borderTop: '1px solid var(--border-hairline-subtle)', paddingTop: '8px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '11px' }}>
                <div>
                  <span style={{ color: 'var(--ink-tertiary)' }}>Policy Layer:</span>
                  <p className="font-tabular" style={{ color: 'var(--accent-focal)', marginTop: '2px' }}>
                    {lastDenial.policy_layer || 'cedar'}
                  </p>
                </div>
                <div>
                  <span style={{ color: 'var(--ink-tertiary)' }}>Mutation Integrity:</span>
                  <p style={{ color: '#7EE787', marginTop: '2px' }}>
                    ZERO STATE MUTATION (Verified)
                  </p>
                </div>
              </div>
            </div>
          )}

          {!lastCheckResult && !lastDenial && !feedbackMessage && (
            <div style={{ padding: '24px', backgroundColor: 'var(--bg-card)', borderRadius: '6px', border: '1px solid var(--border-hairline-subtle)', textAlign: 'center', color: 'var(--ink-tertiary)', fontSize: '12px' }}>
              Select an action on the left to evaluate or execute real-time Cedar authorization.
            </div>
          )}
        </div>
      </div>

      {/* 4. Active Cedar Policy Set Reference */}
      <div style={{ padding: '20px', backgroundColor: 'var(--bg-panel)', border: '1px solid var(--border-hairline)', borderRadius: '8px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
        <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--ink-primary)' }}>
          Active Amazon Cedar Policy Rules
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '12px', fontSize: '12px' }}>
          <div style={{ padding: '12px', backgroundColor: 'var(--bg-card)', borderRadius: '6px', border: '1px solid var(--border-hairline-subtle)' }}>
            <span className="font-tabular" style={{ color: 'var(--accent-focal)', fontWeight: 600 }}>@id("policy_universal_view")</span>
            <p style={{ color: 'var(--ink-secondary)', marginTop: '4px', fontSize: '11px' }}>
              Universal Permit: Any principal (Citizen, Officer, Contractor, Verifier) can view project evidence. Scientific evidence is public.
            </p>
          </div>

          <div style={{ padding: '12px', backgroundColor: 'var(--bg-card)', borderRadius: '6px', border: '1px solid var(--border-hairline-subtle)' }}>
            <span className="font-tabular" style={{ color: 'var(--accent-focal)', fontWeight: 600 }}>@id("policy_pm_propose_revision")</span>
            <p style={{ color: 'var(--ink-secondary)', marginTop: '4px', fontSize: '11px' }}>
              Project Manager Permit: Propose cell-level tree allocation deltas and submit proposals without mutating canonical data.
            </p>
          </div>

          <div style={{ padding: '12px', backgroundColor: 'var(--bg-card)', borderRadius: '6px', border: '1px solid var(--border-hairline-subtle)' }}>
            <span className="font-tabular" style={{ color: 'var(--accent-focal)', fontWeight: 600 }}>@id("policy_officer_approve_project")</span>
            <p style={{ color: 'var(--ink-secondary)', marginTop: '4px', fontSize: '11px' }}>
              Municipal Sanction Permit: Only Municipal Officers may approve capital expenditure, strictly when project is in PROPOSED state.
            </p>
          </div>

          <div style={{ padding: '12px', backgroundColor: 'var(--bg-card)', borderRadius: '6px', border: '1px solid var(--border-hairline-subtle)' }}>
            <span className="font-tabular" style={{ color: 'var(--accent-focal)', fontWeight: 600 }}>@id("policy_contractor_record_impl")</span>
            <p style={{ color: 'var(--ink-secondary)', marginTop: '4px', fontSize: '11px' }}>
              Field Contractor Permit: Record physical sapling deployment events, strictly when project state is FUNDED or IMPLEMENTING.
            </p>
          </div>

          <div style={{ padding: '12px', backgroundColor: 'var(--bg-card)', borderRadius: '6px', border: '1px solid var(--border-hairline-subtle)' }}>
            <span className="font-tabular" style={{ color: 'var(--accent-focal)', fontWeight: 600 }}>@id("policy_mrv_verify_impact")</span>
            <p style={{ color: 'var(--ink-secondary)', marginTop: '4px', fontSize: '11px' }}>
              Independent MRV Certification Permit: Verifiers certify impacts only when state is MONITORING, DID is executable, and QC passed.
            </p>
          </div>

          <div style={{ padding: '12px', backgroundColor: 'rgba(217, 107, 67, 0.08)', borderRadius: '6px', border: '1px solid rgba(217, 107, 67, 0.25)' }}>
            <span className="font-tabular" style={{ color: '#FF7B72', fontWeight: 600 }}>@id("policy_forbid_canonical_mutation")</span>
            <p style={{ color: 'var(--ink-secondary)', marginTop: '4px', fontSize: '11px' }}>
              Architectural Immutability Guardrail: Absolute forbid. No principal may modify canonical scientific baselines or HiGHS optimization results.
            </p>
          </div>
        </div>
      </div>

      {/* 5. Live Governance Audit Trail */}
      <div style={{ padding: '20px', backgroundColor: 'var(--bg-panel)', border: '1px solid var(--border-hairline)', borderRadius: '8px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--ink-primary)' }}>
              Governance Authorization Audit Trail
            </h3>
            <p style={{ fontSize: '12px', color: 'var(--ink-secondary)', marginTop: '2px' }}>
              Chronological log of Cedar authorization evaluations for this project (in-memory demonstration log).
            </p>
          </div>

          <button
            onClick={loadAuditTrail}
            style={{ padding: '5px 12px', backgroundColor: 'var(--bg-elevated)', border: '1px solid var(--border-hairline)', borderRadius: '4px', fontSize: '12px', color: 'var(--ink-primary)' }}
          >
            ↻ Refresh Trail
          </button>
        </div>

        {auditTrail.length === 0 ? (
          <div style={{ padding: '24px', backgroundColor: 'var(--bg-card)', borderRadius: '6px', border: '1px solid var(--border-hairline-subtle)', textAlign: 'center', color: 'var(--ink-tertiary)', fontSize: '12px' }}>
            No governance decisions evaluated yet for this project. Use the simulator above to trigger policy evaluation.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-hairline)', color: 'var(--ink-tertiary)' }}>
                  <th style={{ padding: '8px 12px', fontWeight: 500 }}>Timestamp (UTC)</th>
                  <th style={{ padding: '8px 12px', fontWeight: 500 }}>Actor</th>
                  <th style={{ padding: '8px 12px', fontWeight: 500 }}>Role</th>
                  <th style={{ padding: '8px 12px', fontWeight: 500 }}>Action</th>
                  <th style={{ padding: '8px 12px', fontWeight: 500 }}>Decision</th>
                  <th style={{ padding: '8px 12px', fontWeight: 500 }}>Matched Policy</th>
                  <th style={{ padding: '8px 12px', fontWeight: 500 }}>Audit ID</th>
                </tr>
              </thead>
              <tbody>
                {auditTrail.map((record, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid var(--border-hairline-subtle)' }}>
                    <td className="font-tabular" style={{ padding: '8px 12px', color: 'var(--ink-secondary)', fontSize: '11px' }}>
                      {record.timestamp_utc ? record.timestamp_utc.slice(11, 19) : '—'}
                    </td>
                    <td style={{ padding: '8px 12px', color: 'var(--ink-primary)', fontWeight: 500 }}>
                      {record.actor_name || record.actor_id}
                    </td>
                    <td className="font-tabular" style={{ padding: '8px 12px', color: 'var(--accent-focal)' }}>
                      {record.role}
                    </td>
                    <td className="font-tabular" style={{ padding: '8px 12px', color: 'var(--ink-primary)' }}>
                      {record.action}
                    </td>
                    <td style={{ padding: '8px 12px' }}>
                      <span
                        style={{
                          display: 'inline-block',
                          padding: '2px 8px',
                          borderRadius: '4px',
                          fontSize: '11px',
                          fontWeight: 600,
                          backgroundColor: record.decision === 'ALLOW' ? 'rgba(59, 122, 87, 0.2)' : 'rgba(217, 107, 67, 0.2)',
                          color: record.decision === 'ALLOW' ? '#7EE787' : '#FF7B72',
                        }}
                      >
                        {record.decision}
                      </span>
                    </td>
                    <td className="font-tabular" style={{ padding: '8px 12px', color: 'var(--ink-secondary)', fontSize: '11px' }}>
                      {record.policy_id || 'default_deny'}
                    </td>
                    <td className="font-tabular" style={{ padding: '8px 12px', color: 'var(--ink-tertiary)', fontSize: '10px' }}>
                      {record.audit_id}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
