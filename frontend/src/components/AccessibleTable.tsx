import React from 'react';
import { TruthBadge } from './TruthBadge';
import { AllocationItem, BaselineCell } from '../types/api';

interface AccessibleTableProps {
  cells: BaselineCell[];
  allocations: AllocationItem[];
  selectedCellId: string | null;
  onSelectCell: (cellId: string) => void;
  onReturnToMap: () => void;
}

export const AccessibleTable: React.FC<AccessibleTableProps> = ({
  cells,
  allocations,
  selectedCellId,
  onSelectCell,
  onReturnToMap,
}) => {
  const allocMap = new Map(allocations.map((a) => [a.h3_cell_id, a]));

  return (
    <div
      style={{
        padding: '32px',
        backgroundColor: 'var(--bg-ground)',
        minHeight: 'calc(100vh - var(--nav-height))',
        display: 'flex',
        flexDirection: 'column',
        gap: '20px',
      }}
      role="region"
      aria-label="Accessible Spatial Data Table"
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <span style={{ fontSize: '11px', color: 'var(--ink-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            Accessible Alternative Representation
          </span>
          <h1 style={{ fontSize: '20px', fontWeight: 600, color: 'var(--ink-primary)', marginTop: '4px' }}>
            Pune Prioritized Cells Ledger
          </h1>
          <p style={{ fontSize: '13px', color: 'var(--ink-secondary)', marginTop: '2px' }}>
            Full semantic data equivalence for screen-reader and keyboard navigation.
          </p>
        </div>

        <button
          onClick={onReturnToMap}
          style={{
            padding: '8px 16px',
            backgroundColor: 'var(--bg-elevated)',
            border: '1px solid var(--border-hairline)',
            borderRadius: '4px',
            fontSize: '13px',
            fontWeight: 500,
            color: 'var(--ink-primary)',
          }}
          title="Return to spatial map view"
        >
          Return to Spatial Map View (Alt+T)
        </button>
      </div>

      <div style={{ overflowX: 'auto', border: '1px solid var(--border-hairline)', borderRadius: '6px' }}>
        <table
          style={{
            width: '100%',
            borderCollapse: 'collapse',
            textAlign: 'left',
            fontSize: '13px',
            backgroundColor: 'var(--bg-panel)',
          }}
        >
          <caption style={{ textAlign: 'left', padding: '12px 16px', color: 'var(--ink-secondary)', fontSize: '12px', borderBottom: '1px solid var(--border-hairline)' }}>
            Authoritative municipal decision dataset across canonical H3 Resolution 9 cells in Pune.
          </caption>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-hairline)', color: 'var(--ink-secondary)', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              <th scope="col" style={{ padding: '12px 16px' }}>H3 Cell ID</th>
              <th scope="col" style={{ padding: '12px 16px' }}>Surface Temp (2025)</th>
              <th scope="col" style={{ padding: '12px 16px' }}>Baseline Mean LST</th>
              <th scope="col" style={{ padding: '12px 16px' }}>Thermal Anomaly</th>
              <th scope="col" style={{ padding: '12px 16px' }}>Risk Score (F-22)</th>
              <th scope="col" style={{ padding: '12px 16px' }}>Population (2020)</th>
              <th scope="col" style={{ padding: '12px 16px' }}>Proposed Trees</th>
              <th scope="col" style={{ padding: '12px 16px' }}>Total Cost (INR)</th>
              <th scope="col" style={{ padding: '12px 16px' }}>Truth Layer</th>
              <th scope="col" style={{ padding: '12px 16px' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {cells.map((cell) => {
              const isSelected = cell.h3_cell_id === selectedCellId;
              const alloc = allocMap.get(cell.h3_cell_id);
              const m = cell.metrics;

              return (
                <tr
                  key={cell.h3_cell_id}
                  style={{
                    borderBottom: '1px solid var(--border-hairline-subtle)',
                    backgroundColor: isSelected ? 'var(--bg-elevated)' : 'transparent',
                    transition: 'background-color 0.1s ease',
                  }}
                >
                  <th
                    scope="row"
                    className="font-tabular"
                    style={{
                      padding: '12px 16px',
                      fontWeight: 600,
                      color: isSelected ? 'var(--accent-focal)' : 'var(--ink-primary)',
                    }}
                  >
                    {cell.h3_cell_id}
                  </th>
                  <td className="font-tabular" style={{ padding: '12px 16px' }}>
                    {m?.lst_2025?.value !== undefined ? `${m.lst_2025.value}°C` : '—'}
                  </td>
                  <td className="font-tabular" style={{ padding: '12px 16px', color: 'var(--ink-secondary)' }}>
                    {m?.lst_baseline_mean?.value !== undefined ? `${m.lst_baseline_mean.value}°C` : '—'}
                  </td>
                  <td className="font-tabular" style={{ padding: '12px 16px', color: 'var(--ink-secondary)' }}>
                    {m?.lst_anomaly_absolute?.value !== undefined ? `+${m.lst_anomaly_absolute.value}°C` : '—'}
                  </td>
                  <td className="font-tabular" style={{ padding: '12px 16px' }}>
                    {m?.risk_i?.value !== undefined ? m.risk_i.value.toFixed(4) : '—'}
                  </td>
                  <td className="font-tabular" style={{ padding: '12px 16px' }}>
                    {m?.population_2020?.value !== undefined ? Math.round(m.population_2020.value).toLocaleString('en-US') : '—'}
                  </td>
                  <td className="font-tabular" style={{ padding: '12px 16px', fontWeight: 500 }}>
                    {alloc?.planned_quantity !== undefined ? `${alloc.planned_quantity} trees` : '—'}
                  </td>
                  <td className="font-tabular" style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--truth-modeled-ink)' }}>
                    {alloc?.total_modeled_cost !== undefined ? `₹${alloc.total_modeled_cost.toLocaleString('en-US')}` : '—'}
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <TruthBadge layer={alloc ? 'MODELED' : 'OBSERVED'} />
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <button
                      onClick={() => onSelectCell(cell.h3_cell_id)}
                      style={{
                        padding: '4px 8px',
                        backgroundColor: 'var(--bg-card)',
                        border: '1px solid var(--border-hairline)',
                        borderRadius: '3px',
                        fontSize: '11px',
                        color: 'var(--ink-primary)',
                      }}
                      aria-label={`Inspect cell ${cell.h3_cell_id}`}
                    >
                      {isSelected ? 'Selected' : 'Inspect'}
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
