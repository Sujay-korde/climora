"""
CLIMORA - Phase 1H: Bankable Project Proposal & MRV Architecture Test Suite
Test File: test_phase_1h_project_mrv.py

Tests verifying:
1. Project lineage and optimization run traceability
2. Allocation immutability and revision branching
3. Project state machine transitions and invalid jump rejection
4. Implementation deviation and deviation rate calculation
5. Truth-layer separation (Observed vs Derived vs Modeled vs Verified)
6. Strict MRV verification gating (cannot verify without required evidence)
7. End-to-end data provenance tracking
8. Synthetic demo MRV fixture anti-contamination guard
9. Ward independence decoupling
10. Proposal document structure (13 mandatory sections)
"""

import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from ingestion.common import calculate_sha256
from processing.project_mrv import (
    ProjectLifecycleState,
    VerificationState,
    ImplementationEvent,
    ObservationEvent,
    MRVQualityControlResult,
    VerificationEvent,
    MRVQualityControlEngine,
    ProjectStateMachine,
    AllocationRevisionTracker,
    ProjectProposalBuilder,
    SyntheticMRVFixtureGenerator,
    CANONICAL_ALLOCATION_PARQUET,
    CANONICAL_FEATURE_MATRIX,
    CANONICAL_RUN_MANIFEST,
    PROJECT_MRV_CONTRACT,
    SYNTHETIC_MRV_TAG,
    doy_to_date,
)


