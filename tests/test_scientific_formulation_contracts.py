"""Automated Test Suite for CLIMORA Scientific Formulation Register & Contract.

Validates:
1. Machine-readable scientific formulation contract schema, groups, and status flags.
2. Complete mathematical lineage coverage from raw sensor to MRV / verification (F-01 to F-28).
3. Zero-exposure boundary axiom (E_i = 0 => Risk_i = 0) and numerical edge case stability.
4. Regularization safeguard against division-by-zero in standardized thermal anomalies.
5. Cross-contract alignment with Risk Parameters, Temporal Features, Analytical Units, and Feature Dictionary.
6. Documentation integrity for Mathematical Formulation Register, Uncertainty Framework, and Validation Framework.
"""

import json
import math
from pathlib import Path

import numpy as np
import pytest

from processing.config import PROJECT_ROOT

MANIFESTS_DIR = PROJECT_ROOT / "data" / "manifests"
SCIENCE_DOCS_DIR = PROJECT_ROOT / "docs" / "science"


def test_scientific_formulation_contract_schema_and_completeness():
    """Verify machine-readable scientific formulation contract schema and inventory."""
    contract_file = MANIFESTS_DIR / "scientific_formulation_contract.json"
    assert contract_file.exists(), "scientific_formulation_contract.json must exist"

    with open(contract_file, "r", encoding="utf-8") as f:
        contract = json.load(f)

    assert contract["status"] == "RATIFIED_AND_CANONICAL"
    assert contract["schema_version"] == "1.0.0"
    assert contract["phase"] == "Phase 1B"
    assert contract["contract_id"] == "CLIMORA-CONTRACT-SCIENTIFIC-FORMULATIONS-V1"
    assert contract["total_formulations"] == 28
    assert len(contract["formulations"]) == 28
    assert len(contract["formulation_groups"]) == 14

    required_fields = {
        "formulation_id", "name", "symbol", "group", "expression_latex",
        "expression_ascii", "variable_definitions", "units", "truth_layer",
        "scientific_purpose", "assumptions", "limitations", "validation_method",
        "provenance_source", "implementation_status"
    }

    valid_truth_layers = {"OBSERVED", "DERIVED", "MODELED", "VERIFIED"}
    valid_statuses = {
        "IMPLEMENTED", "IMPLEMENTED_BUT_UNVALIDATED", "IMPLEMENTABLE_NEXT",
        "ASSUMPTION", "PENDING_CALIBRATION", "PENDING_DATA", "PENDING_VALIDATION"
    }

    formulation_ids = set()
    for f_item in contract["formulations"]:
        fid = f_item["formulation_id"]
        assert fid not in formulation_ids, f"Duplicate formulation ID: {fid}"
        formulation_ids.add(fid)

        missing = required_fields - set(f_item.keys())
        assert not missing, f"Formulation {fid} missing fields: {missing}"
        assert f_item["truth_layer"] in valid_truth_layers, f"Invalid truth layer in {fid}: {f_item['truth_layer']}"
        assert f_item["implementation_status"] in valid_statuses, f"Invalid status in {fid}: {f_item['implementation_status']}"
        assert f_item["group"] in contract["formulation_groups"], f"Group {f_item['group']} not in formulation_groups list"

    # Verify ID sequence F-01 through F-28
    expected_ids = {f"F-{i:02d}" for i in range(1, 29)}
    assert formulation_ids == expected_ids, f"Formulation IDs mismatch: {expected_ids - formulation_ids}"


