"""NASA POWER Meteorological Normalization Engine for CLIMORA Phase 1A.8.

Normalizes the 2021-2025 daily meteorological records into a consistent schema:
- date (YYYY-MM-DD)
- year (YYYY)
- day_of_year (1..366)
- variable (T2M, T2M_MAX, T2M_MIN, RH2M, WS10M, PRECTOTCORR, ALLSKY_SFC_SW_DWN)
- value (float)
- unit (°C, %, m/s, mm/day, MJ/m^2/day)
- source (NASA POWER / MERRA-2 Global Grid)

Maintains explicit point/grid-cell forcing identity without spatial fabrication.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from ingestion.common import calculate_sha256, get_logger
from processing.config import (
    NASA_POWER_VARIABLES,
    PROCESSED_DIR,
    PROCESSING_PHASE,
    PROCESSING_VERSION,
    PROJECT_ROOT,
    RAW_DIR,
)

logger = get_logger()

YEARS_BASELINE = [2021, 2022, 2023, 2024, 2025]


def normalize_nasa_power_records() -> Dict[str, Any]:
    """Process and normalize all 2021-2025 daily NASA POWER meteorological series."""
    logger.info("Normalizing NASA POWER 2021-2025 daily records...")
    out_base_dir = PROCESSED_DIR / "nasa_power" / "pune"
    out_base_dir.mkdir(parents=True, exist_ok=True)

    all_normalized_rows: List[Dict[str, Any]] = []
    annual_summaries: Dict[int, Dict[str, Any]] = {}
    source_files_lineage: List[Dict[str, Any]] = []

    for year in YEARS_BASELINE:
        raw_year_file = RAW_DIR / "nasa_power" / "pune" / str(year) / f"power_{year}_daily.json"
        if not raw_year_file.exists():
            raise FileNotFoundError(f"Missing raw NASA POWER file: {raw_year_file}")

        raw_sha = calculate_sha256(raw_year_file)
        source_files_lineage.append({
            "year": year,
            "raw_file": str(raw_year_file.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "raw_sha256": raw_sha,
            "raw_size_bytes": raw_year_file.stat().st_size,
        })

        with open(raw_year_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        params_data = raw_data.get("properties", {}).get("parameter", {})
        geometry = raw_data.get("geometry", {}).get("coordinates", [73.8735, 18.5279])

        year_rows: List[Dict[str, Any]] = []
        year_out_dir = out_base_dir / str(year)
        year_out_dir.mkdir(parents=True, exist_ok=True)

        # For every date key in the year (format YYYYMMDD)
        sample_param = params_data.get("T2M", {})
        date_keys = sorted(sample_param.keys())

        for date_key in date_keys:
            dt = datetime.strptime(date_key, "%Y%m%d")
            iso_date = dt.strftime("%Y-%m-%d")
            doy = dt.timetuple().tm_yday

            for var_name, var_info in NASA_POWER_VARIABLES.items():
                val = params_data.get(var_name, {}).get(date_key)
                if val is not None and val != -999.0:
                    val_float = round(float(val), 3)
                else:
                    val_float = None

                row = {
                    "date": iso_date,
                    "year": year,
                    "day_of_year": doy,
                    "variable": var_name,
                    "value": val_float,
                    "unit": var_info["unit"],
                    "source": "NASA POWER / MERRA-2 Global Grid (0.5° x 0.625°)",
                    "coordinates": geometry,
                }
                year_rows.append(row)
                all_normalized_rows.append(row)

        # Write annual normalized JSON
        year_json_file = year_out_dir / f"power_{year}_daily_normalized.json"
        with open(year_json_file, "w", encoding="utf-8") as f:
            json.dump(year_rows, f, indent=2)

        # Compute seasonal target window metrics (DOY 95-115)
        window_rows = [r for r in year_rows if 95 <= r["day_of_year"] <= 115]
        window_stats: Dict[str, Any] = {}
        for var_name in NASA_POWER_VARIABLES:
            var_vals = [r["value"] for r in window_rows if r["variable"] == var_name and r["value"] is not None]
            if var_vals:
                window_stats[var_name] = {
                    "mean": round(float(sum(var_vals) / len(var_vals)), 2),
                    "min": min(var_vals),
                    "max": max(var_vals),
                    "count": len(var_vals),
                }

        annual_summaries[year] = {
            "year": year,
            "total_daily_records": len(date_keys),
            "total_parameter_observations": len(year_rows),
            "target_window_doy_95_115_stats": window_stats,
            "normalized_file": str(year_json_file.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "sha256": calculate_sha256(year_json_file),
            "file_size_bytes": year_json_file.stat().st_size,
        }

    # Write combined 5-year normalized JSON
    combined_json_file = out_base_dir / "nasa_power_2021_2025_daily_normalized.json"
    with open(combined_json_file, "w", encoding="utf-8") as f:
        json.dump(all_normalized_rows, f, indent=2)
    combined_json_sha = calculate_sha256(combined_json_file)

    # Write combined 5-year normalized CSV
    combined_csv_file = out_base_dir / "nasa_power_2021_2025_daily_normalized.csv"
    with open(combined_csv_file, "w", encoding="utf-8", newline="") as f:
        fieldnames = ["date", "year", "day_of_year", "variable", "value", "unit", "source", "coordinates"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in all_normalized_rows:
            r_copy = r.copy()
            r_copy["coordinates"] = json.dumps(r_copy["coordinates"])
            writer.writerow(r_copy)
    combined_csv_sha = calculate_sha256(combined_csv_file)

    meta = {
        "dataset_category": "nasa_power_normalized",
        "description": "Normalized 5-year daily meteorological forcing series for Pune centroid",
        "years": YEARS_BASELINE,
        "coordinates": [73.8735, 18.5279],
        "spatial_representation": "point/grid-cell forcing (NOT 30m raster)",
        "processing_version": PROCESSING_VERSION,
        "phase": PROCESSING_PHASE,
        "normalized_at": datetime.now(timezone.utc).isoformat(),
        "total_days": len(all_normalized_rows) // len(NASA_POWER_VARIABLES),
        "total_observations": len(all_normalized_rows),
        "variables": list(NASA_POWER_VARIABLES.keys()),
        "source_files": source_files_lineage,
        "annual_summaries": annual_summaries,
        "artifacts": {
            "combined_json": {
                "path": str(combined_json_file.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "sha256": combined_json_sha,
                "size_bytes": combined_json_file.stat().st_size,
            },
            "combined_csv": {
                "path": str(combined_csv_file.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "sha256": combined_csv_sha,
                "size_bytes": combined_csv_file.stat().st_size,
            },
        },
    }
    with open(out_base_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    logger.info(
        f"NASA POWER normalization complete: {len(all_normalized_rows)} observations across 5 years."
    )
    return meta
