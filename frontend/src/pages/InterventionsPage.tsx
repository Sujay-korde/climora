import React, { useState } from 'react';
import { TruthBadge } from '../components/TruthBadge';
import { Link } from 'react-router-dom';

interface InterventionDetail {
  code: string;
  name: string;
  category: 'Nature-Based (Canopy)' | 'Albedo Modification' | 'Nature-Based (Ecology)' | 'Urban Drainage' | 'Sustainable Drainage';
  physicalUnit: string;
  unitCostInr: number;
  fixedMobilizationCostInr: number;
  minLotSize: number;
  maxCapacityFormula: string;
  coolingCoeff: string;
  coolingCoeffValue: number;
  susceptibilityFactor: number;
  spatialConstraint: string;
  eligibleCriteria: string;
  benefits: string[];
  implementationReqs: string[];
  monitoringMethod: string;
  scientificReference: string;
}

const INTERVENTION_CATALOG: InterventionDetail[] = [
  {
    code: 'street_tree_shade',
    name: 'Urban Street Tree Canopy Planting',
    category: 'Nature-Based (Canopy)',
    physicalUnit: 'tree count',
    unitCostInr: 3500.0,
    fixedMobilizationCostInr: 20000.0,
    minLotSize: 25,
    maxCapacityFormula: 'min(800, floor(2 * road_length / 15 * (1 - canopy_fraction)))',
    coolingCoeff: '-0.000714°C per tree (~0.05°C per 70 trees)',
    coolingCoeffValue: 0.000714,
    susceptibilityFactor: 0.05,
    spatialConstraint: 'Road verges and pedestrian rights-of-way (non-ground competing with rooftops)',
    eligibleCriteria: 'Eligible mesh cells with road_length_m > 0 and available planting capacity ≥ 25 trees',
    benefits: [
      'Direct solar radiation interception (80-90% attenuation of incident flux)',
      'Pedestrian thermal comfort (UTCI reduction of 2-5°C at ground level)',
      'Stormwater attenuation through canopy interception and root infiltration',
      'Long-term urban biodiversity and microclimate stabilization',
    ],
    implementationReqs: [
      'Native evergreen and semi-evergreen species (Azadirachta indica, Pongamia pinnata, Ficus racemosa)',
      'Minimum 1.5m root trench buffer from subsurface municipal utilities',
      '3-year sapling survival and irrigation maintenance service-level agreement',
    ],
    monitoringMethod: 'High-resolution optical drone orthomosaic (5cm) or Sentinel-2 NDVI canopy density index + geo-tagged field census',
    scientificReference: 'Bowler et al. (2010), Urban greening to cool towns and cities: A systematic review; Pune PMC Tree Authority Guidelines',
  },
  {
    code: 'cool_roof',
    name: 'High-Albedo Cool Roof Coating',
    category: 'Albedo Modification',
    physicalUnit: 'm² coated surface',
    unitCostInr: 250.0,
    fixedMobilizationCostInr: 25000.0,
    minLotSize: 500,
    maxCapacityFormula: '0.40 * norm_ndbi * cell_area_m2',
    coolingCoeff: '-0.000030°C per m² (~0.06°C per 2,000 m²)',
    coolingCoeffValue: 0.000030,
    susceptibilityFactor: 0.02,
    spatialConstraint: 'Rooftops only (independent of ground surface partitioning)',
    eligibleCriteria: 'Built-up density norm_ndbi > 0.05 and available roof area ≥ 500 m²',
    benefits: [
      'Immediate reduction in building surface temperature by 10-18°C',
      'Substantial indoor air cooling (2-4°C lower indoor temperature)',
      'Air conditioning load reduction of 15-25% in treated structures',
      'Mitigation of nighttime thermal re-radiation into urban boundary layer',
    ],
    implementationReqs: [
      'Elastomeric acrylic or polyurethane coating with Solar Reflectance Index (SRI) ≥ 104',
      'Structural roof substrate pre-inspection and leak repair prior to primer application',
      'Bi-annual wash-down protocol to maintain high solar reflectance',
    ],
    monitoringMethod: 'Satellite thermal infrared (Landsat-9 TIRS) or UAV radiometric thermal survey at solar noon',
    scientificReference: 'Santamouris (2014), Cooling the cities—a review of reflective and green roof mitigation technologies; Bureau of Energy Efficiency (BEE) India',
  },
  {
    code: 'green_corridor',
    name: 'Vegetative Micro-Corridor / Bioretention',
    category: 'Nature-Based (Ecology)',
    physicalUnit: 'm² planted ground',
    unitCostInr: 450.0,
    fixedMobilizationCostInr: 30000.0,
    minLotSize: 300,
    maxCapacityFormula: '0.10 * open_treatable_area_m2',
    coolingCoeff: '-0.000045°C per m² (~0.045°C per 1,000 m²)',
    coolingCoeffValue: 0.000045,
    susceptibilityFactor: 0.04,
    spatialConstraint: 'Ground surface: mutually exclusive with permeable surface and bioswales',
    eligibleCriteria: 'Vegetative deficit norm_ndvi_deficit > 0.15 and treatable open ground area ≥ 300 m²',
    benefits: [
      'Continuous microclimate cooling corridor connecting fragmented green spaces',
      'Enhanced urban infiltration reducing peak monsoon stormwater run-off',
      'Pollinator habitat and native ground-cover biodiversity restoration',
    ],
    implementationReqs: [
      'Multi-tiered vegetative structure: native shrubs, perennial grasses, ground cover',
      'Soil organic matter enrichment and porous topsoil preparation (300mm depth)',
      'Drip irrigation installation with rainwater harvesting catchment integration',
    ],
    monitoringMethod: 'Sentinel-2 Level-2A NDVI / EVI longitudinal temporal trend analysis (10m resolution)',
    scientificReference: 'Gill et al. (2007), Adapting cities for climate change: the role of the green infrastructure; IPCC AR6 WGII Chapter 6',
  },
  {
    code: 'permeable_surface',
    name: 'Permeable Interlocking Concrete Pavement',
    category: 'Urban Drainage',
    physicalUnit: 'm² paved area',
    unitCostInr: 850.0,
    fixedMobilizationCostInr: 40000.0,
    minLotSize: 200,
    maxCapacityFormula: '0.20 * road_length_m * 3.0m',
    coolingCoeff: '-0.000020°C per m²',
    coolingCoeffValue: 0.000020,
    susceptibilityFactor: 0.01,
    spatialConstraint: 'Ground surface: mutually exclusive with green corridors and bioswales',
    eligibleCriteria: 'norm_ndbi > 0.10 and road_length_m > 0 with capacity ≥ 200 m²',
    benefits: [
      'Rapid elimination of standing surface water and waterlogging',
      'Subsurface aquifer recharge along paved vehicular/pedestrian rights-of-way',
      'Reduction of pavement heat storage compared to impervious dark asphalt',
    ],
    implementationReqs: [
      'Interlocking concrete pavers with aggregate void spacers (infiltrability ≥ 1500 mm/hr)',
      'Open-graded crushed stone reservoir base course (ASTM No. 57 and No. 2)',
      'Periodic regenerative vacuum sweeping to prevent fine particulate clogging',
    ],
    monitoringMethod: 'In-situ ASTM C1701 surface infiltration rate testing + stormwater ponding video telemetry',
    scientificReference: 'Ferguson (2005), Porous Pavements; Indian Road Congress (IRC:SP:63) Paving Block Guidelines',
  },
  {
    code: 'bioswale',
    name: 'Bioswale Infiltration Trench',
    category: 'Sustainable Drainage',
    physicalUnit: 'm² bioretention channel',
    unitCostInr: 1200.0,
    fixedMobilizationCostInr: 50000.0,
    minLotSize: 100,
    maxCapacityFormula: '0.05 * road_length_m * 2.0m',
    coolingCoeff: '-0.000035°C per m²',
    coolingCoeffValue: 0.000035,
    susceptibilityFactor: 0.03,
    spatialConstraint: 'Ground surface: mutually exclusive with green corridors and permeable pavements',
    eligibleCriteria: 'road_length_m ≥ 100.0m with sufficient longitudinal gradient for linear bioretention',
    benefits: [
      'Sediment trapping and heavy metal filtering from roadway storm run-off',
      'Intense localized evaporative cooling along street corridors',
      'Reduction in municipal storm sewer overload during cloudburst events',
    ],
    implementationReqs: [
      'Engineered bioretention soil mix (85% sand, 10% silt/clay, 5% organic matter)',
      'Perforated underdrain pipe connecting to municipal stormwater network for overflow',
      'Dense erosion-resistant vegetation buffer along channel embankments',
    ],
    monitoringMethod: 'Flow-metered infiltration gauging + drone multispectral soil moisture index',
    scientificReference: 'Davis et al. (2009), Bioretention technology: Overview of current practice and future needs; EPA 841-B-00-005',
  },
];

