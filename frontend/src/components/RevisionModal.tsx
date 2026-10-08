import React, { useState } from 'react';
import { climoraApi } from '../services/api';

interface RevisionModalProps {
  projectId: string;
  initialCellId?: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (revision: any) => void;
}

export const RevisionModal: React.FC<RevisionModalProps> = ({
  projectId,
  initialCellId = '',
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [cellId, setCellId] = useState(initialCellId);
  const [proposedQuantity, setProposedQuantity] = useState(80);
  const [author, setAuthor] = useState('Urban Planning Consultant');
  const [reason, setReason] = useState('Widened pedestrian sidewalk allows additional sapling density.');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const res = await climoraApi.proposeRevision(
        projectId,
        cellId,
        'street_tree_shade',
        proposedQuantity,
        reason,
        author
      );
      onSuccess(res.revision);
      onClose();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to submit proposal revision.');
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
            Proposal Branching
          </span>
          <h2 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--ink-primary)', marginTop: '2px' }}>
            Propose Allocation Revision
          </h2>
          <p style={{ fontSize: '12px', color: 'var(--ink-secondary)', marginTop: '4px' }}>
            Canonical allocation remains immutable. This branches an auditable alternative scenario for committee review.
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
              Target H3 Resolution 9 Cell
            </label>
            <input
              type="text"
              required
              value={cellId}
              onChange={(e) => setCellId(e.target.value)}
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
              Proposed Tree Quantity
            </label>
            <input
              type="number"
              required
              min={1}
              value={proposedQuantity}
              onChange={(e) => setProposedQuantity(Number(e.target.value))}
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
              Author / Technical Specialist
            </label>
            <input
              type="text"
              required
              value={author}
              onChange={(e) => setAuthor(e.target.value)}
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
              Justification & Engineering Rationale
            </label>
            <textarea
              rows={3}
              required
              value={reason}
              onChange={(e) => setReason(e.target.value)}
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
                backgroundColor: 'var(--truth-derived-ink)',
                border: 'none',
                borderRadius: '4px',
                fontSize: '13px',
                fontWeight: 600,
                color: '#121413',
              }}
            >
              {isLoading ? 'Submitting...' : 'Submit Revision'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
