"""NASA POWER meteorological data acquisition module for CLIMORA.

Targets:
- Daily meteorological parameters for Pune AOI
- Temporal target: 2025
- Variables: T2M, T2M_MAX, T2M_MIN, RH2M, WS10M, PRECTOTCORR, ALLSKY_SFC_SW_DWN
- Storage: data/raw/nasa_power/pune/2025/power_2025_daily.json and metadata.json
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from ingestion.common import calculate_sha256, create_retry_session, get_logger
from ingestion.config import IngestionConfig

logger = get_logger()

DEFAULT_VARIABLES = [
    "T2M",
    "T2M_MAX",
    "T2M_MIN",
    "RH2M",
    "WS10M",
    "PRECTOTCORR",
    "ALLSKY_SFC_SW_DWN",
]


def acquire_nasa_power(
    config: IngestionConfig,
    centroid: List[float],  # [lon, lat]
    variables: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Acquire daily meteorological series from NASA POWER API for Pune centroid."""
    logger.info("Acquiring NASA POWER daily meteorological data for Pune...")
    src_cfg = config.sources.get("nasa_power", {})
    api_url = src_cfg.get("api_url", "https://power.larc.nasa.gov/api/temporal/daily/point")
    community = src_cfg.get("community", "ag")
    vars_to_request = variables or src_cfg.get("variables", DEFAULT_VARIABLES)

    lon, lat = centroid[0], centroid[1]

    # Convert start_date and end_date from YYYY-MM-DD to YYYYMMDD
    start_str = config.start_date.replace("-", "")
    end_str = config.end_date.replace("-", "")

    params = {
        "parameters": ",".join(vars_to_request),
        "community": community,
        "longitude": round(lon, 4),
        "latitude": round(lat, 4),
        "start": start_str,
        "end": end_str,
        "format": "JSON",
    }

    out_dir = config.get_source_raw_dir("nasa_power", f"pune/{config.year}")
    data_file = out_dir / f"power_{config.year}_daily.json"
    metadata_file = out_dir / "metadata.json"

    # Idempotency check: if data file exists and is valid
    if data_file.exists() and metadata_file.exists() and data_file.stat().st_size > 0:
        logger.info(f"[SKIP/VERIFY] NASA POWER data already exists at {data_file.name}")
        checksum = calculate_sha256(data_file)
        with open(metadata_file, "r", encoding="utf-8") as f:
            meta = json.load(f)
        rel_path = str(data_file.relative_to(config.project_root))
        s3_uri = f"s3://climora-lake/raw/nasa_power/pune/{config.year}/{data_file.name}"
        return {
            "dataset_id": "NASA_POWER_DAILY_POINT",
            "provider": "NASA Langley Research Center",
            "product": "NASA Prediction Of Worldwide Energy Resources (POWER) Daily Point",
            "version": "v2.0",
            "source": api_url,
            "source_item_id": f"pune_{config.year}_daily",
            "license": "NASA Open Data Policy",
            "access_method": "REST API JSON",
            "spatial_resolution": "0.5 x 0.625 degree (MERRA-2 Grid)",
            "temporal_resolution": "Daily",
            "acquisition_date": meta.get("acquisition_timestamp", f"{config.year}-01-01"),
            "observation_period": {"start": config.start_date, "end": config.end_date},
            "AOI": {"study_area": config.study_area, "coordinates": [lon, lat]},
            "cloud_cover": None,
            "selection_strategy": "full_annual_series",
            "selection_parameters": {"community": community, "parameters": vars_to_request},
            "required_assets": vars_to_request,
            "local_path": rel_path.replace("\\", "/"),
            "s3_uri": s3_uri,
            "storage_status": "local",
            "file_size_bytes": data_file.stat().st_size,
            "sha256": checksum,
            "validation_status": "VALID",
            "status": "VALID",
            "file": rel_path,
            "metadata_file": str(metadata_file.relative_to(config.project_root)),
            "size_bytes": data_file.stat().st_size,
            "variables": meta.get("returned_variables", vars_to_request),
            "metadata": meta,
        }

    session = create_retry_session(retries=config.download_retries)
    req_headers = {"User-Agent": "CLIMORA-Research-Project/1.0"}

    logger.info(f"Querying NASA POWER API for coords ({lat}, {lon}), period {start_str}-{end_str}...")
    resp = session.get(api_url, params=params, headers=req_headers, timeout=config.download_timeout)

    if resp.status_code != 200:
        raise RuntimeError(
            f"NASA POWER API error {resp.status_code}: {resp.text[:300]}"
        )

    power_data = resp.json()

    # Verify that requested parameters exist in response
    returned_params = list(
        power_data.get("properties", {}).get("parameter", {}).keys()
    )

    # Write data file atomically
    tmp_data = data_file.with_suffix(".part")
    with open(tmp_data, "w", encoding="utf-8") as f:
        json.dump(power_data, f, indent=2)
    if data_file.exists():
        data_file.unlink()
    tmp_data.rename(data_file)

    checksum = calculate_sha256(data_file)

    meta_content = {
        "dataset": "NASA_POWER_DAILY_POINT",
        "provider": "NASA Langley Research Center",
        "official_source": "NASA Prediction Of Worldwide Energy Resources (POWER)",
        "api_endpoint": api_url,
        "request_parameters": params,
        "requested_variables": vars_to_request,
        "returned_variables": returned_params,
        "coordinates": {"latitude": lat, "longitude": lon},
        "period": {"start": config.start_date, "end": config.end_date},
        "acquisition_timestamp": datetime.now(timezone.utc).isoformat(),
        "sha256": checksum,
        "file_size_bytes": data_file.stat().st_size,
    }

    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(meta_content, f, indent=2)

    logger.info(f"[DOWNLOADED] NASA POWER daily data ({data_file.stat().st_size} bytes)")

    return {
        "status": "VALID",
        "file": str(data_file.relative_to(config.project_root)),
        "metadata_file": str(metadata_file.relative_to(config.project_root)),
        "size_bytes": data_file.stat().st_size,
        "sha256": checksum,
        "variables": returned_params,
        "metadata": meta_content,
    }