export const InterventionsPage: React.FC = () => {
  const [selectedIntervention, setSelectedIntervention] = useState<InterventionDetail>(INTERVENTION_CATALOG[0]);

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '48px 32px 96px', display: 'flex', flexDirection: 'column', gap: '48px' }}>
      {/* Header */}
      <section style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--ink-secondary)' }}>
            Analytical Formulation F-24.1
          </span>
          <TruthBadge layer="MODELED" detail="Ratified Science Catalog" />
        </div>
        <h1
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: '44px',
            fontWeight: 400,
            lineHeight: 1.15,
            color: 'var(--ink-primary)',
          }}
        >
          Ratified Adaptation Intervention Library
        </h1>
        <p style={{ fontSize: '16px', color: 'var(--ink-secondary)', maxWidth: '800px', lineHeight: 1.6 }}>
          CLIMORA optimizes adaptation investments across five biophysically grounded nature-based and engineered intervention categories.
          Every intervention possesses verified engineering costs, spatial capacity bounds, minimum viable lot sizes, and peer-reviewed cooling coefficients.
        </p>
      </section>

      {/* Surface Compatibility Rule Banner */}
      <section
        style={{
          backgroundColor: 'var(--bg-panel)',
          border: '1px solid var(--border-hairline)',
          borderRadius: '8px',
          padding: '20px 24px',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ color: 'var(--accent-focal)', fontSize: '13px', fontWeight: 600 }}>
            Mathematical Hard Constraint (F-24.3): Ground-Surface Spatial Exclusivity
          </span>
        </div>
        <p style={{ fontSize: '13px', color: 'var(--ink-secondary)', lineHeight: 1.5 }}>
          Interventions competing for open urban ground surface share a strict non-overlapping capacity inequality:
          <code style={{ display: 'block', backgroundColor: 'var(--bg-card)', padding: '8px 12px', marginTop: '6px', borderRadius: '4px', fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--ink-primary)' }}>
            (q_corridor / Q_max_corridor) + (q_permeable / Q_max_permeable) + (q_bioswale / Q_max_bioswale) ≤ 1.0
          </code>
          Rooftop cool coatings and street verge trees operate in independent physical strata and do not compete for open ground footprint.
        </p>
      </section>

      {/* Main Catalog Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(320px, 380px) 1fr', gap: '32px', alignItems: 'start' }}>
        {/* Intervention Selector List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--ink-tertiary)' }}>
            Select Intervention Category (5 Ratified)
          </span>
          {INTERVENTION_CATALOG.map((inv) => {
            const isSelected = selectedIntervention.code === inv.code;
            return (
              <button
                key={inv.code}
                onClick={() => setSelectedIntervention(inv)}
                style={{
                  textAlign: 'left',
                  padding: '16px 20px',
                  backgroundColor: isSelected ? 'var(--bg-card)' : 'var(--bg-panel)',
                  border: isSelected ? '1px solid var(--accent-focal)' : '1px solid var(--border-hairline)',
                  borderRadius: '6px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '11px', color: 'var(--ink-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    {inv.category}
                  </span>
                  <span className="font-tabular" style={{ fontSize: '12px', color: 'var(--accent-focal)', fontWeight: 500 }}>
                    ₹{inv.unitCostInr.toLocaleString('en-IN')}/{inv.physicalUnit.split(' ')[0]}
                  </span>
                </div>
                <span style={{ fontSize: '15px', fontWeight: 600, color: 'var(--ink-primary)' }}>
                  {inv.name}
                </span>
                <span style={{ fontSize: '12px', color: 'var(--ink-tertiary)', lineHeight: 1.4 }}>
                  Min lot: {inv.minLotSize} {inv.physicalUnit} · Fixed mobilization: ₹{inv.fixedMobilizationCostInr.toLocaleString('en-IN')}
                </span>
              </button>
            );
          })}
        </div>

        {/* Selected Intervention Detailed Specification Dossier */}
        <div
          style={{
            backgroundColor: 'var(--bg-card)',
            border: '1px solid var(--border-hairline)',
            borderRadius: '8px',
            padding: '32px',
            display: 'flex',
            flexDirection: 'column',
            gap: '24px',
          }}
        >
          <div style={{ borderBottom: '1px solid var(--border-hairline)', paddingBottom: '20px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--accent-focal)' }}>
              {selectedIntervention.category}
            </span>
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '28px', color: 'var(--ink-primary)', fontWeight: 400 }}>
              {selectedIntervention.name}
            </h2>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--ink-secondary)' }}>
              Intervention Code: {selectedIntervention.code}
            </span>
          </div>

          {/* Key Parameters Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px' }}>
            <div style={{ backgroundColor: 'var(--bg-panel)', padding: '14px 16px', borderRadius: '6px', border: '1px solid var(--border-hairline-subtle)' }}>
              <span style={{ fontSize: '11px', color: 'var(--ink-secondary)', display: 'block', marginBottom: '4px' }}>Unit Cost</span>
              <span className="font-tabular" style={{ fontSize: '18px', fontWeight: 600, color: 'var(--ink-primary)' }}>
                ₹{selectedIntervention.unitCostInr.toLocaleString('en-IN')}
              </span>
              <span style={{ fontSize: '11px', color: 'var(--ink-tertiary)', display: 'block' }}>per {selectedIntervention.physicalUnit}</span>
            </div>

            <div style={{ backgroundColor: 'var(--bg-panel)', padding: '14px 16px', borderRadius: '6px', border: '1px solid var(--border-hairline-subtle)' }}>
              <span style={{ fontSize: '11px', color: 'var(--ink-secondary)', display: 'block', marginBottom: '4px' }}>Fixed Mobilization</span>
              <span className="font-tabular" style={{ fontSize: '18px', fontWeight: 600, color: 'var(--ink-primary)' }}>
                ₹{selectedIntervention.fixedMobilizationCostInr.toLocaleString('en-IN')}
              </span>
              <span style={{ fontSize: '11px', color: 'var(--ink-tertiary)', display: 'block' }}>per treated hexagon cell</span>
            </div>

            <div style={{ backgroundColor: 'var(--bg-panel)', padding: '14px 16px', borderRadius: '6px', border: '1px solid var(--border-hairline-subtle)' }}>
              <span style={{ fontSize: '11px', color: 'var(--ink-secondary)', display: 'block', marginBottom: '4px' }}>Minimum Viable Lot</span>
              <span className="font-tabular" style={{ fontSize: '18px', fontWeight: 600, color: 'var(--ink-primary)' }}>
                {selectedIntervention.minLotSize}
              </span>
              <span style={{ fontSize: '11px', color: 'var(--ink-tertiary)', display: 'block' }}>{selectedIntervention.physicalUnit}</span>
            </div>

            <div style={{ backgroundColor: 'var(--bg-panel)', padding: '14px 16px', borderRadius: '6px', border: '1px solid var(--border-hairline-subtle)' }}>
              <span style={{ fontSize: '11px', color: 'var(--ink-secondary)', display: 'block', marginBottom: '4px' }}>Susceptibility Factor</span>
              <span className="font-tabular" style={{ fontSize: '18px', fontWeight: 600, color: 'var(--domain-thermal)' }}>
                {selectedIntervention.susceptibilityFactor}
              </span>
              <span style={{ fontSize: '11px', color: 'var(--ink-tertiary)', display: 'block' }}>v_a in response equation</span>
            </div>
          </div>

          {/* Mathematical & Physical Capacity Formula */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--ink-primary)' }}>
              Carrying Capacity Formulation (Q_max):
            </span>
            <code style={{ backgroundColor: 'var(--bg-panel)', padding: '10px 14px', borderRadius: '4px', fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--accent-focal)' }}>
              {selectedIntervention.maxCapacityFormula}
            </code>
          </div>

          {/* Expected Biophysical Cooling Effect */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--ink-primary)' }}>
              Modeled Cooling Coefficient (e_a):
            </span>
            <p style={{ fontSize: '13px', color: 'var(--ink-secondary)', lineHeight: 1.5 }}>
              {selectedIntervention.coolingCoeff}
            </p>
          </div>

          {/* Measurable Urban Benefits */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--ink-primary)' }}>
              Measurable Climate & Resilience Benefits:
            </span>
            <ul style={{ paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '13px', color: 'var(--ink-secondary)' }}>
              {selectedIntervention.benefits.map((b, i) => (
                <li key={i}>{b}</li>
              ))}
            </ul>
          </div>

          {/* Implementation & Engineering Specifications */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--ink-primary)' }}>
              Contractor Delivery & Material Specifications:
            </span>
            <ul style={{ paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '13px', color: 'var(--ink-secondary)' }}>
              {selectedIntervention.implementationReqs.map((req, i) => (
                <li key={i}>{req}</li>
              ))}
            </ul>
          </div>

          {/* MRV & Scientific Provenance */}
          <div style={{ backgroundColor: 'var(--bg-panel)', padding: '16px', borderRadius: '6px', border: '1px solid var(--border-hairline-subtle)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--ink-secondary)' }}>
              Post-Implementation Verification & Monitoring Protocol
            </span>
            <p style={{ fontSize: '12px', color: 'var(--ink-primary)', lineHeight: 1.5 }}>
              {selectedIntervention.monitoringMethod}
            </p>
            <span style={{ fontSize: '11px', color: 'var(--ink-tertiary)', marginTop: '4px' }}>
              Scientific Provenance: {selectedIntervention.scientificReference}
            </span>
          </div>

          {/* Action Link to Optimizer */}
          <div style={{ display: 'flex', gap: '16px', marginTop: '12px' }}>
            <Link
              to="/optimizer"
              style={{
                padding: '10px 20px',
                backgroundColor: 'var(--ink-primary)',
                color: 'var(--bg-ground)',
                fontSize: '13px',
                fontWeight: 600,
                borderRadius: '4px',
              }}
            >
              Configure in Portfolio Optimizer →
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

