import React, { useEffect, useState } from 'react';
import { TruthBadge } from '../components/TruthBadge';
import { CANONICAL_PROJECT_ID, climoraApi } from '../services/api';
import { MRVOverviewResponse } from '../types/api';

export const MRVImpactPage: React.FC = () => {
  const [mrvData, setMrvData] = useState<MRVOverviewResponse['data'] | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    climoraApi.getMRV(CANONICAL_PROJECT_ID)
      .then((data) => setMrvData(data))
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '48px 32px 96px', display: 'flex', flexDirection: 'column', gap: '48px' }}>
      {/* Header */}
      <section style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--ink-secondary)' }}>
            Empirical Evidence & Audit Framework
          </span>
          <TruthBadge layer="UNVERIFIED" detail="Pending Post-Deployment Observation" />
        </div>
        <h1
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: '44px',
            fontWeight: 400,
            color: 'var(--ink-primary)',
          }}
        >
          MRV, Empirical Impact & Verification Architecture
        </h1>
        <p style={{ fontSize: '16px', color: 'var(--ink-secondary)', maxWidth: '820px', lineHeight: 1.6 }}>
          CLIMORA enforces a strict tripartite separation across <strong>PREDICTED</strong>, <strong>OBSERVED</strong>, and <strong>VERIFIED</strong> states.
          Model predictions are never conflated with observed real-world outcomes, and unverified projects never receive deceptive green certification badges.
        </p>
      </section>

      {/* Critical Scientific Detectability Warning Banner (Phase E2) */}
      <section
        style={{
          backgroundColor: 'rgba(217, 107, 67, 0.08)',
          border: '1px solid var(--domain-thermal)',
          borderRadius: '8px',
          padding: '24px',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ color: 'var(--domain-thermal)', fontSize: '14px', fontWeight: 600 }}>
            ⚠️ Scientific Truth Principle: Landsat Thermal Sensor Noise Floor & Single-Cell Detectability Limits
          </span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', fontSize: '13px', color: 'var(--ink-primary)' }}>
          <div>
            <span style={{ color: 'var(--ink-secondary)', display: 'block', fontSize: '11px' }}>USGS Landsat ST Uncertainty</span>
            <strong className="font-tabular" style={{ fontSize: '16px' }}>&lt; 2.2 K (Cook et al. 2014)</strong>
          </div>
          <div>
            <span style={{ color: 'var(--ink-secondary)', display: 'block', fontSize: '11px' }}>Pune Cross-Year Cell Std Dev (σ)</span>
            <strong className="font-tabular" style={{ fontSize: '16px' }}>2.45°C - 3.0°C</strong>
          </div>
          <div>
            <span style={{ color: 'var(--ink-secondary)', display: 'block', fontSize: '11px' }}>Single-Cell MDE (80% Power)</span>
            <strong className="font-tabular" style={{ fontSize: '16px', color: 'var(--domain-thermal)' }}>~6.91°C</strong>
          </div>
          <div>
            <span style={{ color: 'var(--ink-secondary)', display: 'block', fontSize: '11px' }}>Modeled Tree Cooling per Cell</span>
            <strong className="font-tabular" style={{ fontSize: '16px', color: 'var(--domain-canopy)' }}>~0.07°C</strong>
          </div>
        </div>
        <p style={{ fontSize: '13px', color: 'var(--ink-secondary)', lineHeight: 1.6, borderTop: '1px solid rgba(217, 107, 67, 0.2)', paddingTop: '12px' }}>
          <strong>Physical Limitation:</strong> Because single-cell Landsat thermal measurement noise (MDE ~6.91°C) exceeds the modeled intervention cooling (0.07°C) by two orders of magnitude,
          <strong> single-cell satellite detection of tree cooling is physically undetectable without spatial corridor aggregation (minimum 2+ contiguous cells) or multi-year compositing.</strong>
          CLIMORA's MRV Quality Control Engine rejects any premature single-cell satellite verification claim that ignores this sensor noise floor.
        </p>
      </section>

      {/* Tripartite State Separation Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px' }}>
        {/* Tier 1: PREDICTED */}
        <div
          style={{
            backgroundColor: 'var(--bg-card)',
            border: '1px solid var(--border-hairline)',
            borderRadius: '8px',
            padding: '24px',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--truth-modeled-ink)' }}>
              Layer 1: Planned
            </span>
            <TruthBadge layer="MODELED" detail="HiGHS Solver" />
          </div>
          <h2 style={{ fontSize: '20px', fontWeight: 600, color: 'var(--ink-primary)' }}>
            PREDICTED
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--ink-secondary)', lineHeight: 1.5 }}>
            Mathematical optimization outputs based on biophysical models, carrying capacities, and unit cooling coefficients.
          </p>
          <div style={{ backgroundColor: 'var(--bg-panel)', padding: '14px', borderRadius: '6px', fontSize: '12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div>
              <span style={{ color: 'var(--ink-tertiary)', display: 'block' }}>Expected Risk Reduction:</span>
              <strong className="font-tabular" style={{ color: 'var(--truth-modeled-ink)', fontSize: '15px' }}>0.106048</strong>
            </div>
            <div>
              <span style={{ color: 'var(--ink-tertiary)', display: 'block' }}>Expected Cooling:</span>
              <strong className="font-tabular" style={{ color: 'var(--ink-primary)' }}>0.04°C - 0.08°C per cell</strong>
            </div>
            <div>
              <span style={{ color: 'var(--ink-tertiary)', display: 'block' }}>Scope:</span>
              <span>28 H3 Res-9 cells (2,695 trees)</span>
            </div>
          </div>
        </div>

        {/* Tier 2: OBSERVED */}
        <div
          style={{
            backgroundColor: 'var(--bg-card)',
            border: '1px solid var(--border-hairline)',
            borderRadius: '8px',
            padding: '24px',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--truth-observed-ink)' }}>
              Layer 2: Telemetry
            </span>
            <TruthBadge layer="OBSERVED" detail="Empirical Telemetry" />
          </div>
          <h2 style={{ fontSize: '20px', fontWeight: 600, color: 'var(--ink-primary)' }}>
            OBSERVED
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--ink-secondary)', lineHeight: 1.5 }}>
            Post-implementation empirical satellite (Landsat-9, Sentinel-2) and field contractor telemetry.
          </p>
          <div style={{ backgroundColor: 'var(--bg-panel)', padding: '14px', borderRadius: '6px', fontSize: '12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div>
              <span style={{ color: 'var(--ink-tertiary)', display: 'block' }}>Sensor Requirements:</span>
              <strong style={{ color: 'var(--ink-primary)' }}>Landsat-9 TIRS (Thermal) + Sentinel-2 (NDVI)</strong>
            </div>
            <div>
              <span style={{ color: 'var(--ink-tertiary)', display: 'block' }}>Temporal Window:</span>
              <span>DOY 95-115 (Annual April Summer Baseline)</span>
            </div>
            <div>
              <span style={{ color: 'var(--ink-tertiary)', display: 'block' }}>Quality Filters:</span>
              <span>Cloud cover ≤ 5.0%, 100% QA pixel masking</span>
            </div>
          </div>
        </div>

        {/* Tier 3: VERIFIED */}
        <div
          style={{
            backgroundColor: 'var(--bg-card)',
            border: '1px solid var(--border-hairline)',
            borderRadius: '8px',
            padding: '24px',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--truth-unverified-ink)' }}>
              Layer 3: Certification
            </span>
            <TruthBadge layer={(mrvData?.qc_state === 'PASSED' ? 'VERIFIED' : 'UNVERIFIED') as any} detail={isLoading ? 'Auditing...' : (mrvData?.qc_state || "Awaiting Post-Deployment Audit")} />
          </div>
          <h2 style={{ fontSize: '20px', fontWeight: 600, color: 'var(--ink-primary)' }}>
            VERIFIED
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--ink-secondary)', lineHeight: 1.5 }}>
            Third-party audited milestone certifying whether observed empirical effects match planned expectations.
          </p>
          <div style={{ backgroundColor: 'var(--bg-panel)', padding: '14px', borderRadius: '6px', fontSize: '12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div>
              <span style={{ color: 'var(--ink-tertiary)', display: 'block' }}>Status:</span>
              <strong style={{ color: 'var(--truth-unverified-ink)' }}>{mrvData?.difference_in_differences_status?.current_operational_status || 'AWAITING PHYSICAL DEPLOYMENT'}</strong>
            </div>
            <div>
              <span style={{ color: 'var(--ink-tertiary)', display: 'block' }}>Certification Body:</span>
              <span>Accredited Carbon & Environmental Auditor</span>
            </div>
            <div>
              <span style={{ color: 'var(--ink-tertiary)', display: 'block' }}>Cryptographic Artifact:</span>
              <span>SHA-256 Hashed Evidence Audit Dossier</span>
            </div>
          </div>
        </div>
      </div>

      {/* Difference-in-Differences (DID) Honest Disclosure */}
      <section
        style={{
          backgroundColor: 'var(--bg-panel)',
          border: '1px solid var(--border-hairline)',
          borderRadius: '8px',
          padding: '24px',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--ink-primary)' }}>
            Difference-in-Differences (DID) Econometric Evaluation
          </h3>
          <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--ink-tertiary)', padding: '4px 8px', backgroundColor: 'var(--bg-card)', borderRadius: '4px' }}>
            STATUS: PLANNED / NOT_YET_EXECUTABLE
          </span>
        </div>
        <p style={{ fontSize: '13px', color: 'var(--ink-secondary)', lineHeight: 1.6 }}>
          Honest empirical Difference-in-Differences evaluation requires post-deployment satellite acquisitions matching pre-intervention baseline seasonality across treated and matched control hexagons.
          CLIMORA strictly prohibits running DID against baseline-only, synthetic, or modeled data. The econometric evaluator will execute post-April 2026 satellite acquisition.
        </p>
      </section>
    </div>
  );
};

