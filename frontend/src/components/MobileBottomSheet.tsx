import React, { useState } from 'react';
import { TruthBadge } from './TruthBadge';
import { AllocationItem, BaselineCell } from '../types/api';

interface MobileBottomSheetProps {
  cellId: string;
  allocation?: AllocationItem;
  baseline?: BaselineCell;
  onClose: () => void;
  onOpenProvenance: () => void;
}

export const MobileBottomSheet: React.FC<MobileBottomSheetProps> = ({
  cellId,
  allocation,
  baseline,
  onClose,
  onOpenProvenance,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const metrics = baseline?.metrics;
  const lst = metrics?.lst_2025?.value;
  const trees = allocation?.planned_quantity;
  const cost = allocation?.total_modeled_cost;
  const pop = metrics?.population_2020?.value;
  const risk = metrics?.risk_i?.value;

  return (
    <div
      style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        height: isExpanded ? '80vh' : '96px',
        backgroundColor: 'var(--bg-panel)',
        borderTop: '1px solid var(--border-hairline)',
        borderTopLeftRadius: '12px',
        borderTopRightRadius: '12px',
        boxShadow: '0 -8px 32px rgba(0, 0, 0, 0.6)',
        zIndex: 1000,
        transition: 'height 0.25s ease',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
      role="region"
      aria-label="Mobile Cell Inspection Sheet"
    >
      {/* Grab handle & Collapsed Header */}
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        style={{
          padding: '10px 16px',
          cursor: 'pointer',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '6px',
          backgroundColor: 'var(--bg-card)',
          borderBottom: isExpanded ? '1px solid var(--border-hairline)' : 'none',
        }}
      >
        <div style={{ width: '36px', height: '4px', backgroundColor: 'var(--border-hairline-hover)', borderRadius: '2px' }} />
        <div style={{ width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <span className="font-tabular" style={{ fontSize: '13px', fontWeight: 600, color: 'var(--ink-primary)' }}>
              {cellId}
            </span>
            <span style={{ fontSize: '11px', color: 'var(--ink-secondary)', marginLeft: '8px' }}>
              {lst !== undefined ? `${lst}°C` : '—'}
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="font-tabular" style={{ fontSize: '12px', fontWeight: 500, color: 'var(--truth-modeled-ink)' }}>
              {trees !== undefined ? `${trees} trees` : 'Unallocated'}
            </span>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onClose();
              }}
              style={{ fontSize: '14px', color: 'var(--ink-tertiary)', padding: '2px 6px' }}
              aria-label="Dismiss sheet"
            >
              ✕
            </button>
          </div>
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div style={{ padding: '20px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <span style={{ fontSize: '11px', color: 'var(--ink-secondary)' }}>Modeled Capital</span>
              <p className="font-tabular" style={{ fontSize: '18px', fontWeight: 600, color: 'var(--ink-primary)' }}>
                {cost !== undefined ? `₹${cost.toLocaleString('en-US')}` : '—'}
              </p>
            </div>
            <TruthBadge layer="MODELED" />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', borderTop: '1px solid var(--border-hairline)', paddingTop: '12px' }}>
            <div>
              <span style={{ fontSize: '11px', color: 'var(--ink-secondary)' }}>In-scope population</span>
              <p className="font-tabular" style={{ fontSize: '14px', fontWeight: 500, color: 'var(--ink-primary)' }}>
                {pop !== undefined ? `${Math.round(pop).toLocaleString('en-US')}` : '—'}
              </p>
            </div>
            <div>
              <span style={{ fontSize: '11px', color: 'var(--ink-secondary)' }}>Climate risk (F-22)</span>
              <p className="font-tabular" style={{ fontSize: '14px', fontWeight: 500, color: 'var(--ink-primary)' }}>
                {risk !== undefined ? risk.toFixed(4) : '—'}
              </p>
            </div>
          </div>

          <div style={{ borderTop: '1px solid var(--border-hairline)', paddingTop: '12px' }}>
            <span style={{ fontSize: '11px', color: 'var(--ink-secondary)' }}>Biophysical Evidence</span>
            <div style={{ marginTop: '8px', fontSize: '12px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--ink-secondary)' }}>Baseline Mean LST:</span>
                <span className="font-tabular">{metrics?.lst_baseline_mean?.value}°C</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--ink-secondary)' }}>Thermal Anomaly:</span>
                <span className="font-tabular">+{metrics?.lst_anomaly_absolute?.value}°C</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--ink-secondary)' }}>Vegetation (NDVI):</span>
                <span className="font-tabular">{metrics?.ndvi_2025?.value?.toFixed(4)}</span>
              </div>
            </div>
          </div>

          <button
            onClick={onOpenProvenance}
            style={{
              marginTop: '8px',
              fontSize: '12px',
              color: 'var(--truth-derived-ink)',
              textDecoration: 'underline',
              textAlign: 'left',
            }}
          >
            View technical provenance →
          </button>
        </div>
      )}
    </div>
  );
};
