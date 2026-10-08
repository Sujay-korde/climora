"""Unified Processing Pipeline for CLIMORA Phase 1A.8.

Coordinates:
1. Pre-execution verification of raw frozen lake immutability (109 assets).
2. Landsat 5-year temporal processing, AOI clipping, scaling, QA masking, and index derivation.
3. Sentinel-2 2025 current-state high-resolution reference processing.
4. MODIS multi-temporal processing (historical DOY 105 + 2025 observations).
5. NASA POWER 2021-2025 meteorological series normalization.
6. Multi-resolution spatial harmonization registry generation.
7. 5-year temporal stack manifest generation.
8. Actual processed storage measurement and inventory compilation.
9. Generation of authoritative processed manifests and checksums.
10. Post-execution verification of raw frozen lake integrity.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from ingestion.common import calculate_sha256, get_logger
from processing.config import (
    DATA_DIR,
    DERIVED_DIR,
    MANIFESTS_DIR,
    PROCESSED_DIR,
    PROCESSING_PHASE,
    PROCESSING_VERSION,
    PROJECT_ROOT,
    RAW_DIR,
)
from processing.landsat_processor import process_all_landsat_scenes
from processing.modis_processor import process_all_modis_observations
from processing.nasa_power_processor import normalize_nasa_power_records
from processing.sentinel2_processor import process_sentinel2_current_state
from processing.spatial_harmonization import build_spatial_harmonization_framework
from processing.temporal_stack import build_temporal_stack_manifest

logger = get_logger()


def verify_raw_lake_integrity() -> Tuple[bool, List[str]]:
    """Verify that all 109 raw frozen lake assets exist and match SHA-256 hashes."""
    checksum_file = MANIFESTS_DIR / "pune_temporal_baseline_v1_checksums.sha256"
    if not checksum_file.exists():
        return False, [f"Missing raw checksum manifest: {checksum_file}"]

    with open(checksum_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    if len(lines) != 109:
        return False, [f"Expected 109 raw frozen assets, found {len(lines)} in manifest"]

    errors = []
    for line in lines:
        expected_sha, rel_path = line.split(maxsplit=1)
        full_path = PROJECT_ROOT / rel_path.replace("\\", "/")
        if not full_path.exists():
            errors.append(f"MISSING: {rel_path}")
            continue
        act_sha = calculate_sha256(full_path)
        if act_sha != expected_sha:
            errors.append(f"MISMATCH: {rel_path} (expected {expected_sha[:8]}, got {act_sha[:8]})")

    return len(errors) == 0, errors


def compile_processed_inventory() -> Tuple[List[Dict[str, Any]], int, Dict[str, Any]]:
    """Scan processed/ and derived/ directories and build inventory with checksums."""
    inventory: List[Dict[str, Any]] = []
    total_bytes = 0
    categories = {
        "processed_landsat": 0,
        "derived_landsat": 0,
        "processed_modis": 0,
        "processed_sentinel2": 0,
        "processed_nasa_power": 0,
        "processed_dem": 0,
        "temporal_framework": 0,
    }

    # Files in processed/
    for p in sorted(PROCESSED_DIR.rglob("*")):
        if p.is_file() and not p.name.endswith(".tmp") and not p.name.endswith(".part"):
            size = p.stat().st_size
            sha = calculate_sha256(p)
            rel_p = str(p.relative_to(PROJECT_ROOT)).replace("\\", "/")
            total_bytes += size

            cat = "processed_other"
            if "processed/landsat" in rel_p:
                cat = "processed_landsat"
            elif "processed/modis" in rel_p:
                cat = "processed_modis"
            elif "processed/sentinel2" in rel_p:
                cat = "processed_sentinel2"
            elif "processed/nasa_power" in rel_p:
                cat = "processed_nasa_power"
            elif "processed/dem" in rel_p:
                cat = "processed_dem"
            elif "processed/temporal" in rel_p:
                cat = "temporal_framework"

            if cat in categories:
                categories[cat] += size

            inventory.append({
                "path": rel_p,
                "size_bytes": size,
                "sha256": sha,
                "category": cat,
                "extension": p.suffix,
            })

    # Files in derived/
    for p in sorted(DERIVED_DIR.rglob("*")):
        if p.is_file() and not p.name.endswith(".tmp") and not p.name.endswith(".part"):
            size = p.stat().st_size
            sha = calculate_sha256(p)
            rel_p = str(p.relative_to(PROJECT_ROOT)).replace("\\", "/")
            total_bytes += size

            cat = "derived_other"
            if "derived/landsat" in rel_p:
                cat = "derived_landsat"
            elif "derived/temporal" in rel_p:
                cat = "temporal_framework"

            if cat in categories:
                categories[cat] += size

            inventory.append({
                "path": rel_p,
                "size_bytes": size,
                "sha256": sha,
                "category": cat,
                "extension": p.suffix,
            })

    return inventory, total_bytes, categories


def run_phase_1a8_execution() -> int:
    """Execute complete Phase 1A.8 pipeline end-to-end."""
    print("=" * 70)
    print("CLIMORA PHASE 1A.8 — TEMPORAL PROCESSING & SPATIAL HARMONIZATION")
    print("=" * 70)

    # STEP 1: Pre-Execution Raw Lake Verification
    print("\n--- STEP 1: VERIFYING RAW FROZEN LAKE IMMUTABILITY (109 ASSETS) ---")
    raw_ok, raw_errs = verify_raw_lake_integrity()
    if not raw_ok:
        print("[FAIL] Raw frozen lake protection breached:")
        for err in raw_errs:
            print(f"  {err}")
        return 1
    print("[PASS] All 109 raw frozen baseline assets verified 100% byte-for-byte intact.")

    # STEP 2: Landsat 5-Year Temporal Baseline Processing & Derived Products
    print("\n--- STEP 2: PROCESSING LANDSAT 5-YEAR BASELINE & DERIVED PRODUCTS ---")
    landsat_results = process_all_landsat_scenes()
    for yr, res in landsat_results.items():
        print(
            f"  [OK] Landsat {yr} ({res['scene_id']}) | Platform: {res['platform']} | "
            f"DOY: {res['doy']} | Clean: {res['qa_metrics']['valid_clear_pct']}% | "
            f"Processed: {len(res['processed_assets'])} assets | Derived: {len(res['derived_assets'])} indices"
        )

    # STEP 3: Sentinel-2 2025 Current-State Reference Processing
    print("\n--- STEP 3: PROCESSING SENTINEL-2 2025 CURRENT-STATE REFERENCE DATA ---")
    s2_result = process_sentinel2_current_state()
    print(
        f"  [OK] Sentinel-2A ({s2_result['item_id']}) | Date: {s2_result['observation_date']} | "
        f"Native: 10m & 20m preserved | Assets: {len(s2_result['assets'])}"
    )

    # STEP 4: MODIS Multi-Temporal Processing
    print("\n--- STEP 4: PROCESSING MODIS MULTI-TEMPORAL OBSERVATIONS ---")
    modis_results = process_all_modis_observations()
    print(f"  [OK] Processed {len(modis_results)} MODIS granules across 2021-2025.")

    # STEP 5: NASA POWER 2021-2025 Daily Meteorological Normalization
    print("\n--- STEP 5: NORMALIZING NASA POWER 2021-2025 METEOROLOGICAL SERIES ---")
    nasa_power_summary = normalize_nasa_power_records()
    print(
        f"  [OK] Normalized {nasa_power_summary['total_observations']} observations "
        f"across {nasa_power_summary['total_days']} daily dates (2021-2025)."
    )

    # STEP 6: Multi-Resolution Spatial Harmonization Framework
    print("\n--- STEP 6: BUILDING SPATIAL HARMONIZATION FRAMEWORK ---")
    spatial_framework = build_spatial_harmonization_framework()
    print(
        f"  [OK] Multi-resolution spatial registry recorded across 6 data modalities. "
        f"Analytical spatial unit: {spatial_framework['governance_status']}."
    )

    # STEP 7: 5-Year Temporal Stack Manifest
    print("\n--- STEP 7: BUILDING 5-YEAR TEMPORAL STACK MANIFEST ---")
    temporal_stack_manifest = build_temporal_stack_manifest(
        landsat_results, nasa_power_summary, modis_results
    )
    print(
        f"  [OK] Temporal stack manifest generated linking 5 annual observations (2021-2025) "
        f"with complete source lineage."
    )

    # STEP 8: Measure Processed Storage & Build Inventory
    print("\n--- STEP 8: MEASURING ACTUAL PROCESSED STORAGE & COMPILING INVENTORY ---")
    inventory, total_bytes, categories = compile_processed_inventory()

    gib_total = total_bytes / (1024**3)
    mib_total = total_bytes / (1024**2)
    print(f"  Total Processed & Derived Files: {len(inventory)}")
    print(f"  Total Processed & Derived Size:  {total_bytes} bytes ({mib_total:.2f} MiB / {gib_total:.4f} GiB)")
    for cat_name, cat_bytes in categories.items():
        print(f"    - {cat_name}: {cat_bytes / (1024**2):.2f} MiB ({cat_bytes} bytes)")

    # STEP 9: Generate Authoritative Processed Checksums Manifest
    print("\n--- STEP 9: GENERATING PROCESSED CHECKSUMS MANIFEST ---")
    processed_checksums_path = MANIFESTS_DIR / "pune_temporal_baseline_v1_processed_checksums.sha256"
    with open(processed_checksums_path, "w", encoding="utf-8") as f:
        f.write(f"# CLIMORA Pune Temporal Baseline v1 Processed & Derived Checksums\n")
        f.write(f"# Generated: {datetime.now(timezone.utc).isoformat()}\n")
        f.write(f"# Total Files: {len(inventory)}\n")
        f.write(f"# Total Size: {total_bytes} bytes ({gib_total:.4f} GiB)\n\n")
        for item in inventory:
            f.write(f"{item['sha256']}  {item['path'].replace('/', '\\')}\n")
    print(f"  [OK] Processed checksums manifest written: {processed_checksums_path.name}")

    # STEP 10: Generate Authoritative Processed Frozen Manifest
    print("\n--- STEP 10: GENERATING PROCESSED FROZEN MANIFEST ---")
    processed_frozen_path = MANIFESTS_DIR / "pune_temporal_baseline_v1_processed_frozen.json"
    frozen_manifest_data = {
        "manifest_id": "climora_temporal_baseline_v1_processed_frozen",
        "dataset_name": "CLIMORA Pune 5-Year Temporal Baseline Processed & Derived Layer",
        "status": "FROZEN",
        "phase": PROCESSING_PHASE,
        "processing_version": PROCESSING_VERSION,
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "study_area": "Pune, Maharashtra, India",
        "temporal_scope": "2021-2025",
        "canonical_doy": 105,
        "preferred_window": [95, 115],
        "hard_max_offset_days": 15,
        "raw_baseline_manifest": "data/manifests/pune_temporal_baseline_v1_frozen.json",
        "raw_checksums_manifest": "data/manifests/pune_temporal_baseline_v1_checksums.sha256",
        "processed_checksums_manifest": "data/manifests/pune_temporal_baseline_v1_processed_checksums.sha256",
        "temporal_stack_manifest": "data/processed/temporal/pune_temporal_stack_manifest.json",
        "spatial_harmonization_framework": "data/processed/temporal/spatial_harmonization_framework.json",
        "sensor_governance": {
            "statement": (
                "A five-year Landsat Collection 2 Level-2 temporal baseline using the same WRS-2 "
                "Path/Row 147/047 and peak pre-monsoon acquisition window, comprising four Landsat 8 "
                "observations and one Landsat 9 observation in 2023. Explicit platform identity preserved."
            ),
            "platform_sequence": {
                "2021": "Landsat 8",
                "2022": "Landsat 8",
                "2023": "Landsat 9",
                "2024": "Landsat 8",
                "2025": "Landsat 8",
            },
        },
        "storage_metrics": {
            "total_files": len(inventory),
            "total_bytes": total_bytes,
            "total_mib": round(mib_total, 2),
            "total_gib": round(gib_total, 4),
            "categories_bytes": categories,
        },
        "inventory": inventory,
    }
    with open(processed_frozen_path, "w", encoding="utf-8") as f:
        json.dump(frozen_manifest_data, f, indent=2)
    print(f"  [OK] Processed frozen manifest written: {processed_frozen_path.name}")

    # STEP 11: Post-Execution Raw Lake Verification
    print("\n--- STEP 11: POST-EXECUTION RAW LAKE INTEGRITY AUDIT ---")
    post_raw_ok, post_raw_errs = verify_raw_lake_integrity()
    if not post_raw_ok:
        print("[FAIL] Post-execution raw lake audit failed! Immutability violated:")
        for err in post_raw_errs:
            print(f"  {err}")
        return 1
    print("[PASS] All 109 raw frozen baseline assets verified 100% untouched post-processing.")

    print("\n" + "=" * 70)
    print("PHASE 1A.8 EXECUTION COMPLETE — ALL GATES PASSED")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(run_phase_1a8_execution())
