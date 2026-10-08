import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { TruthBadge } from '../components/TruthBadge';

describe('TruthLayer Epistemic Integrity System', () => {
  it('renders OBSERVED badge with explicit text and neutral styling', () => {
    render(<TruthBadge layer="OBSERVED" detail="Landsat 8" />);
    expect(screen.getByText('Observed')).toBeInTheDocument();
    expect(screen.getByText('Landsat 8')).toBeInTheDocument();
  });

  it('renders DERIVED badge with explicit text and formula detail', () => {
    render(<TruthBadge layer="DERIVED" detail="F-15" />);
    expect(screen.getByText('Derived')).toBeInTheDocument();
    expect(screen.getByText('F-15')).toBeInTheDocument();
  });

  it('renders MODELED badge with explicit text', () => {
    render(<TruthBadge layer="MODELED" detail="HiGHS MILP" />);
    expect(screen.getByText('Modeled')).toBeInTheDocument();
    expect(screen.getByText('HiGHS MILP')).toBeInTheDocument();
  });

  it('renders NOT_YET_VERIFIED badge and NEVER confuses modeled with verified', () => {
    render(<TruthBadge layer="NOT_YET_VERIFIED" />);
    expect(screen.getByText('Not yet verified')).toBeInTheDocument();
    expect(screen.queryByText('Verified')).not.toBeInTheDocument();
  });

  it('does not display verified green status for proposal phase', () => {
    render(<TruthBadge layer="UNVERIFIED" />);
    expect(screen.getByText('Not yet verified')).toBeInTheDocument();
  });
});
