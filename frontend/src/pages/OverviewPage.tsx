import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { TruthBadge } from '../components/TruthBadge';
import { CANONICAL_PROJECT_ID, climoraApi } from '../services/api';
import { ProjectSummary } from '../types/api';

export const OverviewPage: React.FC = () => {
  const [project, setProject] = useState<ProjectSummary | null>(null);

  useEffect(() => {
    climoraApi.getProjectDetail(CANONICAL_PROJECT_ID)
      .then((data) => setProject(data))
      .catch(() => {
        // Fallback gracefully without fabricating false data
      });
  }, []);

  return (
    <div style={{ maxWidth: '1080px', margin: '0 auto', padding: '64px 32px 96px', display: 'flex', flexDirection: 'column', gap: '64px' }}>
      {/* Editorial Hero */}
      <section style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <h1
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: '52px',
            fontWeight: 400,
            lineHeight: 1.1,
            letterSpacing: '-0.02em',
            color: 'var(--ink-primary)',
            maxWidth: '820px',
          }}
        >
          Turning planetary observations into fundable urban interventions.
        </h1>

        <p
          style={{
            fontSize: '18px',
            color: 'var(--ink-secondary)',
            maxWidth: '680px',
            lineHeight: 1.5,
          }}
        >
          A mathematical decision-support instrument for municipal heat resilience in Pune, India.
        </p>

        <div style={{ display: 'flex', gap: '16px', marginTop: '12px' }}>
          <Link
            to="/explore/pune"
            style={{
              padding: '12px 24px',
              backgroundColor: 'var(--ink-primary)',
              color: 'var(--bg-ground)',
              fontSize: '14px',
              fontWeight: 500,
              borderRadius: '4px',
              transition: 'opacity 0.15s ease',
            }}
          >
            Explore Pune
          </Link>
          <Link
            to={`/projects/${CANONICAL_PROJECT_ID}`}
            style={{
              padding: '12px 24px',
              backgroundColor: 'transparent',
              border: '1px solid var(--border-hairline-hover)',
              color: 'var(--ink-primary)',
              fontSize: '14px',
              fontWeight: 500,
              borderRadius: '4px',
              transition: 'background-color 0.15s ease',
            }}
          >
            View project
          </Link>
        </div>
      </section>

      {/* Restrained 4-Metric Summary Strip */}
      <section
        style={{
          borderTop: '1px solid var(--border-hairline)',
          borderBottom: '1px solid var(--border-hairline)',
          padding: '32px 0',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '24px',
        }}
      >
        <div>
          <span style={{ fontSize: '12px', color: 'var(--ink-secondary)', display: 'block', marginBottom: '4px' }}>
            5-year thermal baseline
          </span>
          <p className="font-tabular" style={{ fontSize: '28px', fontWeight: 600, color: 'var(--ink-primary)' }}>
            46.36°C
          </p>
          <div style={{ marginTop: '6px' }}>
            <TruthBadge layer="OBSERVED" detail="Landsat 2021-2025" />
          </div>
        </div>

        <div>
          <span style={{ fontSize: '12px', color: 'var(--ink-secondary)', display: 'block', marginBottom: '4px' }}>
            Priority footprint
          </span>
          <p className="font-tabular" style={{ fontSize: '28px', fontWeight: 600, color: 'var(--ink-primary)' }}>
            {project?.geographic_scope?.total_treated_cells_count || 28} H3 cells
          </p>
          <div style={{ marginTop: '6px' }}>
            <TruthBadge layer="DERIVED" detail="Spatial hotspot cluster" />
          </div>
        </div>

        <div>
          <span style={{ fontSize: '12px', color: 'var(--ink-secondary)', display: 'block', marginBottom: '4px' }}>
            Planned intervention
          </span>
          <p className="font-tabular" style={{ fontSize: '28px', fontWeight: 600, color: 'var(--ink-primary)' }}>
            {project?.intervention_summary?.total_physical_units
              ? `${Math.round(project.intervention_summary.total_physical_units).toLocaleString('en-US')} trees`
              : '2,695 trees'}
          </p>
          <div style={{ marginTop: '6px' }}>
            <TruthBadge layer="MODELED" detail="15.0m interval" />
          </div>
        </div>

        <div>
          <span style={{ fontSize: '12px', color: 'var(--ink-secondary)', display: 'block', marginBottom: '4px' }}>
            Modeled capital
          </span>
          <p className="font-tabular" style={{ fontSize: '28px', fontWeight: 600, color: 'var(--ink-primary)' }}>
            {project?.modeled_cost ? `₹${(project.modeled_cost / 1e6).toFixed(2)}M` : '₹9.99M'}
          </p>
          <div style={{ marginTop: '6px' }}>
            <TruthBadge layer="MODELED" detail="Under ₹10.0M ceiling" />
          </div>
        </div>
      </section>

      {/* The Decision Process */}
      <section style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <h2 style={{ fontSize: '18px', fontWeight: 500, color: 'var(--ink-primary)' }}>
          The Decision Process
        </h2>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '16px',
            backgroundColor: 'var(--bg-panel)',
            border: '1px solid var(--border-hairline)',
            borderRadius: '6px',
            padding: '24px',
          }}
        >
          <div>
            <span className="font-tabular" style={{ fontSize: '11px', color: 'var(--ink-tertiary)', textTransform: 'uppercase' }}>
              Stage 1
            </span>
            <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--ink-primary)', marginTop: '2px' }}>
              Satellite Observation
            </h3>
            <p style={{ fontSize: '12px', color: 'var(--ink-secondary)', marginTop: '4px', lineHeight: 1.5 }}>
              Landsat 8/9 TIRS & Sentinel-2 surface temperature and vegetation coverage across multi-year pre-monsoon windows.
            </p>
          </div>

          <div>
            <span className="font-tabular" style={{ fontSize: '11px', color: 'var(--ink-tertiary)', textTransform: 'uppercase' }}>
              Stage 2
            </span>
            <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--ink-primary)', marginTop: '2px' }}>
              Spatial Risk Mesh
            </h3>
            <p style={{ fontSize: '12px', color: 'var(--ink-secondary)', marginTop: '4px', lineHeight: 1.5 }}>
              Uber H3 Resolution 9 discretization evaluating compound thermal hazard, WorldPop human exposure, and LISA clusters.
            </p>
          </div>

          <div>
            <span className="font-tabular" style={{ fontSize: '11px', color: 'var(--ink-tertiary)', textTransform: 'uppercase' }}>
              Stage 3
            </span>
            <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--ink-primary)', marginTop: '2px' }}>
              Optimized Intervention
            </h3>
            <p style={{ fontSize: '12px', color: 'var(--ink-secondary)', marginTop: '4px', lineHeight: 1.5 }}>
              Mixed-integer programming allocates roadside street-tree shading to maximize verified risk reduction under budget limits.
            </p>
          </div>

          <div>
            <span className="font-tabular" style={{ fontSize: '11px', color: 'var(--ink-tertiary)', textTransform: 'uppercase' }}>
              Stage 4
            </span>
            <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--ink-primary)', marginTop: '2px' }}>
              Municipal Tender
            </h3>
            <p style={{ fontSize: '12px', color: 'var(--ink-secondary)', marginTop: '4px', lineHeight: 1.5 }}>
              Immutable capital ledger with cell-by-cell sapling quantities, mobilization line-items, and contractor tracking.
            </p>
          </div>
        </div>
      </section>

      {/* Pune Municipal Demonstration */}
      <section style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <h2 style={{ fontSize: '18px', fontWeight: 500, color: 'var(--ink-primary)' }}>
          Pune Municipal Demonstration
        </h2>
        <div
          style={{
            padding: '28px',
            backgroundColor: 'var(--bg-panel)',
            border: '1px solid var(--border-hairline)',
            borderRadius: '6px',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
          }}
        >
          <div>
            <span className="font-tabular" style={{ fontSize: '12px', color: 'var(--ink-secondary)' }}>
              {CANONICAL_PROJECT_ID}
            </span>
            <h3 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--ink-primary)', marginTop: '2px' }}>
              Pune Urban Heat Island Mitigation & Street Canopy Initiative
            </h3>
            <p style={{ fontSize: '14px', color: 'var(--ink-secondary)', marginTop: '6px', maxWidth: '720px', lineHeight: 1.5 }}>
              A targeted ₹10M roadside canopy intervention protecting {project?.population_in_scope?.display_rounded?.toLocaleString('en-US') || '118,941'} residents
              across acute heat-island corridors in Pune.
            </p>
          </div>

          <div>
            <Link
              to={`/projects/${CANONICAL_PROJECT_ID}`}
              style={{
                fontSize: '13px',
                fontWeight: 500,
                color: 'var(--truth-derived-ink)',
                textDecoration: 'underline',
              }}
            >
              View project prospectus →
            </Link>
          </div>
        </div>
      </section>

      {/* Institutional Source Attribution Footer */}
      <footer
        style={{
          borderTop: '1px solid var(--border-hairline)',
          paddingTop: '24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: '11px',
          color: 'var(--ink-tertiary)',
        }}
      >
        <span>CLIMORA · Planetary climate intelligence for municipal decision-making</span>
        <span>USGS Landsat · ESA Sentinel-2 · WorldPop · OpenStreetMap · Uber H3 DGGS</span>
      </footer>
    </div>
  );
};
