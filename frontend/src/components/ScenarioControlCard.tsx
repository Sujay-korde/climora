import React, { useState } from 'react';
import { ScenarioOptimizeResponse } from '../types/api';

interface ScenarioControlCardProps {
  currentBudget: number;
  onBudgetChange: (budget: number) => void;
  onRunScenario: (budget: number) => void;
  isOptimizing: boolean;
  scenarioResult: ScenarioOptimizeResponse['data'] | null;
  onClearScenario: () => void;
  error: string | null;
  showScenarioOverlay: boolean;
  onToggleScenarioOverlay: () => void;
}

const PRESETS = [
  { label: '₹2.5M', value: 2500000 },
  { label: '₹5.0M', value: 5000000 },
  { label: '₹7.5M', value: 7500000 },
  { label: '₹10.0M', value: 10000000 },
];

export const ScenarioControlCard: React.FC<ScenarioControlCardProps> = ({
  currentBudget,
  onBudgetChange,
  onRunScenario,
  isOptimizing,
  scenarioResult,
  onClearScenario,
  error,
  showScenarioOverlay,
  onToggleScenarioOverlay,
}) => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [customInput, setCustomInput] = useState(currentBudget.toString());

  const handlePresetClick = (val: number) => {
    onBudgetChange(val);
    setCustomInput(val.toString());
    onRunScenario(val);
  };

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const parsed = parseInt(customInput.replace(/,/g, ''), 10);
    if (!isNaN(parsed) && parsed >= 500000 && parsed <= 25000000) {
      onBudgetChange(parsed);
      onRunScenario(parsed);
    }
  };

  return (
    <div
      style={{
        backgroundColor: 'var(--bg-panel)',
        border: '1px solid var(--border-hairline)',
        borderRadius: '8px',
        padding: '16px',
        width: '320px',
        maxWidth: 'calc(100vw - 40px)',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.45)',
        backdropFilter: 'blur(8px)',
        zIndex: 800,
        fontFamily: 'var(--font-sans)',
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: isCollapsed ? 0 : '14px' }}>
        <div>
          <span style={{ fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--ink-secondary)', display: 'block' }}>
            Decision Intelligence
          </span>
          <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--ink-primary)', margin: 0 }}>
            Scenario Optimization
          </h3>
        </div>
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--ink-secondary)',
            fontSize: '12px',
            cursor: 'pointer',
            padding: '4px',
          }}
          aria-label={isCollapsed ? 'Expand Scenario Panel' : 'Collapse Scenario Panel'}
        >
          {isCollapsed ? '+' : '—'}
        </button>
      </div>

      {!isCollapsed && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {/* Preset Buttons */}
          <div>
            <span style={{ fontSize: '11px', color: 'var(--ink-secondary)', display: 'block', marginBottom: '6px' }}>
              Select Scenario Budget (INR)
            </span>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '6px' }}>
              {PRESETS.map((p) => {
                const isSelected = currentBudget === p.value;
                return (
                  <button
                    key={p.value}
                    onClick={() => handlePresetClick(p.value)}
                    disabled={isOptimizing}
                    style={{
                      padding: '6px 4px',
                      fontSize: '11px',
                      fontWeight: isSelected ? 600 : 500,
                      fontFamily: 'var(--font-mono)',
                      borderRadius: '4px',
                      border: isSelected ? '1px solid #4CC9F0' : '1px solid var(--border-hairline)',
                      backgroundColor: isSelected ? 'rgba(76, 201, 240, 0.15)' : 'var(--bg-card)',
                      color: isSelected ? '#4CC9F0' : 'var(--ink-primary)',
                      cursor: isOptimizing ? 'not-allowed' : 'pointer',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    {p.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Custom Budget Form */}
          <form onSubmit={handleCustomSubmit} style={{ display: 'flex', gap: '6px' }}>
            <input
              type="number"
              min={500000}
              max={25000000}
              step={100000}
              value={customInput}
              onChange={(e) => setCustomInput(e.target.value)}
              disabled={isOptimizing}
              placeholder="e.g. 5000000"
              style={{
                flex: 1,
                padding: '6px 8px',
                fontSize: '12px',
                fontFamily: 'var(--font-mono)',
                backgroundColor: 'var(--bg-card)',
                border: '1px solid var(--border-hairline)',
                borderRadius: '4px',
                color: 'var(--ink-primary)',
              }}
            />
            <button
              type="submit"
              disabled={isOptimizing}
              style={{
                padding: '6px 12px',
                fontSize: '11px',
                fontWeight: 600,
                backgroundColor: 'var(--truth-modeled-border)',
                border: '1px solid var(--border-hairline)',
                borderRadius: '4px',
                color: 'var(--ink-primary)',
                cursor: isOptimizing ? 'not-allowed' : 'pointer',
              }}
            >
              {isOptimizing ? 'Solving...' : 'Run'}
            </button>
          </form>

          {/* Optimization State / Progress */}
          {isOptimizing && (
            <div
              style={{
                padding: '8px 12px',
                backgroundColor: 'rgba(76, 201, 240, 0.1)',
                border: '1px solid rgba(76, 201, 240, 0.3)',
                borderRadius: '4px',
                fontSize: '11px',
                color: '#4CC9F0',
                fontFamily: 'var(--font-mono)',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <span>●</span> Optimizing with HiGHS MILP (SciPy)...
            </div>
          )}

          {error && (
            <div
              style={{
                padding: '8px',
                backgroundColor: 'rgba(217, 107, 67, 0.15)',
                border: '1px solid var(--domain-thermal)',
                borderRadius: '4px',
                fontSize: '11px',
                color: 'var(--ink-primary)',
              }}
            >
              {error}
            </div>
          )}

          {/* Scenario Result Summary */}
          {scenarioResult && !isOptimizing && (
            <div
              style={{
                backgroundColor: 'var(--bg-card)',
                border: '1px solid rgba(76, 201, 240, 0.4)',
                borderRadius: '6px',
                padding: '12px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
                fontSize: '12px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '10px', textTransform: 'uppercase', color: '#4CC9F0', fontWeight: 600 }}>
                  Modeled Scenario Result
                </span>
                <span
                  style={{
                    fontSize: '9px',
                    padding: '2px 6px',
                    borderRadius: '2px',
                    backgroundColor: 'rgba(76, 201, 240, 0.2)',
                    color: '#4CC9F0',
                    fontFamily: 'var(--font-mono)',
                  }}
                >
                  {scenarioResult.solver_status}
                </span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', marginTop: '4px' }}>
                <div>
                  <span style={{ fontSize: '10px', color: 'var(--ink-tertiary)' }}>Modeled Cost</span>
                  <p className="font-tabular" style={{ fontWeight: 600, color: 'var(--ink-primary)', margin: 0 }}>
                    ₹{scenarioResult.total_allocated_cost_inr.toLocaleString('en-US')}
                  </p>
                </div>
                <div>
                  <span style={{ fontSize: '10px', color: 'var(--ink-tertiary)' }}>Treated Cells</span>
                  <p className="font-tabular" style={{ fontWeight: 600, color: 'var(--ink-primary)', margin: 0 }}>
                    {scenarioResult.total_cells_treated} H3 cells
                  </p>
                </div>
                <div>
                  <span style={{ fontSize: '10px', color: 'var(--ink-tertiary)' }}>Allocated Units</span>
                  <p className="font-tabular" style={{ fontWeight: 600, color: 'var(--ink-primary)', margin: 0 }}>
                    {scenarioResult.summary_by_intervention?.street_tree_shade?.total_quantity.toLocaleString('en-US') || 0} trees
                  </p>
                </div>
                <div>
                  <span style={{ fontSize: '10px', color: 'var(--ink-tertiary)' }}>Objective Score</span>
                  <p className="font-tabular" style={{ fontWeight: 600, color: 'var(--ink-primary)', margin: 0 }}>
                    {scenarioResult.optimal_objective_value.toFixed(4)}
                  </p>
                </div>
              </div>

              <div style={{ borderTop: '1px solid var(--border-hairline)', paddingTop: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: 'var(--ink-secondary)', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={showScenarioOverlay}
                    onChange={onToggleScenarioOverlay}
                  />
                  Show scenario overlay
                </label>
                <button
                  onClick={onClearScenario}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--ink-tertiary)',
                    fontSize: '11px',
                    cursor: 'pointer',
                    textDecoration: 'underline',
                  }}
                >
                  Clear
                </button>
              </div>
            </div>
          )}

          {/* Subtext explaining immutable separation */}
          <span style={{ fontSize: '10px', color: 'var(--ink-tertiary)', lineHeight: 1.4 }}>
            Simulation only. Does not modify canonical municipal project or allocation truth.
          </span>
        </div>
      )}
    </div>
  );
};
