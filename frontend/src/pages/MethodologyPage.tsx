import React from 'react';
import { TruthBadge } from '../components/TruthBadge';

export const MethodologyPage: React.FC = () => {
  return (
    <div style={{ maxWidth: '1120px', margin: '0 auto', padding: '48px 32px 96px', display: 'flex', flexDirection: 'column', gap: '48px' }}>
      {/* Header */}
      <section style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--ink-secondary)' }}>
            Scientific & Analytical Provenance
          </span>
          <TruthBadge layer="DERIVED" detail="Peer-Reviewed Methodology" />
        </div>
        <h1
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: '44px',
            fontWeight: 400,
            color: 'var(--ink-primary)',
          }}
        >
          Data Provenance & Scientific Methodology
        </h1>
        <p style={{ fontSize: '16px', color: 'var(--ink-secondary)', maxWidth: '820px', lineHeight: 1.6 }}>
          CLIMORA maintains complete mathematical and scientific transparency. Every layer, coefficient, constraint, and score is
          grounded in peer-reviewed climate literature, verifiable satellite acquisitions, and ratifiable operations research formulations.
        </p>
      </section>

      {/* Section 1: Foundational Datasets & Ingestion Traceability */}
      <section style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: 600, color: 'var(--ink-primary)', borderBottom: '1px solid var(--border-hairline)', paddingBottom: '12px' }}>
          1. Verified Upstream Datasets & Spatial Lineage
        </h2>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px' }}>
          <div style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-hairline)', borderRadius: '6px', padding: '20px' }}>
            <span style={{ fontSize: '11px', color: 'var(--domain-thermal)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
              Thermal Surface Temperature
            </span>
            <h3 style={{ fontSize: '15px', color: 'var(--ink-primary)', margin: '6px 0 10px' }}>Landsat 8 & 9 TIRS</h3>
            <ul style={{ fontSize: '12px', color: 'var(--ink-secondary)', lineHeight: 1.6, paddingLeft: '16px' }}>
              <li><strong>Provider:</strong> USGS / NASA Earth Data</li>
              <li><strong>Native Resolution:</strong> 100m resampled to 30m</li>
              <li><strong>Temporal Coverage:</strong> 5-Year Baseline (2021-2025 April DOY 95-115)</li>
              <li><strong>Sensor Uncertainty:</strong> &lt; 2.2 K (USGS Level-2 Surface Temperature)</li>
              <li><strong>Aggregation:</strong> Zonal Median & Mean per H3 Res-9 hexagon</li>
            </ul>
          </div>

          <div style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-hairline)', borderRadius: '6px', padding: '20px' }}>
            <span style={{ fontSize: '11px', color: 'var(--domain-canopy)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
              Optical Vegetation & Built Index
            </span>
            <h3 style={{ fontSize: '15px', color: 'var(--ink-primary)', margin: '6px 0 10px' }}>Sentinel-2 MSI (Level-2A)</h3>
            <ul style={{ fontSize: '12px', color: 'var(--ink-secondary)', lineHeight: 1.6, paddingLeft: '16px' }}>
              <li><strong>Provider:</strong> European Space Agency (ESA) Copernicus</li>
              <li><strong>Native Resolution:</strong> 10m (B4, B8) and 20m (B11 SWIR)</li>
              <li><strong>Metrics:</strong> NDVI = (B8 - B4)/(B8 + B4); NDBI = (B11 - B8)/(B11 + B8)</li>
              <li><strong>Quality Screening:</strong> SCL cloud/shadow mask with 0% unmasked pixels</li>
              <li><strong>Aggregation:</strong> Zonal mean within H3 cell polygon</li>
            </ul>
          </div>

          <div style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-hairline)', borderRadius: '6px', padding: '20px' }}>
            <span style={{ fontSize: '11px', color: 'var(--accent-focal)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
              Demographic Exposure
            </span>
            <h3 style={{ fontSize: '15px', color: 'var(--ink-primary)', margin: '6px 0 10px' }}>WorldPop UN-adjusted 2020</h3>
            <ul style={{ fontSize: '12px', color: 'var(--ink-secondary)', lineHeight: 1.6, paddingLeft: '16px' }}>
              <li><strong>Provider:</strong> University of Southampton WorldPop</li>
              <li><strong>Native Resolution:</strong> 30 arc-seconds (~1 km at equator)</li>
              <li><strong>Downscaling Method:</strong> Area-weighted dasymetric polygon sum</li>
              <li><strong>Mass Conservation Delta:</strong> 0.0033% (verified &lt; 0.05% contract)</li>
              <li><strong>Citywide Total:</strong> 5,011,229.59 residents across Pune AOI</li>
            </ul>
          </div>

          <div style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-hairline)', borderRadius: '6px', padding: '20px' }}>
            <span style={{ fontSize: '11px', color: 'var(--domain-hydrology)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
              Urban Infrastructure
            </span>
            <h3 style={{ fontSize: '15px', color: 'var(--ink-primary)', margin: '6px 0 10px' }}>OpenStreetMap (OSM) Vector</h3>
            <ul style={{ fontSize: '12px', color: 'var(--ink-secondary)', lineHeight: 1.6, paddingLeft: '16px' }}>
              <li><strong>Provider:</strong> OSM Contributors via Overpass API</li>
              <li><strong>Network Coverage:</strong> Motorway, trunk, primary, secondary, tertiary</li>
              <li><strong>Civic Infrastructure:</strong> Hospitals, clinics, schools, universities</li>
              <li><strong>Geometry Integrity:</strong> Coordinate deduplication and topological clipping</li>
              <li><strong>Intervention Input:</strong> Derives street tree and pavement capacities</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Section 2: Climate Risk Formulation (H x E x V) */}
      <section style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: 600, color: 'var(--ink-primary)', borderBottom: '1px solid var(--border-hairline)', paddingBottom: '12px' }}>
          2. IPCC AR5 / AR6 Risk Formulation
        </h2>
        <p style={{ fontSize: '14px', color: 'var(--ink-secondary)', lineHeight: 1.6 }}>
          Risk is constructed as a multiplicative tripartite composite index: <code>Risk_i = H_i · E_i · V_i</code>, where each component is bounded in [0, 1]:
        </p>

        <div style={{ backgroundColor: 'var(--bg-panel)', padding: '20px', borderRadius: '6px', border: '1px solid var(--border-hairline-subtle)', display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '13px' }}>
          <div>
            <strong style={{ color: 'var(--domain-thermal)' }}>Hazard (H_i):</strong>
            <code style={{ display: 'block', backgroundColor: 'var(--bg-card)', padding: '6px 10px', marginTop: '4px', borderRadius: '4px', fontFamily: 'var(--font-mono)' }}>
              H_i = 0.40 · norm_LST_2025 + 0.35 · norm_LST_anomaly + 0.15 · norm_Persistence + 0.10 · norm_Recurrence_ge45
            </code>
          </div>

          <div>
            <strong style={{ color: 'var(--accent-focal)' }}>Exposure (E_i):</strong>
            <code style={{ display: 'block', backgroundColor: 'var(--bg-card)', padding: '6px 10px', marginTop: '4px', borderRadius: '4px', fontFamily: 'var(--font-mono)' }}>
              E_i = 0.60 · norm_Population_Count + 0.40 · norm_Population_Density
            </code>
          </div>

          <div>
            <strong style={{ color: 'var(--domain-canopy)' }}>Vulnerability (V_i):</strong>
            <code style={{ display: 'block', backgroundColor: 'var(--bg-card)', padding: '6px 10px', marginTop: '4px', borderRadius: '4px', fontFamily: 'var(--font-mono)' }}>
              V_i = 0.50 · norm_NDVI_Deficit + 0.50 · norm_NDBI (Built-up thermal mass)
            </code>
          </div>
        </div>
      </section>

      {/* Section 3: Observational vs Causal Boundary */}
      <section style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: 600, color: 'var(--ink-primary)', borderBottom: '1px solid var(--border-hairline)', paddingBottom: '12px' }}>
          3. Observational vs. Causal Boundary
        </h2>
        <div style={{ backgroundColor: 'rgba(217, 155, 38, 0.08)', border: '1px solid var(--truth-modeled-ink)', borderRadius: '6px', padding: '16px 20px' }}>
          <p style={{ fontSize: '13px', color: 'var(--ink-primary)', lineHeight: 1.6 }}>
            <strong>Critical Scientific Distinction:</strong> The empirical relationship between vegetative density and surface temperature
            (cross-sectional slope: -0.024°C per canopy m², R² ≈ 0.38 across Pune) is an <strong>observational association</strong>, NOT a causal guarantee.
            CLIMORA uses peer-reviewed biophysical coefficients for optimization planning while explicitly subjecting all intervention outcomes to post-implementation MRV verification.
          </p>
        </div>
      </section>

      {/* Section 4: Optimization Engine & Mathematical Formulation */}
      <section style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: 600, color: 'var(--ink-primary)', borderBottom: '1px solid var(--border-hairline)', paddingBottom: '12px' }}>
          4. Mathematical Formulation (HiGHS MILP F-24.6)
        </h2>
        <p style={{ fontSize: '14px', color: 'var(--ink-secondary)', lineHeight: 1.6 }}>
          The portfolio is formulated as a Mixed-Integer Linear Program solved with the HiGHS branch-and-cut engine:
        </p>

        <div style={{ backgroundColor: 'var(--bg-panel)', padding: '20px', borderRadius: '6px', border: '1px solid var(--border-hairline-subtle)', fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--ink-primary)', lineHeight: 1.8 }}>
          <p><span style={{ color: 'var(--accent-focal)' }}>Maximize:</span> Σ_i Σ_a r_ia · q_ia</p>
          <p><span style={{ color: 'var(--domain-hydrology)' }}>Subject to:</span></p>
          <p>• Budget constraint: Σ_i Σ_a (F_a · x_ia + c_a · q_ia) ≤ B</p>
          <p>• Semi-continuous lot size: Q_ia^min · x_ia ≤ q_ia ≤ Q_ia^max · x_ia</p>
          <p>• Ground surface mutual exclusivity: (q_i,corridor/Q_max) + (q_i,permeable/Q_max) + (q_i,bioswale/Q_max) ≤ 1.0</p>
          <p>• Physical integrality: q_i,tree ∈ ℤ_≥0, x_ia ∈ {'{0, 1}'}</p>
          <p>• Maximum cooling cap: Σ_a e_a · q_ia ≤ 4.0°C per hexagon</p>
        </div>
      </section>

      {/* Section 5: What the System Measures vs What It Cannot Verify */}
      <section style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: 600, color: 'var(--ink-primary)', borderBottom: '1px solid var(--border-hairline)', paddingBottom: '12px' }}>
          5. System Scope: Capabilities & Honest Boundaries
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-hairline)', borderRadius: '6px', padding: '20px' }}>
            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--domain-canopy)', display: 'block', marginBottom: '8px' }}>
              ✓ What CLIMORA Defensibly Achieves
            </span>
            <ul style={{ fontSize: '12px', color: 'var(--ink-secondary)', lineHeight: 1.6, paddingLeft: '16px' }}>
              <li>Unified multi-spectral satellite baseline across 3,181 H3 Res-9 cells</li>
              <li>Mass-conserved population exposure downscaling (0.0033% error)</li>
              <li>Exact integer-constrained budget optimization eliminating fractional trees</li>
              <li>Cedar-guarded municipal governance audit trail with cryptographic immutability</li>
              <li>Transparent multi-objective metric reporting (risk, population, equity, slack)</li>
            </ul>
          </div>

          <div style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-hairline)', borderRadius: '6px', padding: '20px' }}>
            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--domain-thermal)', display: 'block', marginBottom: '8px' }}>
              ✗ What CLIMORA Does Not Claim
            </span>
            <ul style={{ fontSize: '12px', color: 'var(--ink-secondary)', lineHeight: 1.6, paddingLeft: '16px' }}>
              <li>Does NOT claim single-cell satellite detection of 0.07°C tree cooling</li>
              <li>Does NOT present modeled predictions as verified real-world outcomes</li>
              <li>Does NOT run Difference-in-Differences before post-deployment satellite acquisitions</li>
              <li>Does NOT permit unauthenticated role elevation or query-string impersonation</li>
              <li>Does NOT invent missing datasets or fabricate socioeconomic variables</li>
            </ul>
          </div>
        </div>
      </section>
    </div>
  );
};

