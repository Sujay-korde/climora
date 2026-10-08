import React from 'react';
import { TruthLayer } from '../types/api';

interface TruthBadgeProps {
  layer: TruthLayer | string;
  detail?: string;
  size?: 'sm' | 'md';
}

export const TruthBadge: React.FC<TruthBadgeProps> = ({ layer, detail, size = 'sm' }) => {
  const norm = String(layer).toUpperCase().replace(/[\s-]/g, '_');

  let bg = 'var(--truth-unverified-bg)';
  let border = 'var(--truth-unverified-border)';
  let ink = 'var(--truth-unverified-ink)';
  let label = 'Not yet verified';

  if (norm.includes('OBSERVED')) {
    bg = 'var(--truth-observed-bg)';
    border = 'var(--truth-observed-border)';
    ink = 'var(--truth-observed-ink)';
    label = 'Observed';
  } else if (norm.includes('DERIVED')) {
    bg = 'var(--truth-derived-bg)';
    border = 'var(--truth-derived-border)';
    ink = 'var(--truth-derived-ink)';
    label = 'Derived';
  } else if (norm.includes('MODELED')) {
    bg = 'var(--truth-modeled-bg)';
    border = 'var(--truth-modeled-border)';
    ink = 'var(--truth-modeled-ink)';
    label = 'Modeled';
  } else if (norm === 'VERIFIED') {
    // Only if genuinely verified
    bg = 'rgba(59, 122, 87, 0.18)';
    border = 'rgba(59, 122, 87, 0.45)';
    ink = '#7BDCB5';
    label = 'Verified';
  }

  const isSmall = size === 'sm';

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        backgroundColor: bg,
        border: `1px solid ${border}`,
        color: ink,
        fontFamily: 'var(--font-mono)',
        fontSize: isSmall ? '10px' : '11px',
        padding: isSmall ? '2px 6px' : '3px 8px',
        borderRadius: '3px',
        letterSpacing: '0.03em',
        lineHeight: 1,
        whiteSpace: 'nowrap',
      }}
      title={detail ? `${label}: ${detail}` : label}
    >
      <span>{label}</span>
      {detail && (
        <span style={{ opacity: 0.7, borderLeft: `1px solid ${border}`, paddingLeft: '6px' }}>
          {detail}
        </span>
      )}
    </span>
  );
};
