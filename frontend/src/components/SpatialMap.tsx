import React, { useMemo } from 'react';
import { MapContainer, TileLayer, Polygon, Tooltip, GeoJSON } from 'react-leaflet';
import { cellToBoundary } from 'h3-js';
import { LayerMode } from './MapControls';
import { AllocationItem, BaselineCell, RiskSurfaceCell, ScenarioAllocationItem } from '../types/api';

interface SpatialMapProps {
  riskCells?: RiskSurfaceCell[];
  cells?: BaselineCell[];
  puneBoundary?: any;
  allocations: AllocationItem[];
  scenarioAllocations?: ScenarioAllocationItem[];
  activeLayer: LayerMode;
  showFootprint: boolean;
  showScenarioOverlay?: boolean;
  selectedCellId: string | null;
  onSelectCell: (cellId: string) => void;
}

interface StandardMapCell {
  h3_cell_id: string;
  risk_i: number;
  H_i: number;
  E_i: number;
  V_i: number;
  lst_2025: number;
  population_2020: number;
  lisa_cluster: string;
  is_eligible: boolean;
}

export const SpatialMap: React.FC<SpatialMapProps> = ({
  riskCells,
  cells,
  puneBoundary,
  allocations,
  scenarioAllocations = [],
  activeLayer,
  showFootprint,
  showScenarioOverlay = true,
  selectedCellId,
  onSelectCell,
}) => {
  const footprintSet = useMemo(() => {
    return new Set(allocations.map((a) => a.h3_cell_id));
  }, [allocations]);

  const scenarioSet = useMemo(() => {
    return new Set(scenarioAllocations.map((s) => s.h3_cell_id));
  }, [scenarioAllocations]);

  // Normalize cell sources: prefer full riskCells surface (3,181 cells)
  const displayCells: StandardMapCell[] = useMemo(() => {
    if (riskCells && riskCells.length > 0) {
      return riskCells.map((c) => ({
        h3_cell_id: c.h3_cell_id,
        risk_i: c.risk_i,
        H_i: c.H_i,
        E_i: c.E_i,
        V_i: c.V_i,
        lst_2025: c.lst_2025,
        population_2020: c.population_2020,
        lisa_cluster: c.lisa_cluster,
        is_eligible: c.is_eligible,
      }));
    }
    if (cells && cells.length > 0) {
      return cells.map((c) => ({
        h3_cell_id: c.h3_cell_id,
        risk_i: c.metrics?.risk_i?.value || 0.1,
        H_i: c.metrics?.H_i?.value || 0.5,
        E_i: c.metrics?.E_i?.value || 0.5,
        V_i: c.metrics?.V_i?.value || 0.5,
        lst_2025: c.metrics?.lst_2025?.value || 45,
        population_2020: c.metrics?.population_2020?.value || 0,
        lisa_cluster: c.metrics?.lisa_cluster?.value || 'Not Significant',
        is_eligible: true,
      }));
    }
    return [];
  }, [riskCells, cells]);

  // Multi-stop color interpolation helper for high visual contrast
  const interpolateRgb = (c1: [number, number, number], c2: [number, number, number], factor: number): string => {
    const f = Math.max(0, Math.min(1, factor));
    const r = Math.round(c1[0] + f * (c2[0] - c1[0]));
    const g = Math.round(c1[1] + f * (c2[1] - c1[1]));
    const b = Math.round(c1[2] + f * (c2[2] - c1[2]));
    return `rgb(${r}, ${g}, ${b})`;
  };

  const getRampColor = (stops: { stop: number; color: [number, number, number] }[], t: number): string => {
    const clamped = Math.max(0, Math.min(1, t));
    for (let i = 0; i < stops.length - 1; i++) {
      if (clamped >= stops[i].stop && clamped <= stops[i + 1].stop) {
        const localT = (clamped - stops[i].stop) / (stops[i + 1].stop - stops[i].stop);
        return interpolateRgb(stops[i].color, stops[i + 1].color, localT);
      }
    }
    return interpolateRgb(stops[stops.length - 2].color, stops[stops.length - 1].color, 1);
  };

  // Color ramps based on empirical 5th to 95th percentiles of Pune canonical data
  const getCellFillColor = (cell: StandardMapCell): string => {
    if (activeLayer === 'thermal') {
      const lst = cell.lst_2025 || 45;
      // 5th percentile = 41.5°C, median = 45.8°C, 95th percentile = 51.3°C
      const t = Math.max(0, Math.min(1, (lst - 40.0) / 12.0));
      return getRampColor([
        { stop: 0.0, color: [59, 130, 246] },   // Cool Blue #3B82F6 (river / canopy)
        { stop: 0.35, color: [234, 179, 8] },   // Amber Gold #EAB308
        { stop: 0.65, color: [249, 115, 22] },  // Vivid Orange #F97316
        { stop: 1.0, color: [220, 38, 38] },    // Severe Crimson #DC2626 (urban heat island)
      ], t);
    }
    if (activeLayer === 'exposure') {
      const pop = cell.population_2020 || 0;
      // 5th percentile = 128, median = 1,055, 95th percentile = 4,178
      const t = Math.max(0, Math.min(1, (pop - 100.0) / 4400.0));
      return getRampColor([
        { stop: 0.0, color: [20, 184, 166] },   // Teal #14B8A6 (sparse periphery)
        { stop: 0.25, color: [6, 182, 212] },   // Cyan #06B6D4
        { stop: 0.65, color: [59, 130, 246] },  // Electric Blue #3B82F6
        { stop: 1.0, color: [139, 92, 246] },   // Deep Violet #8B5CF6 (dense settlement)
      ], t);
    }
    // Risk surface F-22 (H * E * V)
    const risk = cell.risk_i || 0.05;
    // 5th percentile = 0.0065, median = 0.0446, 95th percentile = 0.187
    const t = Math.max(0, Math.min(1, (risk - 0.005) / 0.215));
    return getRampColor([
      { stop: 0.0, color: [132, 204, 22] },   // Sage Lime #84CC16 (low risk)
      { stop: 0.25, color: [245, 158, 11] },  // Golden Amber #F59E0B (median risk)
      { stop: 0.60, color: [234, 88, 12] },   // Intense Orange #EA580C (elevated risk)
      { stop: 1.0, color: [190, 18, 60] },    // Deep Carmine #BE123C (critical acute risk)
    ], t);
  };

  // Basemap provider: Use CARTO Voyager when key is supplied, else clean public OpenStreetMap
  const cartoKey = import.meta.env.VITE_CARTO_BASEMAP_KEY;
  const tileUrl = cartoKey
    ? `https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png?api_key=${cartoKey}`
    : 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
  const tileAttribution = cartoKey
    ? '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions" target="_blank" rel="noreferrer">CARTO</a>'
    : '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a> contributors';

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <MapContainer
        center={[18.5204, 73.8567]}
        zoom={12}
        minZoom={10}
        maxZoom={16}
        scrollWheelZoom={true}
        style={{ width: '100%', height: '100%', background: '#0C0E0D' }}
        attributionControl={true}
      >
        <TileLayer
          url={tileUrl}
          subdomains="abcd"
          maxZoom={19}
          attribution={tileAttribution}
        />

        {/* Pune AOI Boundary Context */}
        {puneBoundary && (
          <GeoJSON
            key="pune-aoi-boundary"
            data={puneBoundary}
            style={{
              color: '#0EA5E9',
              weight: 2,
              dashArray: '5, 5',
              fill: false,
              interactive: false,
            }}
          />
        )}

        {/* Citywide H3 Analytical Mesh Polygons */}
        {displayCells.map((cell) => {
          const isSelected = cell.h3_cell_id === selectedCellId;
          const isInCanonical = footprintSet.has(cell.h3_cell_id);
          const isInScenario = scenarioSet.has(cell.h3_cell_id);

          let boundary: [number, number][] = [];
          try {
            boundary = cellToBoundary(cell.h3_cell_id) as [number, number][];
          } catch {
            return null;
          }

          // Visual Hierarchy Styling per Phase 2C.2R
          let strokeColor = 'rgba(255, 255, 255, 0.15)';
          let weight = 0.5;
          let dashArray: string | undefined = undefined;
          let fillOpacity = cell.is_eligible ? 0.65 : 0.18;

          if (isSelected) {
            strokeColor = '#C8FF3B'; // Acid Lime strictly reserved for selected active focus (<0.5%)
            weight = 3.5;
            fillOpacity = 0.92;
          } else if (showScenarioOverlay && isInScenario) {
            strokeColor = '#4CC9F0'; // Electric Cyan for modeled scenario overlay
            weight = 2.5;
            dashArray = '3, 3';
            fillOpacity = 0.82;
          } else if (showFootprint && isInCanonical) {
            strokeColor = '#3B7A57'; // Botanical Sage for canonical municipal plan
            weight = 2;
            fillOpacity = 0.75;
          }

          const fillColor = getCellFillColor(cell);

          return (
            <Polygon
              key={cell.h3_cell_id}
              positions={boundary}
              pathOptions={{
                color: strokeColor,
                weight,
                dashArray,
                fillColor,
                fillOpacity,
              }}
              eventHandlers={{
                click: () => onSelectCell(cell.h3_cell_id),
              }}
            >
              <Tooltip sticky direction="top" className="climora-tooltip">
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', padding: '4px 6px' }}>
                  <div style={{ fontWeight: 600, color: 'var(--ink-primary)' }}>{cell.h3_cell_id}</div>
                  <div>Modeled Risk: {cell.risk_i.toFixed(4)}</div>
                  <div>Observed LST: {cell.lst_2025.toFixed(1)}°C</div>
                  <div>Population: {cell.population_2020.toLocaleString()}</div>
                  {cell.lisa_cluster && cell.lisa_cluster !== 'Not Significant' && (
                    <div style={{ color: 'var(--domain-thermal)' }}>LISA: {cell.lisa_cluster}</div>
                  )}
                  {isInCanonical && <div style={{ color: '#3B7A57' }}>● Canonical Footprint</div>}
                  {isInScenario && <div style={{ color: '#4CC9F0' }}>◆ Modeled Scenario Footprint</div>}
                </div>
              </Tooltip>
            </Polygon>
          );
        })}
      </MapContainer>

      {/* On-Map Floating Metric Legend */}
      <div
        style={{
          position: 'absolute',
          bottom: '24px',
          left: '24px',
          zIndex: 1000,
          background: 'rgba(12, 14, 13, 0.88)',
          backdropFilter: 'blur(8px)',
          border: '1px solid rgba(255, 255, 255, 0.12)',
          borderRadius: '6px',
          padding: '8px 12px',
          minWidth: '220px',
          fontFamily: 'var(--font-mono)',
          fontSize: '11px',
          color: 'var(--ink-primary)',
          boxShadow: '0 4px 16px rgba(0, 0, 0, 0.4)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px', fontWeight: 500 }}>
          <span>
            {activeLayer === 'thermal' && 'Thermal (LST 2025)'}
            {activeLayer === 'exposure' && 'Exposure (WorldPop)'}
            {activeLayer === 'risk' && 'Climate Risk (F-22)'}
          </span>
          <span style={{ color: 'var(--ink-secondary)', fontSize: '10px' }}>
            {activeLayer === 'thermal' && '°C'}
            {activeLayer === 'exposure' && 'people/cell'}
            {activeLayer === 'risk' && 'H × E × V'}
          </span>
        </div>
        <div
          style={{
            height: '8px',
            borderRadius: '4px',
            marginBottom: '4px',
            background:
              activeLayer === 'thermal'
                ? 'linear-gradient(to right, #3B82F6, #EAB308, #F97316, #DC2626)'
                : activeLayer === 'exposure'
                ? 'linear-gradient(to right, #14B8A6, #06B6D4, #3B82F6, #8B5CF6)'
                : 'linear-gradient(to right, #84CC16, #F59E0B, #EA580C, #BE123C)',
          }}
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--ink-secondary)', fontSize: '10px' }}>
          <span>
            {activeLayer === 'thermal' && '≤40°C'}
            {activeLayer === 'exposure' && '≤100'}
            {activeLayer === 'risk' && '≤0.01'}
          </span>
          <span>
            {activeLayer === 'thermal' && '46°C'}
            {activeLayer === 'exposure' && '1,800'}
            {activeLayer === 'risk' && '0.08'}
          </span>
          <span>
            {activeLayer === 'thermal' && '≥52°C'}
            {activeLayer === 'exposure' && '≥4,500'}
            {activeLayer === 'risk' && '≥0.22'}
          </span>
        </div>
      </div>
    </div>
  );
};