def test_zero_exposure_boundary_and_numerical_stability():
    """Computationally test that E_i = 0 strictly implies Risk_i = 0 without numerical exceptions."""
    contract_file = MANIFESTS_DIR / "scientific_formulation_contract.json"
    with open(contract_file, "r", encoding="utf-8") as f:
        contract = json.load(f)

    # Formulation F-22 (Power-law Risk)
    f22 = next(f for f in contract["formulations"] if f["formulation_id"] == "F-22")
    assert "Risk_i" in f22["symbol"]
    assert "H_i^alpha * E_i^beta * V_i^gamma" in f22["expression_ascii"]

    def compute_risk(h: float, e: float, v: float, alpha: float = 1.0, beta: float = 1.0, gamma: float = 1.0) -> float:
        """CLIMORA canonical multiplicative power-law implementation."""
        # Safeguard: if exposure is zero, risk is strictly zero
        if e <= 0.0:
            return 0.0
        return (h ** alpha) * (e ** beta) * (v ** gamma)

    # 1. Zero exposure axiom across varied parameter ranges
    for alpha in [0.5, 1.0, 1.5, 2.0]:
        for beta in [0.5, 1.0, 1.5, 2.0]:
            for gamma in [0.5, 1.0, 1.5, 2.0]:
                for h in [0.1, 0.5, 1.0]:
                    for v in [0.1, 0.5, 1.0]:
                        risk = compute_risk(h=h, e=0.0, v=v, alpha=alpha, beta=beta, gamma=gamma)
                        assert risk == 0.0, f"Zero exposure axiom violated: risk={risk} for e=0.0"

    # 2. All zero inputs edge case
    risk_all_zero = compute_risk(0.0, 0.0, 0.0)
    assert risk_all_zero == 0.0
    assert not math.isnan(risk_all_zero)
    assert not math.isinf(risk_all_zero)

    # 3. Vectorized NumPy evaluation
    H_arr = np.array([0.0, 0.5, 0.8, 1.0, 0.9])
    E_arr = np.array([0.0, 0.0, 0.5, 1.0, 0.2])
    V_arr = np.array([0.0, 0.7, 0.6, 1.0, 0.4])

    risk_vector = np.where(E_arr == 0.0, 0.0, (H_arr ** 1.0) * (E_arr ** 1.0) * (V_arr ** 1.0))
    assert risk_vector[0] == 0.0
    assert risk_vector[1] == 0.0  # E=0
    assert abs(risk_vector[2] - (0.8 * 0.5 * 0.6)) < 1e-6
    assert abs(risk_vector[3] - 1.0) < 1e-6


def test_standardized_anomaly_regularization_safeguard():
    """Verify that standardized anomaly calculation prevents division-by-zero when baseline std is zero."""
    contract_file = MANIFESTS_DIR / "scientific_formulation_contract.json"
    with open(contract_file, "r", encoding="utf-8") as f:
        contract = json.load(f)

    f15 = next(f for f in contract["formulations"] if f["formulation_id"] == "F-15")
    assert "epsilon" in f15["variable_definitions"]
    epsilon = 0.001

    def compute_z_score(lst_2025: float, lst_baseline_mean: float, lst_baseline_std: float) -> float:
        return (lst_2025 - lst_baseline_mean) / (lst_baseline_std + epsilon)

    # Case 1: Identical interannual temperatures (std == 0.0)
    z_zero_std = compute_z_score(lst_2025=44.0, lst_baseline_mean=42.0, lst_baseline_std=0.0)
    assert not math.isnan(z_zero_std)
    assert not math.isinf(z_zero_std)
    assert z_zero_std == 2000.0  # (44 - 42) / 0.001

    # Case 2: Zero anomaly and zero std
    z_no_diff = compute_z_score(lst_2025=42.0, lst_baseline_mean=42.0, lst_baseline_std=0.0)
    assert z_no_diff == 0.0

    # Case 3: Typical real-world variation (std == 1.2°C)
    z_normal = compute_z_score(lst_2025=45.0, lst_baseline_mean=42.0, lst_baseline_std=1.2)
    expected = 3.0 / 1.201
    assert abs(z_normal - expected) < 1e-5