@pytest.fixture(scope="module")
def project_contract():
    """Load canonical Phase 1H Project & MRV Architecture contract."""
    assert PROJECT_MRV_CONTRACT.exists(), f"Contract missing: {PROJECT_MRV_CONTRACT}"
    with open(PROJECT_MRV_CONTRACT, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


@pytest.fixture(scope="module")
def canonical_proposal_doc():
    """Build and return the canonical 13-section project proposal document."""
    return ProjectProposalBuilder.build_from_optimization_run()


def test_contract_manifest_integrity(project_contract):
    """Test 1: Verify contract manifest schema, states, and truth layers."""
    assert project_contract["schema_version"] == "1.0.0"
    assert project_contract["phase"] == "Phase 1H"
    assert project_contract["status"] == "RATIFIED_PROJECT_MRV_ARCHITECTURE_GATE_PASSED"

    # Truth layers
    truth_layers = project_contract["truth_layer_taxonomy"]
    for tl in ["OBSERVED", "DERIVED", "MODELED", "VERIFIED"]:
        assert tl in truth_layers, f"Truth layer {tl} missing"

    # Proposal sections
    sections = project_contract["proposal_document_structure"]["mandatory_sections"]
    assert len(sections) == 13


def test_project_lineage_and_optimization_traceability(canonical_proposal_doc):
    """Test 2: Verify that project proposal references immutable upstream optimization run."""
    with open(CANONICAL_RUN_MANIFEST, "r", encoding="utf-8") as f:
        run_manifest = json.load(f)

    expected_run_id = run_manifest["run_id"]
    doc_run_id = canonical_proposal_doc["section_13_optimization_run_traceability"]["optimization_run_id"]
    assert doc_run_id == expected_run_id

    # Checksum provenance
    prov = canonical_proposal_doc["section_12_data_lake_lineage_and_provenance"]
    assert prov["feature_matrix_sha256"] == run_manifest["input_artifacts"]["feature_matrix_sha256"]
    assert prov["risk_surface_sha256"] == run_manifest["input_artifacts"]["risk_surface_sha256"]
    assert prov["allocation_parquet_sha256"] == run_manifest["output_artifacts"]["allocation_parquet_sha256"]


def test_allocation_immutability_and_revision_branching():
    """Test 3: Verify that original optimization allocation is immutable and revisions branch cleanly."""
    df_alloc = pd.read_parquet(CANONICAL_ALLOCATION_PARQUET)
    tracker = AllocationRevisionTracker(df_alloc)

    orig_df = tracker.original_allocation
    target_cell = df_alloc.iloc[0]["h3_cell_id"]
    orig_qty = float(df_alloc.iloc[0]["quantity"])

    # Propose an adjusted quantity
    new_qty = orig_qty + 20.0
    rev = tracker.propose_revision(
        project_id="PROJ-TEST",
        h3_cell_id=target_cell,
        intervention_code="street_tree_shade",
        proposed_quantity=new_qty,
        reason="Field inspection identified additional roadway verge space.",
        author="Municipal Urban Forester",
    )

    assert rev.original_quantity == orig_qty
    assert rev.proposed_quantity == new_qty
    assert rev.revision_delta == 20.0

    # 1. Original allocation must remain 100% untouched
    pd.testing.assert_frame_equal(tracker.original_allocation, orig_df)
    assert tracker.original_allocation.iloc[0]["quantity"] == orig_qty

    # 2. Effective allocation reflects the proposed modification
    eff_df = tracker.get_effective_allocation()
    assert eff_df.iloc[0]["quantity"] == new_qty
    assert bool(eff_df.iloc[0]["is_revised"]) is True


def test_project_state_machine_valid_and_invalid_transitions():
    """Test 4: Verify state machine rules and reject arbitrary/illegal jumps."""
    # Valid forward step: DISCOVERED -> ASSESSED
    ok, msg = ProjectStateMachine.can_transition(
        ProjectLifecycleState.DISCOVERED, ProjectLifecycleState.ASSESSED
    )
    assert ok, msg

    # Invalid jump: DISCOVERED -> VERIFIED
    ok, msg = ProjectStateMachine.can_transition(
        ProjectLifecycleState.DISCOVERED, ProjectLifecycleState.VERIFIED
    )
    assert not ok
    assert "Illegal state transition" in msg

    # Invalid jump: PROPOSED -> VERIFIED (skipping funding and implementation)
    ok, msg = ProjectStateMachine.can_transition(
        ProjectLifecycleState.PROPOSED, ProjectLifecycleState.VERIFIED
    )
    assert not ok

    # Guard check: PROPOSED -> FUNDED without sanction info
    ok, msg = ProjectStateMachine.can_transition(
        ProjectLifecycleState.PROPOSED, ProjectLifecycleState.FUNDED, context={}
    )
    assert not ok
    assert "Transition to FUNDED requires 'sanction_id'" in msg

    # Guard check: PROPOSED -> FUNDED with valid sanction info
    ok, msg = ProjectStateMachine.can_transition(
        ProjectLifecycleState.PROPOSED,
        ProjectLifecycleState.FUNDED,
        context={"sanction_id": "PMC-SANC-2025-09", "approved_budget_inr": 10000000.0},
    )
    assert ok


def test_implementation_deviation_calculation():
    """Test 5: Verify planned vs implemented quantities and deviation metrics across all 5 domain cases."""
    # Case 1: Under-delivery (implemented < planned)
    e1 = ImplementationEvent(
        event_id="EVT-1",
        project_id="PROJ-1",
        h3_cell_id="c0",
        intervention_code="street_tree_shade",
        planned_quantity=100.0,
        implemented_quantity=80.0,
        quantity_unit="tree_count",
        contractor_id="CONT-01",
        completion_date="2026-03-31",
        evidence_uri="s3://climora/evidence/evt-1.pdf",
    )
    assert e1.deviation == -20.0
    assert np.isclose(e1.deviation_rate, -0.20)

    # Case 2: Over-delivery (implemented > planned)
    e2 = ImplementationEvent(
        event_id="EVT-2",
        project_id="PROJ-1",
        h3_cell_id="c1",
        intervention_code="street_tree_shade",
        planned_quantity=50.0,
        implemented_quantity=60.0,
        quantity_unit="tree_count",
        contractor_id="CONT-01",
        completion_date="2026-03-31",
        evidence_uri="s3://climora/evidence/evt-2.pdf",
    )
    assert e2.deviation == 10.0
    assert np.isclose(e2.deviation_rate, 0.20)

    # Case 3: Exact delivery (implemented == planned)
    e3 = ImplementationEvent(
        event_id="EVT-3",
        project_id="PROJ-1",
        h3_cell_id="c2",
        intervention_code="street_tree_shade",
        planned_quantity=75.0,
        implemented_quantity=75.0,
        quantity_unit="tree_count",
        contractor_id="CONT-01",
        completion_date="2026-03-31",
        evidence_uri="s3://climora/evidence/evt-3.pdf",
    )
    assert e3.deviation == 0.0
    assert e3.deviation_rate == 0.0

    # Case 4: Zero planned and zero implemented (planned == 0, implemented == 0)
    e4 = ImplementationEvent(
        event_id="EVT-4",
        project_id="PROJ-1",
        h3_cell_id="c3",
        intervention_code="street_tree_shade",
        planned_quantity=0.0,
        implemented_quantity=0.0,
        quantity_unit="tree_count",
        contractor_id="CONT-01",
        completion_date="2026-03-31",
        evidence_uri="s3://climora/evidence/evt-4.pdf",
    )
    assert e4.deviation == 0.0
    assert e4.deviation_rate is None  # Undefined/not-applicable; do not fabricate rate

    # Case 5: Zero planned and positive implemented (planned == 0, implemented > 0)
    e5 = ImplementationEvent(
        event_id="EVT-5",
        project_id="PROJ-1",
        h3_cell_id="c4",
        intervention_code="street_tree_shade",
        planned_quantity=0.0,
        implemented_quantity=25.0,
        quantity_unit="tree_count",
        contractor_id="CONT-01",
        completion_date="2026-03-31",
        evidence_uri="s3://climora/evidence/evt-5.pdf",
    )
    assert e5.deviation == 25.0
    assert e5.deviation_rate is None  # Undefined/not-applicable; do not divide by zero or return inf


def test_mrv_quality_control_audits():
    """Test 6: Verify the 5 mandatory MRV quality control checks, metric-specific sensor compatibility, and cloud masking semantics."""
    valid_obs = ObservationEvent(
        observation_id="OBS-1",
        sensor_platform="Landsat-9-TIRS",
        acquisition_date="2026-04-18",
        doy=108,  # Target 105, offset = 3 <= 15
        spatial_resolution_m=30.0,
        cloud_cover_aoi_pct=2.5,  # <= 5.0% ceiling
        quality_flags_passed=True,  # 100% pixel masking passed
        asset_uri="s3://climora/obs/obs-1.tif",
    )
    # Perfect thermal LST observation
    qc = MRVQualityControlEngine.audit_observation(
        observation=valid_obs,
        treated_cell_count=28,
        observed_cell_count=28,
        target_metric="lst",
        baseline_target_doy=105,
    )
    assert qc.all_passed is True
    assert len(qc.violations) == 0

    # Incomplete spatial coverage (e.g. edge swath truncation)
    qc_bad_spatial = MRVQualityControlEngine.audit_observation(
        observation=valid_obs,
        treated_cell_count=28,
        observed_cell_count=20,  # missing 8 cells
        target_metric="lst",
    )
    assert qc_bad_spatial.all_passed is False
    assert any("Spatial coverage incomplete" in v for v in qc_bad_spatial.violations)

    # Cloud contaminated observation (> 5% ceiling)
    cloudy_obs = ObservationEvent(
        observation_id="OBS-2",
        sensor_platform="Landsat-9-TIRS",
        acquisition_date="2026-04-18",
        doy=108,
        spatial_resolution_m=30.0,
        cloud_cover_aoi_pct=12.5,  # Exceeds 5.0% ceiling
        quality_flags_passed=True,
        asset_uri="s3://climora/obs/obs-2.tif",
    )
    qc_cloud = MRVQualityControlEngine.audit_observation(
        observation=cloudy_obs, treated_cell_count=28, observed_cell_count=28, target_metric="lst"
    )
    assert qc_cloud.all_passed is False
    assert any("Cloud/shadow contamination" in v for v in qc_cloud.violations)

    # Cloud masked failure (unmasked invalid pixels detected despite low cloud cover)
    unmasked_obs = ObservationEvent(
        observation_id="OBS-2B",
        sensor_platform="Landsat-9-TIRS",
        acquisition_date="2026-04-18",
        doy=108,
        spatial_resolution_m=30.0,
        cloud_cover_aoi_pct=3.0,  # Below 5% ceiling
        quality_flags_passed=False,  # Unmasked invalid pixels
        asset_uri="s3://climora/obs/obs-2b.tif",
    )
    qc_unmasked = MRVQualityControlEngine.audit_observation(
        observation=unmasked_obs, treated_cell_count=28, observed_cell_count=28, target_metric="lst"
    )
    assert qc_unmasked.all_passed is False
    assert any("Pixel quality flags failed" in v for v in qc_unmasked.violations)

    # Metric-Specific Sensor Compatibility Check:
    # Sentinel-2 MUST FAIL for thermal LST because it has no thermal payload
    sentinel_obs = ObservationEvent(
        observation_id="OBS-S2",
        sensor_platform="Sentinel-2B-MSI",
        acquisition_date="2026-04-19",
        doy=109,
        spatial_resolution_m=10.0,
        cloud_cover_aoi_pct=0.0,
        quality_flags_passed=True,
        asset_uri="s3://climora/obs/s2.tif",
    )
    qc_s2_thermal = MRVQualityControlEngine.audit_observation(
        observation=sentinel_obs, treated_cell_count=28, observed_cell_count=28, target_metric="lst"
    )
    assert qc_s2_thermal.all_passed is False
    assert any("has no thermal infrared payload" in v for v in qc_s2_thermal.violations)

    # Sentinel-2 MUST SUCCEED for optical NDVI metric
    qc_s2_optical = MRVQualityControlEngine.audit_observation(
        observation=sentinel_obs, treated_cell_count=28, observed_cell_count=28, target_metric="ndvi"
    )
    assert qc_s2_optical.all_passed is True

    # Out of season observation (e.g. monsoon scene in July DOY 200)
    monsoon_obs = ObservationEvent(
        observation_id="OBS-3",
        sensor_platform="Landsat-9-TIRS",
        acquisition_date="2026-07-19",
        doy=200,  # offset 95 days >> 15 days
        spatial_resolution_m=30.0,
        cloud_cover_aoi_pct=0.0,
        quality_flags_passed=True,
        asset_uri="s3://climora/obs/obs-3.tif",
    )
    qc_monsoon = MRVQualityControlEngine.audit_observation(
        observation=monsoon_obs, treated_cell_count=28, observed_cell_count=28, target_metric="lst"
    )
    assert qc_monsoon.all_passed is False
    assert any("Temporal offset" in v for v in qc_monsoon.violations)


def test_verification_gating_and_synthetic_isolation():
    """Test 7, 8: Verify that verification gating rejects incomplete evidence and synthetic demo data."""
    # Context with missing verification event
    impl_event = ImplementationEvent(
        event_id="EVT-1",
        project_id="PROJ-1",
        h3_cell_id="c0",
        intervention_code="street_tree_shade",
        planned_quantity=84.0,
        implemented_quantity=84.0,
        quantity_unit="tree_count",
        contractor_id="CONT-01",
        completion_date="2026-04-01",
        evidence_uri="s3://climora/evt-1.pdf",
    )
    obs_event = ObservationEvent(
        observation_id="OBS-1",
        sensor_platform="Landsat-9",
        acquisition_date="2026-04-18",
        doy=108,
        spatial_resolution_m=30.0,
        cloud_cover_aoi_pct=0.0,
        quality_flags_passed=True,
        asset_uri="s3://climora/obs-1.tif",
    )
    qc_ok = MRVQualityControlResult(
        spatial_coverage_passed=True,
        temporal_window_passed=True,
        cloud_screening_passed=True,
        sensor_consistency_passed=True,
        geolocation_alignment_passed=True,
        all_passed=True,
        violations=[],
    )

    # Incomplete context (no verification event)
    ok, msg = ProjectStateMachine.can_transition(
        ProjectLifecycleState.MONITORING,
        ProjectLifecycleState.VERIFIED,
        context={
            "implementation_events": [impl_event],
            "observation_event": obs_event,
            "qc_result": qc_ok,
            # missing verification_event
        },
    )
    assert not ok
    assert "Verification requires certified third-party verification event" in msg

    # Context with synthetic demo fixture (Anti-Contamination Guard)
    synth_fixture = SyntheticMRVFixtureGenerator.generate_demo_mrv_fixture(
        project_id="PROJ-1", h3_cell_id="c0"
    )
    synth_impl = ImplementationEvent(**synth_fixture["implementation_event"])
    synth_obs = ObservationEvent(**synth_fixture["observation_event"])
    synth_verif = VerificationEvent(
        verification_id=synth_fixture["verification_event"]["verification_id"],
        project_id="PROJ-1",
        verification_status="PASSED",
        verification_date="2026-05-01",
        verifier_identity="Mock Verifier",
        methodology_standard="Demo standard",
        evidence_artifact_uri="mock://demo",
        findings_summary="Synthetic findings",
        is_synthetic_demo=True,  # Synthetic demo flag
    )

    ok, msg = ProjectStateMachine.can_transition(
        ProjectLifecycleState.MONITORING,
        ProjectLifecycleState.VERIFIED,
        context={
            "implementation_events": [synth_impl],
            "observation_event": synth_obs,
            "qc_result": qc_ok,
            "verification_event": synth_verif,
        },
    )
    assert not ok
    assert "REJECTED: Demo fixture (DEMO_ONLY_SYNTHETIC_MRV_DATA)" in msg


def test_ward_independence_decoupling(canonical_proposal_doc):
    """Test 9: Verify that no PMC ward dependency enters project structure."""
    target_geo = canonical_proposal_doc["section_3_target_geography"]
    assert target_geo["spatial_grid_type"] == "Uber H3 Discrete Global Grid System"
    assert target_geo["h3_resolution"] == 9
    assert "NONE" in target_geo["administrative_ward_dependency"]


def test_proposal_document_13_sections_and_truth_layers(canonical_proposal_doc):
    """Test 10: Verify the 13 mandatory sections and strict truth layer labeling."""
    expected_sections = [
        "section_1_project_identity",
        "section_2_problem_statement_baseline",
        "section_3_target_geography",
        "section_4_intervention_portfolio",
        "section_5_physical_scope_and_quantities",
        "section_6_transparent_cost_breakdown",
        "section_7_modeled_microclimatic_and_risk_impact",
        "section_8_physical_implementation_plan",
        "section_9_long_term_monitoring_protocol",
        "section_10_third_party_mrv_and_verification",
        "section_11_scientific_assumptions_and_limitations",
        "section_12_data_lake_lineage_and_provenance",
        "section_13_optimization_run_traceability",
    ]
    for sec in expected_sections:
        assert sec in canonical_proposal_doc, f"Section {sec} missing from proposal"

    # Truth-layer assertions
    sec7 = canonical_proposal_doc["section_7_modeled_microclimatic_and_risk_impact"]
    assert "MODELED" in sec7["truth_layer"]
    assert sec7["modeled_aggregate_risk_reduction_score"] == 0.10604830270054796
    assert "does NOT represent a guaranteed 10.6% clinical or ambient cooling outcome" in sec7["governance_note"]

    # Budget separation
    sec6 = canonical_proposal_doc["section_6_transparent_cost_breakdown"]
    assert sec6["modeled_optimized_capex_inr"] == 9992500.0
    assert sec6["actual_expenditure_inr"] == "NOT_AVAILABLE (Pre-implementation proposal phase)"


def test_truth_layer_metric_separation_and_provenance(canonical_proposal_doc):
    """Test 11: Explicit verification that modeled metrics cannot contaminate verified fields and provenance is unbroken."""
    # 1. Modeled metrics cannot contaminate verified fields
    sec7 = canonical_proposal_doc["section_7_modeled_microclimatic_and_risk_impact"]
    sec10 = canonical_proposal_doc["section_10_third_party_mrv_and_verification"]

    assert "MODELED" in sec7["truth_layer"]
    assert sec10["verification_status"] == "UNOBSERVED / NOT YET VERIFIED"
    assert sec10["measured_empirical_cooling_degC"] is None
    assert sec10["verified_impact_claims"] is None

    # 2. Section 12 Data Lake Lineage and SHA-256 Provenance
    sec12 = canonical_proposal_doc["section_12_data_lake_lineage_and_provenance"]
    expected_lineage_keys = [
        "feature_matrix_artifact",
        "hev_components_artifact",
        "risk_surface_artifact",
        "optimization_allocation_artifact",
    ]
    for k in expected_lineage_keys:
        assert k in sec12, f"Lineage key {k} missing in section 12"
        artifact_path = Path(sec12[k])
        assert artifact_path.exists(), f"Upstream artifact referenced in provenance does not exist: {artifact_path}"


def test_phase_1h_1_hardening_validation():
    """Test 12: Comprehensive Phase 1H.1 forensic hardening checks."""
    # 1. Division by zero in deviation rate explicitly returns None
    evt_zero = ImplementationEvent(
        event_id="EVT-Z",
        project_id="P-Z",
        h3_cell_id="c0",
        intervention_code="street_tree_shade",
        planned_quantity=0.0,
        implemented_quantity=10.0,
        quantity_unit="tree_count",
        contractor_id="C1",
        completion_date="2026-04-01",
        evidence_uri="s3://c/e.pdf",
    )
    assert evt_zero.deviation == 10.0
    assert evt_zero.deviation_rate is None

    # 2. Metric-specific sensor compatibility: Sentinel-2 rejected for thermal, accepted for optical
    s2_obs = ObservationEvent(
        observation_id="OBS-S2-HARDEN",
        sensor_platform="Sentinel-2A-MSI",
        acquisition_date="2026-04-20",
        doy=110,
        spatial_resolution_m=10.0,
        cloud_cover_aoi_pct=1.0,
        quality_flags_passed=True,
        asset_uri="s3://c/s2.tif",
    )
    qc_thermal = MRVQualityControlEngine.audit_observation(
        observation=s2_obs, treated_cell_count=28, observed_cell_count=28, target_metric="lst"
    )
    assert qc_thermal.all_passed is False
    assert any("has no thermal infrared payload" in v for v in qc_thermal.violations)

    qc_optical = MRVQualityControlEngine.audit_observation(
        observation=s2_obs, treated_cell_count=28, observed_cell_count=28, target_metric="ndvi"
    )
    assert qc_optical.all_passed is True

    # 3. Cloud screening semantics: <= 5% AOI ceiling and 100% pixel masking
    cloud_obs_borderline = ObservationEvent(
        observation_id="OBS-CLOUD-5",
        sensor_platform="Landsat-9-TIRS",
        acquisition_date="2026-04-20",
        doy=110,
        spatial_resolution_m=30.0,
        cloud_cover_aoi_pct=5.0,  # Exactly at ceiling
        quality_flags_passed=True,
        asset_uri="s3://c/l9.tif",
    )
    qc_borderline = MRVQualityControlEngine.audit_observation(
        observation=cloud_obs_borderline, treated_cell_count=28, observed_cell_count=28, target_metric="lst"
    )
    assert qc_borderline.all_passed is True

    cloud_obs_excess = ObservationEvent(
        observation_id="OBS-CLOUD-6",
        sensor_platform="Landsat-9-TIRS",
        acquisition_date="2026-04-20",
        doy=110,
        spatial_resolution_m=30.0,
        cloud_cover_aoi_pct=5.1,  # Exceeds ceiling
        quality_flags_passed=True,
        asset_uri="s3://c/l9.tif",
    )
    qc_excess = MRVQualityControlEngine.audit_observation(
        observation=cloud_obs_excess, treated_cell_count=28, observed_cell_count=28, target_metric="lst"
    )
    assert qc_excess.all_passed is False
    assert any("exceeds allowable ceiling" in v for v in qc_excess.violations)

    # 4. Gating verification: QC alone without verification event cannot verify
    ok, msg = ProjectStateMachine.can_transition(
        ProjectLifecycleState.MONITORING,
        ProjectLifecycleState.VERIFIED,
        context={
            "implementation_events": [evt_zero],
            "observation_event": cloud_obs_borderline,
            "qc_result": qc_borderline,
            # No verification_event
        },
    )
    assert not ok
    assert "Verification requires certified third-party verification event" in msg


def test_phase_1h_2_canonical_reconciliation(canonical_proposal_doc, project_contract):
    """Test 13: Phase 1H.2 Canonical Reconciliation Audit across 12 mandatory criteria."""
    # 1. Canonical selected-cell count
    df_alloc = pd.read_parquet(CANONICAL_ALLOCATION_PARQUET)
    selected_cells = df_alloc["h3_cell_id"].unique()
    assert len(selected_cells) == 28

    # 2. Canonical intervention quantity (street trees)
    total_trees = float(df_alloc["quantity"].sum())
    assert total_trees == 2695.0, f"Expected 2695.0 street trees, found {total_trees}"

    # 3. Canonical total modeled cost
    direct_cost = float((df_alloc["quantity"] * df_alloc["unit_cost"]).sum())
    fixed_cost = float(df_alloc["fixed_cost"].sum())
    total_cost = float(df_alloc["total_cost"].sum())
    assert direct_cost == 9432500.0
    assert fixed_cost == 560000.0
    assert total_cost == 9992500.0

    # 4. Canonical remaining budget
    with open(CANONICAL_RUN_MANIFEST, "r", encoding="utf-8") as f:
        run_manifest = json.load(f)
    budget = float(run_manifest["scenario_parameters"]["budget_inr"])
    slack = float(run_manifest["portfolio_summary"]["budget_slack_inr"])
    assert budget == 10000000.0
    assert slack == 7500.0
    assert (budget - total_cost) == slack

    # 5. Canonical objective reconstruction
    objective = float(df_alloc["modeled_risk_reduction"].sum())
    assert np.isclose(objective, 0.10604830270054796)

    # 6. Selected-cell population (from canonical feature matrix join)
    df_feat = pd.read_parquet(CANONICAL_FEATURE_MATRIX).set_index("h3_cell_id")
    pop_sum = float(df_feat.loc[selected_cells, "population_2020"].sum())
    assert int(pop_sum) == 118941, f"Expected 118941 residents in 28 treated cells, found {pop_sum}"

    # 7. Project ID / Optimization run consistency
    expected_project_id = f"PROJ-PUNE-2025-{run_manifest['run_id'].split('-')[-1]}"
    assert expected_project_id == "PROJ-PUNE-2025-BA225D6A"
    assert canonical_proposal_doc["section_1_project_identity"]["project_id"] == expected_project_id
    assert canonical_proposal_doc["section_13_optimization_run_traceability"]["optimization_run_id"] == "OPT-PUNE-2025-SCENARIO-BA225D6A"

    # 8. Preferred DOY window (DOY 95-115)
    obs_preferred = ObservationEvent(
        observation_id="OBS-PREF",
        sensor_platform="Landsat-9-TIRS",
        acquisition_date="2026-04-15",
        doy=105,
        spatial_resolution_m=30.0,
        cloud_cover_aoi_pct=1.0,
        quality_flags_passed=True,
        asset_uri="s3://c/pref.tif",
    )
    qc_pref = MRVQualityControlEngine.audit_observation(
        observation=obs_preferred, treated_cell_count=28, observed_cell_count=28
    )
    assert qc_pref.temporal_tier == "PREFERRED"
    assert qc_pref.temporal_window_passed is True

    # 9. Fallback DOY window (DOY 90-120 with max offset <= 15) vs Rejected (> 15)
    obs_fallback = ObservationEvent(
        observation_id="OBS-FALL",
        sensor_platform="Landsat-9-TIRS",
        acquisition_date="2026-04-01",
        doy=91,  # In fallback window 90-120, offset = 14 <= 15
        spatial_resolution_m=30.0,
        cloud_cover_aoi_pct=1.0,
        quality_flags_passed=True,
        asset_uri="s3://c/fall.tif",
    )
    qc_fall = MRVQualityControlEngine.audit_observation(
        observation=obs_fallback, treated_cell_count=28, observed_cell_count=28
    )
    assert qc_fall.temporal_tier == "FALLBACK"
    assert qc_fall.temporal_window_passed is True

    obs_rejected = ObservationEvent(
        observation_id="OBS-REJ",
        sensor_platform="Landsat-9-TIRS",
        acquisition_date="2026-03-25",
        doy=84,  # Outside fallback window, offset = 21 > 15
        spatial_resolution_m=30.0,
        cloud_cover_aoi_pct=1.0,
        quality_flags_passed=True,
        asset_uri="s3://c/rej.tif",
    )
    qc_rej = MRVQualityControlEngine.audit_observation(
        observation=obs_rejected, treated_cell_count=28, observed_cell_count=28
    )
    assert qc_rej.temporal_tier == "REJECTED"
    assert qc_rej.temporal_window_passed is False

    # 10. Leap-year-safe calendar conversion
    assert doy_to_date(2025, 95) == "2025-04-05"  # Non-leap year
    assert doy_to_date(2024, 95) == "2024-04-04"  # Leap year
    assert doy_to_date(2025, 105) == "2025-04-15"
    assert doy_to_date(2024, 105) == "2024-04-14"

    # 11. Difference-in-Differences remains non-executable
    assert project_contract["mrv_architecture_specification"]["difference_in_differences_status"]["current_operational_status"] == "PLANNED / NOT_EXECUTABLE"

    # 12. Upstream allocation remains immutable
    alloc_sha = calculate_sha256(CANONICAL_ALLOCATION_PARQUET)
    assert alloc_sha == "2519473a32a2b4a3a22bc8beb43525c3f21dc404783168f1edd6de7bc4bb5555"


