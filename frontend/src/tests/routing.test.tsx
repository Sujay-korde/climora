import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { Navigation } from '../components/Navigation';

describe('Navigation Wayfinding Architecture', () => {
  it('renders persistent quiet navigation with 3 canonical routes and zero telemetry clutter', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Navigation />
      </MemoryRouter>
    );

    // Brand and 3 routes
    expect(screen.getByText('CLIMORA')).toBeInTheDocument();
    expect(screen.getByText('Overview')).toBeInTheDocument();
    expect(screen.getByText('Explore')).toBeInTheDocument();
    expect(screen.getByText('Projects')).toBeInTheDocument();

    // Verify deprecated telemetry and numbering are permanently absent
    expect(screen.queryByText(/01 \//)).not.toBeInTheDocument();
    expect(screen.queryByText(/02 \//)).not.toBeInTheDocument();
    expect(screen.queryByText(/03 \//)).not.toBeInTheDocument();
    expect(screen.queryByText(/AOI: 4194/)).not.toBeInTheDocument();
    expect(screen.queryByText(/METRIC:/)).not.toBeInTheDocument();
    expect(screen.queryByText(/SENSOR:/)).not.toBeInTheDocument();
    expect(screen.queryByText(/DOY:/)).not.toBeInTheDocument();
    expect(screen.queryByText(/CLOUD:/)).not.toBeInTheDocument();
  });
});
