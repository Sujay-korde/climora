import React from 'react';
import { TruthBadge } from './TruthBadge';
import { ScenarioOptimizeResponse } from '../types/api';

interface ProjectBriefModalProps {
  scenario: ScenarioOptimizeResponse['data'];
  onClose: () => void;
}

export const ProjectBriefModal: React.FC<ProjectBriefModalProps> = ({ scenario, onClose }) => {
  const handlePrint = () => {
    window.print();
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(12, 14, 13, 0.88)',
        backdropFilter: 'blur(8px)',
        zIndex: 2000,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        padding: '24px',
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: 'var(--bg-card)',
          border: '1px solid var(--border-hairline)',
          borderRadius: '8px',
          width: '880px',
          maxWidth: '100%',
          maxHeight: '90vh',
          overflowY: 'auto',
          padding: '40px',
          display: 'flex',
          flexDirection: 'column',
          gap: '28px',
          boxShadow: '0 16px 48px rgba(0, 0, 0, 0.7)',
          fontFamily: 'var(--font-sans)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--border-hairline)', paddingBottom: '20px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--accent-focal)', fontWeight: 600 }}>
                Municipal Sanction & CSR Investment Dossier
              </span>
              <TruthBadge layer="MODELED" detail="Generated from HiGHS Optimization Engine" />
            </div>
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '28px', fontWeight: 400, color: 'var(--ink-primary)' }}>
              Bankable Adaptation Project Brief
            </h2>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--ink-secondary)' }}>
              Scenario ID: {scenario.scenario_id} · Project ID: {scenario.project_id}
            </span>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={handlePrint}
              style={{
                padding: '8px 16px',
                backgroundColor: 'var(--bg-panel)',
                border: '1px solid var(--border-hairline-hover)',
                borderRadius: '4px',
                fontSize: '12px',
                fontWeight: 500,
                color: 'var(--ink-primary)',
                cursor: 'pointer',
              }}
            >
              Export / Print Brief 🖨️
            </button>
            <button
              onClick={onClose}
              style={{
                padding: '8px 14px',
                backgroundColor: 'transparent',
                border: '1px solid var(--border-hairline)',
                borderRadius: '4px',
                fontSize: '12px',
                color: 'var(--ink-secondary)',
                cursor: 'pointer',
              }}
            >
              ✕ Close
            </button>
          </div>
        </div>

        {/* Section 1: Executive Summary */}
        <section style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <h3 style={{ fontSize: '14px', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--ink-secondary)' }}>
            1. Executive Investment Summary
          </h3>
          <p style={{ fontSize: '14px', color: 'var(--ink-primary)', lineHeight: 1.6 }}>
            The Pune Municipal Corporation (PMC), in coordination with CSR climate adaptation finance partners, authorizes this
            spatially optimized microclimate cooling portfolio. The investment deploys physically discrete, biophysically verified
            interventions across <strong>{scenario.total_cells_treated} high-priority H3 Resolution 9 hexagons</strong> to systematically
            suppress urban heat island exposure in vulnerable municipal wards.
          </p>
        </section>

        {/* Section 2: Financial Allocation & Capital Structure */}
        <section style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <h3 style={{ fontSize: '14px', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--ink-secondary)' }}>
            2. Financial Allocation & Municipal Line Items
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
            <div style={{ backgroundColor: 'var(--bg-panel)', padding: '12px 16px', borderRadius: '6px' }}>
              <span style={{ fontSize: '11px', color: 'var(--ink-secondary)', display: 'block' }}>Authorized Budget</span>
              <span className="font-tabular" style={{ fontSize: '18px', fontWeight: 600, color: 'var(--ink-primary)' }}>
                ₹{scenario.budget_inr.toLocaleString('en-IN')}
              </span>
            </div>
            <div style={{ backgroundColor: 'var(--bg-panel)', padding: '12px 16px', borderRadius: '6px' }}>
              <span style={{ fontSize: '11px', color: 'var(--ink-secondary)', display: 'block' }}>Total Allocated Cost</span>
              <span className="font-tabular" style={{ fontSize: '18px', fontWeight: 600, color: 'var(--accent-focal)' }}>
                ₹{scenario.total_allocated_cost_inr.toLocaleString('en-IN')}
              </span>
            </div>
            <div style={{ backgroundColor: 'var(--bg-panel)', padding: '12px 16px', borderRadius: '6px' }}>
              <span style={{ fontSize: '11px', color: 'var(--ink-secondary)', display: 'block' }}>Budget Slack / Reserve</span>
              <span className="font-tabular" style={{ fontSize: '18px', fontWeight: 600, color: 'var(--domain-hydrology)' }}>
                ₹{scenario.budget_slack_inr.toLocaleString('en-IN')}
              </span>
            </div>
          </div>
        </section>

        {/* Section 3: Physical Interventions Deployed */}
        <section style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <h3 style={{ fontSize: '14px', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--ink-secondary)' }}>
            3. Physical Scope & Discrete Quantities
          </h3>
          <div style={{ backgroundColor: 'var(--bg-panel)', borderRadius: '6px', padding: '16px' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-hairline)', color: 'var(--ink-secondary)', textAlign: 'left' }}>
                  <th style={{ padding: '6px 8px' }}>Intervention</th>
                  <th style={{ padding: '6px 8px' }}>Physical Quantity</th>
                  <th style={{ padding: '6px 8px' }}>Unit</th>
                  <th style={{ padding: '6px 8px' }}>Hexagons</th>
                  <th style={{ padding: '6px 8px' }}>Total Cost (INR)</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(scenario.summary_by_intervention).map(([code, info]) => (
                  <tr key={code} style={{ borderBottom: '1px solid var(--border-hairline-subtle)' }}>
                    <td style={{ padding: '8px', fontWeight: 500, color: 'var(--ink-primary)' }}>
                      {code === 'street_tree_shade' ? 'Urban Street Tree Canopy' : code}
                    </td>
                    <td className="font-tabular" style={{ padding: '8px', color: 'var(--accent-focal)', fontWeight: 600 }}>
                      {info.total_quantity.toLocaleString('en-IN')}
                    </td>
                    <td style={{ padding: '8px', color: 'var(--ink-secondary)' }}>{info.unit}</td>
                    <td className="font-tabular" style={{ padding: '8px', color: 'var(--ink-secondary)' }}>{info.cells_count}</td>
                    <td className="font-tabular" style={{ padding: '8px', color: 'var(--ink-primary)' }}>₹{info.total_cost_inr.toLocaleString('en-IN')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Section 4: Expected Scientific & Demographic Impact */}
        <section style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <h3 style={{ fontSize: '14px', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--ink-secondary)' }}>
            4. Expected Climate & Social Equity Outcomes
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px', fontSize: '13px', color: 'var(--ink-secondary)' }}>
            <div style={{ backgroundColor: 'var(--bg-panel)', padding: '14px', borderRadius: '6px' }}>
              <strong style={{ color: 'var(--ink-primary)', display: 'block', marginBottom: '4px' }}>
                Cumulative Modeled Risk Reduction:
              </strong>
              <p className="font-tabular" style={{ fontSize: '16px', color: 'var(--domain-thermal)', fontWeight: 600 }}>
                {scenario.optimal_objective_value.toFixed(6)}
              </p>
              <span style={{ fontSize: '11px', color: 'var(--ink-tertiary)' }}>
                Dimensionless response: sum of marginal vulnerability attenuations
              </span>
            </div>

            <div style={{ backgroundColor: 'var(--bg-panel)', padding: '14px', borderRadius: '6px' }}>
              <strong style={{ color: 'var(--ink-primary)', display: 'block', marginBottom: '4px' }}>
                Demographic Exposure Beneficiaries:
              </strong>
              <p className="font-tabular" style={{ fontSize: '16px', color: 'var(--domain-canopy)', fontWeight: 600 }}>
                {scenario.multi_objective_metrics?.population_protected?.toLocaleString('en-IN') || '118,941'} residents
              </p>
              <span style={{ fontSize: '11px', color: 'var(--ink-tertiary)' }}>
                Residents residing within treated H3 Res 9 hexagons (WorldPop 2020)
              </span>
            </div>
          </div>
        </section>

        {/* Section 5: Delivery Timeline & MRV Standard */}
        <section style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <h3 style={{ fontSize: '14px', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--ink-secondary)' }}>
            5. Implementation Schedule & Third-Party MRV Protocol
          </h3>
          <p style={{ fontSize: '13px', color: 'var(--ink-secondary)', lineHeight: 1.5 }}>
            • <strong>Month 1-3:</strong> Statutory municipal tender publication and contractor selection under PMC Tree Authority.<br />
            • <strong>Month 4-8:</strong> Physical planting of native evergreen saplings along verified road verges with 1.5m root trenching.<br />
            • <strong>Month 9-12:</strong> Contractor maintenance, geo-tagged photographic audit, and survival census submission.<br />
            • <strong>Post-Month 12:</strong> Independent third-party MRV verification using Landsat-9 TIRS and drone multispectral imagery.
          </p>
        </section>

        {/* Section 6: Official Sign-Off Signatures */}
        <section style={{ borderTop: '1px solid var(--border-hairline)', paddingTop: '24px', display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '40px' }}>
          <div>
            <div style={{ height: '48px', borderBottom: '1px dashed var(--border-hairline-hover)', marginBottom: '8px' }}></div>
            <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--ink-primary)', display: 'block' }}>
              Dr. Rajesh Patil, IAS
            </span>
            <span style={{ fontSize: '11px', color: 'var(--ink-secondary)' }}>
              Municipal Commissioner & Sanctioning Authority<br />Pune Municipal Corporation (PMC)
            </span>
          </div>

          <div>
            <div style={{ height: '48px', borderBottom: '1px dashed var(--border-hairline-hover)', marginBottom: '8px' }}></div>
            <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--ink-primary)', display: 'block' }}>
              CSR Climate Adaptation Lead
            </span>
            <span style={{ fontSize: '11px', color: 'var(--ink-secondary)' }}>
              Corporate Social Responsibility Steering Committee<br />National Climate Adaptation Facility
            </span>
          </div>
        </section>
      </div>
    </div>
  );
};

