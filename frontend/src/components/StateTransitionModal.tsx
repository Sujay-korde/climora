import React, { useState } from 'react';
import { climoraApi } from '../services/api';

interface StateTransitionModalProps {
  projectId: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (targetState: string) => void;
}

export const StateTransitionModal: React.FC<StateTransitionModalProps> = ({
  projectId,
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [sanctionId, setSanctionId] = useState('PMC-RESILIENCE-2025-084');
  const [approvedBudget, setApprovedBudget] = useState(10000000);
  const [notes, setNotes] = useState('Standing Committee resolution for pre-monsoon street canopy deployment.');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg(null);
    try {
      await climoraApi.transitionState(
        projectId,
        'FUNDED',
        sanctionId,
        approvedBudget,
        notes
      );
      onSuccess('FUNDED');
      onClose();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to sanction project.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'var(--bg-overlay)',
        backdropFilter: 'blur(4px)',
        zIndex: 1200,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px',
      }}
      role="dialog"
      aria-modal="true"
    >
      <div
        style={{
          backgroundColor: 'var(--bg-panel)',
          border: '1px solid var(--border-hairline-hover)',
          borderRadius: '8px',
          width: '500px',
          maxWidth: '100%',
          boxShadow: '0 16px 48px rgba(0, 0, 0, 0.6)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--border-hairline)' }}>
          <span style={{ fontSize: '11px', color: 'var(--ink-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Municipal Sanction Order
          </span>
          <h2 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--ink-primary)', marginTop: '2px' }}>
            Sanction Project & Issue Tender
          </h2>
          <p style={{ fontSize: '12px', color: 'var(--ink-secondary)', marginTop: '4px' }}>
            Transitions project state from <strong>PROPOSED</strong> to <strong>FUNDED</strong> in compliance with PMC procurement guidelines.
          </p>
        </div>

        <form onSubmit={handleSubmit} style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {errorMsg && (
            <div style={{ padding: '10px 12px', backgroundColor: 'rgba(217, 107, 67, 0.15)', border: '1px solid var(--domain-thermal)', borderRadius: '4px', fontSize: '12px', color: 'var(--ink-primary)' }}>
              {errorMsg}
            </div>
          )}

          <div>
            <label style={{ fontSize: '12px', color: 'var(--ink-secondary)', display: 'block', marginBottom: '6px' }}>
              Sanction Order Identifier
            </label>
            <input
              type="text"
              required
              value={sanctionId}
              onChange={(e) => setSanctionId(e.target.value)}
              className="font-tabular"
              style={{
                width: '100%',
                padding: '8px 12px',
                backgroundColor: 'var(--bg-card)',
                border: '1px solid var(--border-hairline)',
                borderRadius: '4px',
                color: 'var(--ink-primary)',
                fontSize: '13px',
              }}
            />
          </div>

          <div>
            <label style={{ fontSize: '12px', color: 'var(--ink-secondary)', display: 'block', marginBottom: '6px' }}>
              Approved Statutory Budget (INR)
            </label>
            <input
              type="number"
              required
              min={1000000}
              value={approvedBudget}
              onChange={(e) => setApprovedBudget(Number(e.target.value))}
              className="font-tabular"
              style={{
                width: '100%',
                padding: '8px 12px',
                backgroundColor: 'var(--bg-card)',
                border: '1px solid var(--border-hairline)',
                borderRadius: '4px',
                color: 'var(--ink-primary)',
                fontSize: '13px',
              }}
            />
          </div>

          <div>
            <label style={{ fontSize: '12px', color: 'var(--ink-secondary)', display: 'block', marginBottom: '6px' }}>
              Committee Resolution Notes
            </label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px',
                backgroundColor: 'var(--bg-card)',
                border: '1px solid var(--border-hairline)',
                borderRadius: '4px',
                color: 'var(--ink-primary)',
                fontSize: '12px',
                resize: 'none',
              }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '8px' }}>
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              style={{
                padding: '8px 16px',
                backgroundColor: 'transparent',
                border: '1px solid var(--border-hairline)',
                borderRadius: '4px',
                fontSize: '13px',
                color: 'var(--ink-secondary)',
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              style={{
                padding: '8px 18px',
                backgroundColor: 'var(--truth-modeled-ink)',
                border: 'none',
                borderRadius: '4px',
                fontSize: '13px',
                fontWeight: 600,
                color: '#121413',
              }}
            >
              {isLoading ? 'Sanctioning...' : 'Sanction Project'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
