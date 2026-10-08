import React, { useEffect, useState } from 'react';
import { TruthBadge } from './TruthBadge';
import { AllocationItem, BaselineCell, RiskSurfaceCell, ScenarioAllocationItem } from '../types/api';

interface CellInspectorProps {
  cellId: string;
  allocation?: AllocationItem;
  baseline?: BaselineCell;
  riskCell?: RiskSurfaceCell;
  scenarioAllocation?: ScenarioAllocationItem;
  isOpen: boolean;
  onClose: () => void;
  onOpenProvenance: () => void;
}

export const CellInspector: React.FC<CellInspectorProps> = ({
  cellId,
  allocation,
  baseline,
  riskCell,
  scenarioAllocation,
  isOpen,
  onClose,
  onOpenProvenance,
}) => {
  const [showMethodology, setShowMethodology] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  // Extract metrics from riskCell or baseline fallback
  const lst = riskCell?.lst_2025 ?? baseline?.metrics?.lst_2025?.value;
  const anomaly = riskCell?.lst_anomaly ?? baseline?.metrics?.lst_anomaly_absolute?.value;
  const risk = riskCell?.risk_i ?? baseline?.metrics?.risk_i?.value;
  const pop = riskCell?.population_2020 ?? baseline?.metrics?.population_2020?.value;
  const H_i = riskCell?.H_i ?? baseline?.metrics?.H_i?.value;
  const E_i = riskCell?.E_i ?? baseline?.metrics?.E_i?.value;
  const V_i = riskCell?.V_i ?? baseline?.metrics?.V_i?.value;
  const lisa = riskCell?.lisa_cluster ?? baseline?.metrics?.lisa_cluster?.value;

  const canonTrees = allocation?.planned_quantity;
  const canonCost = allocation?.total_modeled_cost;

  const scenTrees = scenarioAllocation?.quantity;
  const scenCost = scenarioAllocation?.total_cost;
  const scenCooling = scenarioAllocation?.modeled_cooling_degC;

  return (
    <aside
      style={{
        position: 'fixed',
        top: 'var(--nav-height)',
        right: 0,
        bottom: 0,
        width: 'var(--inspector-width)',
        maxWidth: '100vw',
        backgroundColor: 'var(--bg-panel)',
        borderLeft: '1px solid var(--border-hairline)',
        boxShadow: '-8px 0 32px rgba(0, 0, 0, 0.5)',
        zIndex: 900,
        display: 'flex',
        flexDirection: 'column',
        overflowY: 'auto',
      }}
      aria-label={`Cell Inspector for ${cellId}`}
      role="dialog"
      aria-modal="true"
    >
      {/* Drawer Header */}
      <div
        style={{
          padding: '20px 24px',
          borderBottom: '1px solid var(--border-hairline)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          position: 'sticky',
          top: 0,
          backgroundColor: 'var(--bg-panel)',
          zIndex: 10,
        }}
      >
        <div>
          <span style={{ fontSize: '11px', color: 'var(--ink-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            Selected Analytical Unit
          </span>
          <h2 style={{ fontSize: '16px', fontWeight: 500, color: 'var(--ink-primary)' }}>
            Cell Evidence Drilldown
          </h2>
        </div>
        <button
          onClick={onClose}
          style={{
            padding: '6px 10px',
            backgroundColor: 'var(--bg-card)',
            border: '1px solid var(--border-hairline)',
            borderRadius: '4px',
            fontSize: '12px',
            color: 'var(--ink-secondary)',
          }}
          aria-label="Close Inspector"
        >
          Close (ESC)
        </button>
      </div>

      <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {/* Cell Identity */}
        <div>
          <span style={{ fontSize: '11px', color: 'var(--ink-secondary)' }}>H3 cell index</span>
          <p className="font-tabular" style={{ fontSize: '14px', fontWeight: 600, color: 'var(--ink-primary)' }}>
            {cellId}
          </p>
          <span style={{ fontSize: '11px', color: 'var(--ink-tertiary)' }}>9.86 hectares (Resolution 9 mesh)</span>
        </div>

        {/* Core Decision Metrics */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', borderTop: '1px solid var(--border-hairline)', paddingTop: '16px' }}>
          <div>
            <span style={{ fontSize: '11px', color: 'var(--ink-secondary)' }}>Surface temperature</span>
            <p className="font-tabular" style={{ fontSize: '20px', fontWeight: 600, color: 'var(--ink-primary)' }}>
              {lst !== undefined ? `${lst}°C` : '—'}
            </p>
            <span style={{ fontSize: '10px', color: 'var(--ink-tertiary)', display: 'block', marginTop: '2px' }}>
              Observed · Landsat 8 (2025)
            </span>
          </div>

          <div>
            <span style={{ fontSize: '11px', color: 'var(--ink-secondary)' }}>Climate risk score</span>
            <p className="font-tabular" style={{ fontSize: '20px', fontWeight: 600, color: 'var(--ink-primary)' }}>
              {risk !== undefined ? (typeof risk === 'number' ? risk.toFixed(4) : risk) : '—'}
            </p>
            <span style={{ fontSize: '10px', color: 'var(--ink-tertiary)', display: 'block', marginTop: '2px' }}>
              Modeled · F-22 (H × E × V)
            </span>
          </div>
        </div>

        {/* HEV Sub-component Breakdown */}
        <div style={{ borderTop: '1px solid var(--border-hairline)', paddingTop: '14px' }}>
          <span style={{ fontSize: '11px', color: 'var(--ink-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            HEV Risk Formulation Components
          </span>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px', marginTop: '8px' }}>
            <div style={{ backgroundColor: 'var(--bg-card)', padding: '8px', borderRadius: '4px', border: '1px solid var(--border-hairline)' }}>
              <span style={{ fontSize: '10px', color: 'var(--ink-tertiary)' }}>Hazard (H)</span>
              <p className="font-tabular" style={{ fontSize: '14px', fontWeight: 600, color: 'var(--ink-primary)' }}>
                {H_i !== undefined ? (typeof H_i === 'number' ? H_i.toFixed(3) : H_i) : '—'}
              </p>
            </div>
            <div style={{ backgroundColor: 'var(--bg-card)', padding: '8px', borderRadius: '4px', border: '1px solid var(--border-hairline)' }}>
              <span style={{ fontSize: '10px', color: 'var(--ink-tertiary)' }}>Exposure (E)</span>
              <p className="font-tabular" style={{ fontSize: '14px', fontWeight: 600, color: 'var(--ink-primary)' }}>
                {E_i !== undefined ? (typeof E_i === 'number' ? E_i.toFixed(3) : E_i) : '—'}
              </p>
            </div>
            <div style={{ backgroundColor: 'var(--bg-card)', padding: '8px', borderRadius: '4px', border: '1px solid var(--border-hairline)' }}>
              <span style={{ fontSize: '10px', color: 'var(--ink-tertiary)' }}>Susceptibility (V)</span>
              <p className="font-tabular" style={{ fontSize: '14px', fontWeight: 600, color: 'var(--ink-primary)' }}>
                {V_i !== undefined ? (typeof V_i === 'number' ? V_i.toFixed(3) : V_i) : '—'}
              </p>
            </div>
          </div>
        </div>

        {/* Population within cell */}
        <div style={{ borderTop: '1px solid var(--border-hairline)', paddingTop: '14px' }}>
          <span style={{ fontSize: '11px', color: 'var(--ink-secondary)' }}>In-scope population</span>
          <p className="font-tabular" style={{ fontSize: '16px', fontWeight: 500, color: 'var(--ink-primary)' }}>
            {pop !== undefined ? `${Math.round(pop).toLocaleString('en-US')} residents` : '—'}
          </p>
          <span style={{ fontSize: '10px', color: 'var(--ink-tertiary)' }}>
            Observed · WorldPop 2020 dasymetric
          </span>
        </div>

        {/* Canonical Municipal Allocation Card */}
        <div style={{ backgroundColor: 'var(--bg-card)', border: '1px solid rgba(59, 122, 87, 0.4)', borderRadius: '6px', padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '11px', color: '#3B7A57', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Canonical Municipal Allocation
            </span>
            <TruthBadge layer="MODELED" />
          </div>
          <div style={{ marginTop: '8px' }}>
            <p className="font-tabular" style={{ fontSize: '18px', fontWeight: 600, color: 'var(--ink-primary)' }}>
              {canonTrees !== undefined ? `${canonTrees} street trees` : 'Not prioritized in canonical plan'}
            </p>
            <span style={{ fontSize: '11px', color: 'var(--ink-secondary)' }}>
              Modeled · 15.0m roadside interval
            </span>
          </div>
          {canonCost !== undefined && (
            <div style={{ marginTop: '12px', borderTop: '1px solid var(--border-hairline)', paddingTop: '10px' }}>
              <p className="font-tabular" style={{ fontSize: '16px', fontWeight: 600, color: 'var(--truth-modeled-ink)', margin: 0 }}>
                ₹{canonCost.toLocaleString('en-US')}
              </p>
              <span style={{ fontSize: '10px', color: 'var(--ink-secondary)' }}>
                Modeled capital requirement (planting + mobilization)
              </span>
            </div>
          )}
        </div>

        {/* Dynamic Scenario Allocation Card */}
        {scenarioAllocation && (
          <div style={{ backgroundColor: 'var(--bg-card)', border: '1px solid rgba(76, 201, 240, 0.5)', borderRadius: '6px', padding: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '11px', color: '#4CC9F0', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Active Scenario Allocation
              </span>
              <TruthBadge layer="MODELED" />
            </div>
            <div style={{ marginTop: '8px' }}>
              <p className="font-tabular" style={{ fontSize: '16px', fontWeight: 600, color: 'var(--ink-primary)' }}>
                {scenTrees !== undefined ? `${scenTrees} street trees` : 'Unallocated in scenario'}
              </p>
              {scenCost !== undefined && (
                <span className="font-tabular" style={{ fontSize: '12px', color: 'var(--ink-secondary)', display: 'block', marginTop: '2px' }}>
                  Scenario cost: ₹{scenCost.toLocaleString('en-US')}
                </span>
              )}
              {scenCooling !== undefined && scenCooling > 0 && (
                <span className="font-tabular" style={{ fontSize: '11px', color: '#4CC9F0', display: 'block', marginTop: '2px' }}>
                  Modeled cooling impact: ~{scenCooling.toFixed(3)}°C
                </span>
              )}
            </div>
          </div>
        )}

        {/* Biophysical & Spatial Evidence */}
        <div style={{ borderTop: '1px solid var(--border-hairline)', paddingTop: '16px' }}>
          <h3 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--ink-primary)', marginBottom: '12px' }}>
            Biophysical & Spatial Evidence
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ color: 'var(--ink-secondary)' }}>Thermal anomaly</span>
              <span className="font-tabular" style={{ color: 'var(--ink-primary)', fontWeight: 500 }}>
                {anomaly !== undefined ? `${anomaly > 0 ? '+' : ''}${anomaly.toFixed(2)}°C` : '—'}
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ color: 'var(--ink-secondary)' }}>LISA hotspot cluster</span>
              <span className="font-tabular" style={{ color: 'var(--ink-primary)', fontWeight: 500 }}>
                {lisa || 'Not Significant'}
              </span>
            </div>
          </div>
        </div>

        {/* Methodology Accordion */}
        <div style={{ borderTop: '1px solid var(--border-hairline)', paddingTop: '16px' }}>
          <button
            onClick={() => setShowMethodology(!showMethodology)}
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              width: '100%',
              fontSize: '12px',
              color: 'var(--ink-secondary)',
            }}
          >
            <span>{showMethodology ? 'Hide methodology' : 'Expand methodology +'}</span>
          </button>

          {showMethodology && (
            <div style={{ marginTop: '12px', padding: '12px', backgroundColor: 'var(--bg-card)', borderRadius: '4px', fontSize: '11px', color: 'var(--ink-secondary)', lineHeight: 1.6 }}>
              <p>• <strong>Formulation:</strong> F-24.6 Budget-Constrained Mixed-Integer Linear Program.</p>
              <p style={{ marginTop: '4px' }}>• <strong>Solver:</strong> SciPy HiGHS branch-and-cut optimization backend.</p>
              <p style={{ marginTop: '4px' }}>• <strong>Cost basis:</strong> ₹3,500/tree procurement & 2m guard + ₹20,000/cell mobilization overhead.</p>
              <p style={{ marginTop: '4px' }}>• <strong>Thermodynamic cap:</strong> 4.0°C maximum localized intra-cell cooling (F-25.1).</p>
            </div>
          )}
        </div>

        {/* Forensic Link */}
        <div style={{ borderTop: '1px solid var(--border-hairline)', paddingTop: '16px' }}>
          <button
            onClick={onOpenProvenance}
            style={{
              fontSize: '12px',
              color: 'var(--truth-derived-ink)',
              textDecoration: 'underline',
              cursor: 'pointer',
            }}
          >
            View technical provenance →
          </button>
        </div>
      </div>
    </aside>
  );
};
