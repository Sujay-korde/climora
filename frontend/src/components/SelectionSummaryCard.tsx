import React from 'react';
import { TruthBadge } from './TruthBadge';
import { AllocationItem, BaselineCell } from '../types/api';

interface SelectionSummaryCardProps {
  cellId: string;
  allocation?: AllocationItem;
  baseline?: BaselineCell;
  onOpenInspector: () => void;
  onClose: () => void;
}

export const SelectionSummaryCard: React.FC<SelectionSummaryCardProps> = ({
  cellId,
  allocation,
  baseline,
  onOpenInspector,
  onClose,
}) => {
  const lst = baseline?.metrics?.lst_2025?.value;
  const trees = allocation?.planned_quantity;
  const cost = allocation?.total_modeled_cost;

  return (
    <div
      style={{
        backgroundColor: 'var(--bg-panel)',
        border: '1px solid var(--border-hairline-hover)',
        borderRadius: '6px',
        padding: '16px',
        width: '280px',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.4)',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
      }}
      role="region"
      aria-label="Selected Cell Summary"
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <span style={{ fontSize: '11px', color: 'var(--ink-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Selected Cell
          </span>
          <p className="font-tabular" style={{ fontSize: '13px', fontWeight: 500, color: 'var(--ink-primary)', marginTop: '2px' }}>
            {cellId}
          </p>
        </div>
        <button
          onClick={onClose}
          aria-label="Close summary card"
          style={{
            color: 'var(--ink-tertiary)',
            fontSize: '16px',
            lineHeight: 1,
            padding: '2px 4px',
          }}
        >
          ✕
        </button>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border-hairline)', paddingTop: '10px' }}>
        <div>
          <span style={{ fontSize: '11px', color: 'var(--ink-secondary)' }}>Surface temp</span>
          <p className="font-tabular" style={{ fontSize: '16px', fontWeight: 600, color: 'var(--ink-primary)' }}>
            {lst !== undefined ? `${lst}°C` : '—'}
          </p>
        </div>
        <TruthBadge layer="OBSERVED" />
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border-hairline)', paddingTop: '10px' }}>
        <div>
          <span style={{ fontSize: '11px', color: 'var(--ink-secondary)' }}>Intervention</span>
          <p className="font-tabular" style={{ fontSize: '14px', fontWeight: 500, color: 'var(--ink-primary)' }}>
            {trees !== undefined ? `${trees} trees · ₹${cost?.toLocaleString('en-US')}` : 'Unallocated'}
          </p>
        </div>
        <TruthBadge layer="MODELED" />
      </div>

      <button
        onClick={onOpenInspector}
        style={{
          marginTop: '4px',
          padding: '8px 12px',
          backgroundColor: 'var(--bg-elevated)',
          border: '1px solid var(--border-hairline)',
          borderRadius: '4px',
          color: 'var(--ink-primary)',
          fontSize: '12px',
          fontWeight: 500,
          textAlign: 'center',
          transition: 'background-color 0.15s ease',
        }}
      >
        View details →
      </button>
    </div>
  );
};
