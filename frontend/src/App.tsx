import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Navigation } from './components/Navigation';
import { OverviewPage } from './pages/OverviewPage';
import { ExplorePage } from './pages/ExplorePage';
import { ProjectPage } from './pages/ProjectPage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        {/* Accessible skip link */}
        <a
          href="#main-content"
          style={{
            position: 'absolute',
            left: '-9999px',
            top: 'auto',
            width: '1px',
            height: '1px',
            overflow: 'hidden',
          }}
          onFocus={(e) => {
            e.currentTarget.style.position = 'fixed';
            e.currentTarget.style.left = '16px';
            e.currentTarget.style.top = '16px';
            e.currentTarget.style.width = 'auto';
            e.currentTarget.style.height = 'auto';
            e.currentTarget.style.zIndex = '9999';
            e.currentTarget.style.padding = '8px 16px';
            e.currentTarget.style.background = 'var(--accent-focal)';
            e.currentTarget.style.color = '#0C0E0D';
          }}
          onBlur={(e) => {
            e.currentTarget.style.position = 'absolute';
            e.currentTarget.style.left = '-9999px';
            e.currentTarget.style.width = '1px';
            e.currentTarget.style.height = '1px';
          }}
        >
          Skip to main content
        </a>

        <Navigation />

        <main id="main-content" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <Routes>
            <Route path="/" element={<OverviewPage />} />
            <Route path="/explore/pune" element={<ExplorePage />} />
            <Route path="/projects/:id" element={<ProjectPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
};

export default App;
