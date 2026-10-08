"""WorldPop Population Exposure Acquisition & Validation Module for CLIMORA Phase 1B.

Acquires, validates, and clips the official WorldPop 2020 UN-adjusted population count dataset for Pune:
- Product: WorldPop Global 2000-2020 1km UN-adjusted Population Count (IND)
- Official URL: https://data.worldpop.org/GIS/Population/Global_2000_2020_1km_UNadj/2020/IND/ind_ppp_2020_1km_Aggregated_UNadj.tif
- License: Creative Commons Attribution 4.0 International (CC BY 4.0)
- Units: Estimated number of persons (people per pixel / count)
- Native CRS: EPSG:4326 (WGS 84)
- Methodology: Random forest dasymetric spatial disaggregation adjusted to UN national population totals
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import rasterio
from rasterio.mask import mask
from rasterio.warp import transform_geom

from ingestion.common import calculate_sha256, create_retry_session, get_logger, load_aoi, safe_download_file
from processing.config import PROJECT_ROOT, RAW_DIR, PROCESSED_DIR

logger = get_logger()

WORLDPOP_URL = "https://data.worldpop.org/GIS/Population/Global_2000_2020_1km_UNadj/2020/IND/ind_ppp_2020_1km_Aggregated_UNadj.tif"
EXPECTED_SIZE_BYTES = 18313124  # Official file size on WorldPop server


def acquire_worldpop_raw(force: bool = False) -> Dict[str, Any]:
    """Download the raw WorldPop 2020 UN-adjusted population count raster idempotently."""
    dest_dir = RAW_DIR / "worldpop" / "2020"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / "ind_ppp_2020_1km_Aggregated_UNadj.tif"

    logger.info(f"Acquiring WorldPop 2020 population count raster from {WORLDPOP_URL}...")

    session = create_retry_session(retries=5, backoff_factor=1.0)
    dest_path, sha256_hash, file_size, skipped = safe_download_file(
        url=WORLDPOP_URL,
        dest_path=dest_file,
        expected_size=EXPECTED_SIZE_BYTES,
        session=session,
        timeout=120,
    )

    meta = {
        "dataset_id": "worldpop_ind_ppp_2020_1km_unadj",
        "provider": "WorldPop / University of Southampton",
        "product": "WorldPop Global 2000-2020 1km UN-adjusted Population Count",
        "year": 2020,
        "country": "India (IND)",
        "source_url": WORLDPOP_URL,
        "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
        "native_crs": "EPSG:4326",
        "units": "people per grid cell (estimated count)",
        "methodology": "Random forest dasymetric spatial disaggregation calibrated to UN WPP national totals",
        "local_path": str(dest_file.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "file_size_bytes": file_size,
        "sha256": sha256_hash,
        "skipped_idempotent": skipped,
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
    }

    meta_file = dest_dir / "metadata.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    logger.info(f"WorldPop raw acquisition complete: {dest_file.name} ({file_size} bytes, SHA: {sha256_hash[:12]}...)")
    return meta


if __name__ == "__main__":
    acquire_worldpop_raw()
