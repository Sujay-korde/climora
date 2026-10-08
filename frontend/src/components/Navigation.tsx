import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import { CANONICAL_PROJECT_ID } from '../services/api';

export const Navigation: React.FC = () => {
  return (
    <header
      style={{
        height: 'var(--nav-height)',
        borderBottom: '1px solid var(--border-hairline)',
        backgroundColor: 'var(--bg-ground)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 32px',
        position: 'sticky',
        top: 0,
        zIndex: 1000,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '48px' }}>
        <Link
          to="/"
          style={{
            fontFamily: 'var(--font-sans)',
            fontSize: '15px',
            fontWeight: 600,
            letterSpacing: '0.04em',
            color: 'var(--ink-primary)',
          }}
          aria-label="CLIMORA Home"
        >
          CLIMORA
        </Link>

        <nav aria-label="Main Navigation" style={{ display: 'flex', gap: '28px' }}>
          <NavLink
            to="/"
            end
            style={({ isActive }) => ({
              fontFamily: 'var(--font-sans)',
              fontSize: '13px',
              color: isActive ? 'var(--ink-primary)' : 'var(--ink-secondary)',
              transition: 'color 0.15s ease',
              borderBottom: isActive ? '1px solid var(--ink-primary)' : '1px solid transparent',
              paddingBottom: '4px',
            })}
          >
            Overview
          </NavLink>
          <NavLink
            to="/explore/pune"
            style={({ isActive }) => ({
              fontFamily: 'var(--font-sans)',
              fontSize: '13px',
              color: isActive ? 'var(--ink-primary)' : 'var(--ink-secondary)',
              transition: 'color 0.15s ease',
              borderBottom: isActive ? '1px solid var(--ink-primary)' : '1px solid transparent',
              paddingBottom: '4px',
            })}
          >
            Explore
          </NavLink>
          <NavLink
            to={`/projects/${CANONICAL_PROJECT_ID}`}
            style={({ isActive }) => ({
              fontFamily: 'var(--font-sans)',
              fontSize: '13px',
              color: isActive ? 'var(--ink-primary)' : 'var(--ink-secondary)',
              transition: 'color 0.15s ease',
              borderBottom: isActive ? '1px solid var(--ink-primary)' : '1px solid transparent',
              paddingBottom: '4px',
            })}
          >
            Projects
          </NavLink>
        </nav>
      </div>

      <div style={{ display: 'flex', alignItems: 'center' }}>
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '11px',
            color: 'var(--ink-tertiary)',
            letterSpacing: '0.02em',
          }}
        >
          Pune · H3 Res-9
        </span>
      </div>
    </header>
  );
};