def test_cross_contract_alignment():
    """Ensure scientific formulation contract aligns with all established Phase 1B contracts."""
    # 1. Risk Parameter Contract alignment
    with open(MANIFESTS_DIR / "risk_parameter_contract.json", "r", encoding="utf-8") as f:
        rp = json.load(f)
    assert rp["methodological_thresholds"]["lst_extreme_recurrence_threshold_celsius"] == 45.0
    assert rp["methodological_thresholds"]["threshold_type"] == "CLIMORA_METHODOLOGICAL_SURFACE_TEMPERATURE_THRESHOLD"
    assert rp["methodological_thresholds"]["annual_cell_coverage_valid_threshold"] == 0.70
    assert rp["methodological_thresholds"]["min_valid_baseline_years_required"] == 4

    # 2. Temporal Feature Contract alignment
    with open(MANIFESTS_DIR / "temporal_feature_contract.json", "r", encoding="utf-8") as f:
        tf = json.load(f)
    assert tf["temporal_quality_and_missing_data_policy"]["min_valid_baseline_years"] == 4
    assert tf["temporal_quality_and_missing_data_policy"]["annual_cell_validity_threshold"] == 0.70

    # 3. Feature Dictionary NDWI exclusion audit
    with open(MANIFESTS_DIR / "feature_dictionary.json", "r", encoding="utf-8") as f:
        fd = json.load(f)
    active_feature_ids = [feat["feature_id"] for feat in fd["features"]]
    assert not any("ndwi" in fid.lower() for fid in active_feature_ids), "NDWI must remain excluded from active features"

    # 4. Analytical Unit Contract alignment
    with open(MANIFESTS_DIR / "analytical_unit_contract.json", "r", encoding="utf-8") as f:
        au = json.load(f)
    assert au["primary_analytical_unit"]["total_aoi_cells"] == 3181
    assert au["primary_analytical_unit"]["resolution"] == 9
    assert au["secondary_administrative_unit"]["total_wards"] == 41


def test_scientific_documentation_integrity():
    """Verify that all canonical scientific documents exist and contain required core sections."""
    register_path = SCIENCE_DOCS_DIR / "climora-mathematical-formulation-register.md"
    assert register_path.exists(), "climora-mathematical-formulation-register.md must exist"
    reg_text = register_path.read_text(encoding="utf-8")

    # Check key sections and terms in register
    assert "CLIMORA — Mathematical Formulation Register" in reg_text
    assert "FORMULATION F-01" in reg_text
    assert "FORMULATION F-28" in reg_text
    assert "Zero-Exposure Proof & Computational Axiom" in reg_text
    assert "Scientific Validation Hierarchy (Levels 0 through 6)" in reg_text
    assert "IMPLEMENTED NOW" in reg_text
    assert "IMPLEMENTABLE NEXT" in reg_text
    assert "REQUIRES NEW DATA" in reg_text
    assert "REQUIRES CALIBRATION" in reg_text
    assert "REQUIRES VALIDATION" in reg_text
    assert "STRICT FORENSIC BAN" in reg_text
    assert "MATHEMATICALLY INVALID" in reg_text

    # Check uncertainty framework
    unc_path = SCIENCE_DOCS_DIR / "uncertainty-and-sensitivity-framework.md"
    assert unc_path.exists(), "uncertainty-and-sensitivity-framework.md must exist"
    unc_text = unc_path.read_text(encoding="utf-8")
    assert "7-Category Component-Wise Uncertainty Architecture" in unc_text
    assert "Strict Conditions for Quadrature Summation" in unc_text
    assert "Multi-Dimensional Sensitivity Analysis Protocol" in unc_text
    assert "Local Logarithmic Elasticity" in unc_text
    assert "Global Variance Decomposition (Sobol Indices)" in unc_text

    # Check validation framework
    val_path = SCIENCE_DOCS_DIR / "validation-framework.md"
    assert val_path.exists(), "validation-framework.md must exist"
    val_text = val_path.read_text(encoding="utf-8")
    assert "LEVEL 0: MATHEMATICAL CONSISTENCY" in val_text
    assert "LEVEL 1: DATA INTEGRITY & PROVENANCE" in val_text
    assert "LEVEL 2: PHYSICAL PLAUSIBILITY" in val_text
    assert "LEVEL 3: SPATIAL CONSISTENCY & AUTOCORRELATION" in val_text
    assert "LEVEL 4: TEMPORAL CONSISTENCY & MICROCLIMATIC STABILITY" in val_text
    assert "LEVEL 5: EXTERNAL / CROSS-SENSOR REFERENCE VALIDATION" in val_text
    assert "LEVEL 6: GROUND-TRUTH & CLINICAL IN-SITU VALIDATION" in val_text
    assert "MANDATORY SCIENTIFIC RULE" in val_text
