import React from 'react';

export type LayerMode = 'thermal' | 'exposure' | 'risk';

interface MapControlsProps {
  activeLayer: LayerMode;
  onLayerChange: (layer: LayerMode) => void;
  showFootprint: boolean;
  onToggleFootprint: () => void;
  onToggleTableView: () => void;
  isTableView: boolean;
}

export const MapControls: React.FC<MapControlsProps> = ({
  activeLayer,
  onLayerChange,
  showFootprint,
  onToggleFootprint,
  onToggleTableView,
  isTableView,
}) => {
  return (
    <div
      style={{
        backgroundColor: 'var(--bg-panel)',
        border: '1px solid var(--border-hairline)',
        borderRadius: '6px',
        padding: '16px',
        width: '220px',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.35)',
        display: 'flex',
        flexDirection: 'column',
        gap: '14px',
      }}
      role="region"
      aria-label="Map Layer Controls"
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '11px', color: 'var(--ink-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Active Metric
        </span>
        <button
          onClick={onToggleTableView}
          style={{
            fontSize: '11px',
            fontFamily: 'var(--font-mono)',
            padding: '2px 6px',
            backgroundColor: isTableView ? 'var(--bg-elevated)' : 'transparent',
            border: '1px solid var(--border-hairline)',
            borderRadius: '3px',
            color: isTableView ? 'var(--accent-focal)' : 'var(--ink-secondary)',
          }}
          title="Press Alt+T to toggle accessible table"
        >
          {isTableView ? 'Map View' : 'Alt+T: Table'}
        </button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <label
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '13px',
            color: activeLayer === 'thermal' ? 'var(--ink-primary)' : 'var(--ink-secondary)',
            cursor: 'pointer',
          }}
        >
          <input
            type="radio"
            name="layer_mode"
            checked={activeLayer === 'thermal'}
            onChange={() => onLayerChange('thermal')}
            style={{ accentColor: 'var(--domain-thermal)' }}
          />
          Thermal (LST 2025)
        </label>

        <label
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '13px',
            color: activeLayer === 'exposure' ? 'var(--ink-primary)' : 'var(--ink-secondary)',
            cursor: 'pointer',
          }}
        >
          <input
            type="radio"
            name="layer_mode"
            checked={activeLayer === 'exposure'}
            onChange={() => onLayerChange('exposure')}
            style={{ accentColor: 'var(--domain-hydrology)' }}
          />
          Exposure (WorldPop)
        </label>

        <label
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '13px',
            color: activeLayer === 'risk' ? 'var(--ink-primary)' : 'var(--ink-secondary)',
            cursor: 'pointer',
          }}
        >
          <input
            type="radio"
            name="layer_mode"
            checked={activeLayer === 'risk'}
            onChange={() => onLayerChange('risk')}
            style={{ accentColor: 'var(--truth-modeled-ink)' }}
          />
          Risk Surface (F-22)
        </label>
      </div>

      <div style={{ borderTop: '1px solid var(--border-hairline)', paddingTop: '10px' }}>
        <label
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '12px',
            color: showFootprint ? 'var(--ink-primary)' : 'var(--ink-secondary)',
            cursor: 'pointer',
          }}
        >
          <input
            type="checkbox"
            checked={showFootprint}
            onChange={onToggleFootprint}
            style={{ accentColor: 'var(--domain-canopy)' }}
          />
          Project Footprint (28 Cells)
        </label>
      </div>
    </div>
  );
};
