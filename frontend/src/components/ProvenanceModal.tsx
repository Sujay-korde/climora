import React, { useEffect } from 'react';

interface ProvenanceModalProps {
  isOpen: boolean;
  onClose: () => void;
  provenanceData?: Record<string, any>;
}

export const ProvenanceModal: React.FC<ProvenanceModalProps> = ({
  isOpen,
  onClose,
  provenanceData,
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

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
      aria-labelledby="provenance-title"
    >
      <div
        style={{
          backgroundColor: 'var(--bg-panel)',
          border: '1px solid var(--border-hairline-hover)',
          borderRadius: '8px',
          width: '680px',
          maxWidth: '100%',
          maxHeight: '85vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 16px 48px rgba(0, 0, 0, 0.6)',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            padding: '20px 24px',
            borderBottom: '1px solid var(--border-hairline)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <span style={{ fontSize: '11px', color: 'var(--ink-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              Level D Disclosure
            </span>
            <h2 id="provenance-title" style={{ fontSize: '18px', fontWeight: 600, color: 'var(--ink-primary)' }}>
              Forensic System Provenance & Lineage
            </h2>
          </div>
          <button
            onClick={onClose}
            style={{
              padding: '6px 12px',
              backgroundColor: 'var(--bg-card)',
              border: '1px solid var(--border-hairline)',
              borderRadius: '4px',
              fontSize: '12px',
              color: 'var(--ink-secondary)',
            }}
          >
            Close (ESC)
          </button>
        </div>

        <div style={{ padding: '24px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '20px', fontSize: '12px' }}>
          {/* Earth Observation Sensor Attribution */}
          <div style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-hairline)', borderRadius: '6px', padding: '16px' }}>
            <h3 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--ink-primary)', marginBottom: '8px' }}>
              Authoritative Remote Sensing Assets
            </h3>
            <p style={{ color: 'var(--ink-secondary)', lineHeight: 1.6 }}>
              • <strong>Thermal Infrared Sensor:</strong> Landsat 8 OLI/TIRS-1 (Collection 2 Level-2 Surface Temperature)<br />
              • <strong>Scene Identifier:</strong> <span className="font-tabular">LC08_L2SP_147047_20250419_02_T1</span><br />
              • <strong>Acquisition Date:</strong> April 19, 2025 (Day of Year 109, Window Target DOY 105)<br />
              • <strong>Multispectral Optical:</strong> Copernicus Sentinel-2 MSI (Level-2A BOA Reflectance, 10m)<br />
              • <strong>Demographic Census:</strong> WorldPop 2020 UN-Adjusted 100m Dasymetric Grid (Persons/Grid)
            </p>
          </div>

          {/* Mathematical Formulations Register */}
          <div>
            <h3 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--ink-primary)', marginBottom: '8px' }}>
              Ratified Scientific Formulations (Frozen Baseline)
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div style={{ padding: '10px', backgroundColor: 'var(--bg-card)', borderRadius: '4px' }}>
                <span className="font-tabular" style={{ fontWeight: 600, color: 'var(--truth-derived-ink)' }}>F-14 / F-15</span>
                <p style={{ color: 'var(--ink-secondary)', fontSize: '11px', marginTop: '2px' }}>Multi-year temporal LST anomaly and peak summer baseline aggregation.</p>
              </div>
              <div style={{ padding: '10px', backgroundColor: 'var(--bg-card)', borderRadius: '4px' }}>
                <span className="font-tabular" style={{ fontWeight: 600, color: 'var(--truth-derived-ink)' }}>F-21 / F-22</span>
                <p style={{ color: 'var(--ink-secondary)', fontSize: '11px', marginTop: '2px' }}>Compound Hazard, Exposure, Vulnerability (HEV) climate risk surface.</p>
              </div>
              <div style={{ padding: '10px', backgroundColor: 'var(--bg-card)', borderRadius: '4px' }}>
                <span className="font-tabular" style={{ fontWeight: 600, color: 'var(--truth-derived-ink)' }}>F-23.1</span>
                <p style={{ color: 'var(--ink-secondary)', fontSize: '11px', marginTop: '2px' }}>Anselin Local Moran’s I spatial autocorrelation and LISA cluster prioritization.</p>
              </div>
              <div style={{ padding: '10px', backgroundColor: 'var(--bg-card)', borderRadius: '4px' }}>
                <span className="font-tabular" style={{ fontWeight: 600, color: 'var(--truth-modeled-ink)' }}>F-24.1 – F-25.1</span>
                <p style={{ color: 'var(--ink-secondary)', fontSize: '11px', marginTop: '2px' }}>Mixed-Integer Linear Programming (MILP) budget-constrained spatial allocation.</p>
              </div>
            </div>
          </div>

          {/* Optimization Engine & Solver Runtime */}
          <div style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-hairline)', borderRadius: '6px', padding: '16px' }}>
            <h3 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--ink-primary)', marginBottom: '8px' }}>
              Optimization Solver Performance
            </h3>
            <p style={{ color: 'var(--ink-secondary)', lineHeight: 1.6 }}>
              • <strong>Solver Engine:</strong> HiGHS (scipy.optimize.milp, Branch-and-Cut simplex)<br />
              • <strong>Run ID:</strong> <span className="font-tabular">OPT-PUNE-2025-SCENARIO-BA225D6A</span><br />
              • <strong>Candidate Pairs Evaluated:</strong> 7,115 (H3 Resolution 9 cells)<br />
              • <strong>Solver Execution Time:</strong> 70.13 seconds<br />
              • <strong>Optimality Status:</strong> OPTIMAL (Relative MIP gap &lt; 0.01)
            </p>
          </div>

          {/* Immutable Parquet SHA-256 Digests */}
          <div>
            <h3 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--ink-primary)', marginBottom: '8px' }}>
              Cryptographic Artifact Digests (SHA-256)
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ padding: '8px 12px', backgroundColor: 'var(--bg-card)', borderRadius: '4px' }}>
                <span style={{ fontSize: '11px', color: 'var(--ink-secondary)' }}>canonical_feature_matrix.parquet:</span>
                <p className="font-tabular" style={{ fontSize: '11px', color: 'var(--ink-primary)', wordBreak: 'break-all' }}>
                  {provenanceData?.feature_matrix_sha256 || '76f344b147b349f3887259f64c97923414c74fd9a97ec679844fb8d9109f7c01'}
                </p>
              </div>
              <div style={{ padding: '8px 12px', backgroundColor: 'var(--bg-card)', borderRadius: '4px' }}>
                <span style={{ fontSize: '11px', color: 'var(--ink-secondary)' }}>canonical_optimization_allocation.parquet:</span>
                <p className="font-tabular" style={{ fontSize: '11px', color: 'var(--ink-primary)', wordBreak: 'break-all' }}>
                  {provenanceData?.source_sha256 || '2519473a32a2b4a3a22bc8beb43525c3f21dc404783168f1edd6de7bc4bb5555'}
                </p>
              </div>
              <div style={{ padding: '8px 12px', backgroundColor: 'var(--bg-card)', borderRadius: '4px' }}>
                <span style={{ fontSize: '11px', color: 'var(--ink-secondary)' }}>canonical_risk_surface.parquet:</span>
                <p className="font-tabular" style={{ fontSize: '11px', color: 'var(--ink-primary)', wordBreak: 'break-all' }}>
                  {provenanceData?.risk_surface_sha256 || 'e2d5df6c7a0a9584367a623b0722e87f3f4340ea5ebf297cb5aaed6533da5677'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
