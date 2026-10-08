import React, { useEffect, useState, useCallback } from 'react';
import { SpatialMap } from '../components/SpatialMap';
import { MapControls, LayerMode } from '../components/MapControls';
import { ScenarioControlCard } from '../components/ScenarioControlCard';
import { SelectionSummaryCard } from '../components/SelectionSummaryCard';
import { CellInspector } from '../components/CellInspector';
import { AccessibleTable } from '../components/AccessibleTable';
import { MobileBottomSheet } from '../components/MobileBottomSheet';
import { ProvenanceModal } from '../components/ProvenanceModal';
import { CANONICAL_PROJECT_ID, climoraApi } from '../services/api';
import { AllocationItem, BaselineCell, RiskSurfaceCell, ScenarioOptimizeResponse } from '../types/api';

export const ExplorePage: React.FC = () => {
  const [riskCells, setRiskCells] = useState<RiskSurfaceCell[]>([]);
  const [puneBoundary, setPuneBoundary] = useState<any>(null);
  const [cells, setCells] = useState<BaselineCell[]>([]);
  const [allocations, setAllocations] = useState<AllocationItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Map state
  const [activeLayer, setActiveLayer] = useState<LayerMode>('thermal');
  const [showFootprint, setShowFootprint] = useState(true);
  const [showScenarioOverlay, setShowScenarioOverlay] = useState(true);
  const [selectedCellId, setSelectedCellId] = useState<string | null>(null);
  const [isInspectorOpen, setIsInspectorOpen] = useState(false);
  const [isTableView, setIsTableView] = useState(false);
  const [isProvenanceOpen, setIsProvenanceOpen] = useState(false);

  // Scenario Optimization state
  const [scenarioBudget, setScenarioBudget] = useState<number>(5000000);
  const [scenarioResult, setScenarioResult] = useState<ScenarioOptimizeResponse['data'] | null>(null);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [scenarioError, setScenarioError] = useState<string | null>(null);

  // Responsive state
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Fetch canonical allocation, boundary, and full risk surface data
  useEffect(() => {
    setIsLoading(true);
    setErrorMsg(null);

    Promise.all([
      climoraApi.getRiskSurface(CANONICAL_PROJECT_ID),
      climoraApi.getPuneBoundary(CANONICAL_PROJECT_ID).catch(() => null),
      climoraApi.getAllocation(CANONICAL_PROJECT_ID),
      climoraApi.getBaseline(CANONICAL_PROJECT_ID).catch(() => ({ cells: [] })),
    ])
      .then(([riskData, boundaryData, allocData, baseData]) => {
        setRiskCells(riskData.cells);
        setPuneBoundary(boundaryData);
        setAllocations(allocData.allocations);
        setCells(baseData.cells);
        setIsLoading(false);
      })
      .catch((err) => {
        setErrorMsg(err.message || 'Unable to connect to municipal spatial data service.');
        setIsLoading(false);
      });
  }, []);

  // Handle Alt+T shortcut
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.altKey && (e.key === 't' || e.key === 'T')) {
        e.preventDefault();
        setIsTableView((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleSelectCell = useCallback((cellId: string) => {
    setSelectedCellId(cellId);
  }, []);

  const handleCloseSelection = useCallback(() => {
    setSelectedCellId(null);
    setIsInspectorOpen(false);
  }, []);

  const handleRunScenario = async (budget: number) => {
    setIsOptimizing(true);
    setScenarioError(null);
    try {
      const res = await climoraApi.optimizeScenario(CANONICAL_PROJECT_ID, budget);
      setScenarioResult(res);
      setShowScenarioOverlay(true);
    } catch (err: any) {
      setScenarioError(err.message || 'Failed to optimize scenario.');
    } finally {
      setIsOptimizing(false);
    }
  };

  const selectedCell = cells.find((c) => c.h3_cell_id === selectedCellId);
  const selectedRiskCell = riskCells.find((c) => c.h3_cell_id === selectedCellId);
  const selectedAllocation = allocations.find((a) => a.h3_cell_id === selectedCellId);
  const selectedScenarioAlloc = scenarioResult?.allocations.find((a) => a.h3_cell_id === selectedCellId);

  return (
    <div style={{ position: 'relative', width: '100%', height: 'calc(100vh - var(--nav-height))', overflow: 'hidden' }}>
      {/* Loading & Error States */}
      {isLoading && (
        <div
          style={{
            position: 'absolute',
            top: '16px',
            left: '50%',
            transform: 'translateX(-50%)',
            backgroundColor: 'var(--bg-panel)',
            border: '1px solid var(--border-hairline)',
            borderRadius: '4px',
            padding: '8px 16px',
            fontSize: '12px',
            color: 'var(--ink-secondary)',
            zIndex: 1100,
          }}
        >
          Loading Pune risk surface...
        </div>
      )}

      {errorMsg && (
        <div
          style={{
            position: 'absolute',
            top: '16px',
            left: '50%',
            transform: 'translateX(-50%)',
            backgroundColor: 'rgba(217, 107, 67, 0.2)',
            border: '1px solid var(--domain-thermal)',
            borderRadius: '4px',
            padding: '8px 16px',
            fontSize: '12px',
            color: 'var(--ink-primary)',
            zIndex: 1100,
          }}
        >
          {errorMsg}
        </div>
      )}

      {/* Main View: Spatial Map or Accessible Table */}
      {isTableView ? (
        <AccessibleTable
          cells={cells}
          allocations={allocations}
          selectedCellId={selectedCellId}
          onSelectCell={(id) => {
            setSelectedCellId(id);
            setIsInspectorOpen(true);
          }}
          onReturnToMap={() => setIsTableView(false)}
        />
      ) : (
        <>
          <SpatialMap
            riskCells={riskCells}
            cells={cells}
            puneBoundary={puneBoundary}
            allocations={allocations}
            scenarioAllocations={scenarioResult?.allocations || []}
            activeLayer={activeLayer}
            showFootprint={showFootprint}
            showScenarioOverlay={showScenarioOverlay}
            selectedCellId={selectedCellId}
            onSelectCell={handleSelectCell}
          />

          {/* Floating Scenario Control Card (Top Left) */}
          <div style={{ position: 'absolute', top: '20px', left: '20px', zIndex: 800 }}>
            <ScenarioControlCard
              currentBudget={scenarioBudget}
              onBudgetChange={setScenarioBudget}
              onRunScenario={handleRunScenario}
              isOptimizing={isOptimizing}
              scenarioResult={scenarioResult}
              onClearScenario={() => setScenarioResult(null)}
              error={scenarioError}
              showScenarioOverlay={showScenarioOverlay}
              onToggleScenarioOverlay={() => setShowScenarioOverlay(!showScenarioOverlay)}
            />
          </div>

          {/* Floating Map Controls (Top Right) */}
          <div style={{ position: 'absolute', top: '20px', right: '20px', zIndex: 800 }}>
            <MapControls
              activeLayer={activeLayer}
              onLayerChange={setActiveLayer}
              showFootprint={showFootprint}
              onToggleFootprint={() => setShowFootprint(!showFootprint)}
              onToggleTableView={() => setIsTableView(true)}
              isTableView={false}
            />
          </div>

          {/* Contextual Selection Card (Bottom Right Floating) */}
          {selectedCellId && !isInspectorOpen && !isMobile && (
            <div style={{ position: 'absolute', bottom: '40px', right: '20px', zIndex: 850 }}>
              <SelectionSummaryCard
                cellId={selectedCellId}
                allocation={selectedAllocation}
                baseline={selectedCell}
                onOpenInspector={() => setIsInspectorOpen(true)}
                onClose={handleCloseSelection}
              />
            </div>
          )}

          {/* Desktop / Laptop Inspector Drawer */}
          {!isMobile && (
            <CellInspector
              cellId={selectedCellId || ''}
              allocation={selectedAllocation}
              baseline={selectedCell}
              riskCell={selectedRiskCell}
              scenarioAllocation={selectedScenarioAlloc}
              isOpen={isInspectorOpen && Boolean(selectedCellId)}
              onClose={() => setIsInspectorOpen(false)}
              onOpenProvenance={() => setIsProvenanceOpen(true)}
            />
          )}

          {/* Mobile Bottom Sheet */}
          {isMobile && selectedCellId && (
            <MobileBottomSheet
              cellId={selectedCellId}
              allocation={selectedAllocation}
              baseline={selectedCell}
              onClose={handleCloseSelection}
              onOpenProvenance={() => setIsProvenanceOpen(true)}
            />
          )}

          {/* Contextual Map Metadata Line (Bottom Left) */}
          <div
            style={{
              position: 'absolute',
              bottom: '16px',
              left: '20px',
              backgroundColor: 'rgba(12, 14, 13, 0.75)',
              padding: '4px 10px',
              borderRadius: '3px',
              border: '1px solid var(--border-hairline)',
              fontSize: '11px',
              fontFamily: 'var(--font-mono)',
              color: 'var(--ink-secondary)',
              zIndex: 700,
              pointerEvents: 'none',
            }}
          >
            Pune AOI (3,181 H3 Cells) · Landsat 8 TIRS (2025) · Modeled Risk F-22
          </div>
        </>
      )}

      {/* Forensic Provenance Modal */}
      <ProvenanceModal
        isOpen={isProvenanceOpen}
        onClose={() => setIsProvenanceOpen(false)}
      />
    </div>
  );
};
