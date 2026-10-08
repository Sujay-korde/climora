"""Common reusable ingestion utilities for CLIMORA Phase 0.

Provides:
- AOI loading & geometry validation
- SHA-256 calculation
- Idempotent safe download with atomic .part rename
- Raster and vector validation
- Manifest management
- Structured logging
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from shapely.geometry import shape, Polygon, MultiPolygon

logger = logging.getLogger("climora.ingestion")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("[%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def get_logger() -> logging.Logger:
    """Return the CLIMORA ingestion logger."""
    return logger


def load_aoi(aoi_path: Path | str) -> dict:
    """Load AOI GeoJSON file."""
    path = Path(aoi_path)
    if not path.exists():
        raise FileNotFoundError(f"AOI file does not exist at {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_aoi(aoi_data: dict) -> Tuple[bool, str, Any, List[float], List[float]]:
    """Validate AOI GeoJSON.

    Returns:
        (is_valid, crs_name, shapely_geom, bbox, centroid)
    """
    if "type" not in aoi_data:
        return False, "Missing 'type' in GeoJSON", None, [], []

    features = aoi_data.get("features", [])
    if not features and aoi_data.get("type") in ("Polygon", "MultiPolygon"):
        geom = shape(aoi_data)
    elif features:
        # Use first feature or union of features
        first_feat = features[0]
        geom_dict = first_feat.get("geometry")
        if not geom_dict:
            return False, "First feature missing geometry", None, [], []
        geom = shape(geom_dict)
    else:
        return False, "No valid geometry found in GeoJSON", None, [], []

    if not geom.is_valid:
        geom = geom.buffer(0)

    if not geom.is_valid:
        return False, "Geometry is invalid and cannot be fixed with buffer(0)", None, [], []

    crs_name = "EPSG:4326"
    crs_info = aoi_data.get("crs")
    if crs_info and isinstance(crs_info, dict):
        props = crs_info.get("properties", {})
        crs_name = props.get("name", "EPSG:4326")

    bbox = list(geom.bounds)  # [minx, miny, maxx, maxy]
    centroid = [geom.centroid.x, geom.centroid.y]

    return True, crs_name, geom, bbox, centroid


def calculate_sha256(filepath: Path | str, chunk_size: int = 1048576) -> str:
    """Calculate SHA-256 hash of a file using chunked streaming."""
    path = Path(filepath)
    if not path.is_file():
        raise FileNotFoundError(f"Cannot compute hash: {path} is not a file")
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def create_retry_session(
    retries: int = 3,
    backoff_factor: float = 0.5,
    status_forcelist: Tuple[int, ...] = (429, 500, 502, 503, 504),
) -> requests.Session:
    """Create a requests Session with automatic HTTP retry logic."""
    session = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def safe_download_file(
    url: str,
    dest_path: Path | str,
    expected_size: Optional[int] = None,
    session: Optional[requests.Session] = None,
    chunk_size: int = 1048576,
    retries: int = 3,
    timeout: int = 60,
    headers: Optional[Dict[str, str]] = None,
) -> Tuple[Path, str, int, bool]:
    """Download a file with idempotency, .part temporary file, and SHA-256 calculation.

    Returns:
        (dest_path, sha256_checksum, file_size, skipped_already_exists)
    """
    dest = Path(dest_path)
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Idempotency check: if destination file exists and is non-empty
    if dest.exists() and dest.is_file():
        existing_size = dest.stat().st_size
        if existing_size > 0:
            if expected_size is None or existing_size == expected_size:
                logger.info(f"[SKIP/VERIFY] File already exists: {dest.name} ({existing_size} bytes)")
                checksum = calculate_sha256(dest)
                return dest, checksum, existing_size, True

    part_file = dest.with_suffix(dest.suffix + ".part")
    if part_file.exists():
        part_file.unlink()

    sess = session or create_retry_session(retries=retries)
    req_headers = {"User-Agent": "CLIMORA-Research-Project/1.0"}
    if headers:
        req_headers.update(headers)

    hasher = hashlib.sha256()
    total_written = 0

    try:
        with sess.get(url, stream=True, timeout=timeout, headers=req_headers) as response:
            if response.status_code != 200:
                raise RuntimeError(
                    f"HTTP {response.status_code} error downloading from {url}: {response.text[:200]}"
                )

            with open(part_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        hasher.update(chunk)
                        total_written += len(chunk)

        if total_written == 0:
            raise RuntimeError(f"Downloaded empty file (0 bytes) from {url}")

        if expected_size is not None and total_written != expected_size:
            raise RuntimeError(
                f"File size mismatch for {dest.name}: expected {expected_size} bytes, got {total_written} bytes"
            )

        # Atomic rename from .part to destination
        if dest.exists():
            dest.unlink()
        part_file.rename(dest)

        checksum = hasher.hexdigest()
        logger.info(f"[DOWNLOADED] {dest.name} ({total_written} bytes) SHA-256: {checksum[:12]}...")
        return dest, checksum, total_written, False

    except Exception as e:
        if part_file.exists():
            part_file.unlink()
        raise e


def validate_raster(filepath: Path | str) -> Dict[str, Any]:
    """Validate a raster GeoTIFF file.

    Checks:
    - file existence
    - opens cleanly with rasterio
    - raster dimensions > 0
    - CRS present
    - bounding box sensible
    """
    path = Path(filepath)
    if not path.is_file():
        return {"valid": False, "error": f"File does not exist: {path}"}

    size = path.stat().st_size
    if size == 0:
        return {"valid": False, "error": f"File is empty (0 bytes): {path}"}

    try:
        import rasterio
        with rasterio.open(path) as src:
            width = src.width
            height = src.height
            count = src.count
            crs = str(src.crs) if src.crs else None
            bounds = [src.bounds.left, src.bounds.bottom, src.bounds.right, src.bounds.top]
            dtype = str(src.dtypes[0]) if src.dtypes else None

            if width <= 0 or height <= 0 or count <= 0:
                return {"valid": False, "error": f"Invalid dimensions: w={width}, h={height}, count={count}"}

            return {
                "valid": True,
                "format": "GeoTIFF",
                "width": width,
                "height": height,
                "bands": count,
                "crs": crs,
                "bounds": bounds,
                "dtype": dtype,
                "size_bytes": size,
            }
    except Exception as e:
        # Fallback to tifffile
        try:
            import tifffile
            with tifffile.TiffFile(path) as tif:
                series = tif.series[0]
                shape_tuple = series.shape
                return {
                    "valid": True,
                    "format": "TIFF (fallback)",
                    "shape": shape_tuple,
                    "size_bytes": size,
                }
        except Exception as e2:
            return {"valid": False, "error": f"Failed to read raster: {e} | Fallback error: {e2}"}


def validate_vector(filepath: Path | str) -> Dict[str, Any]:
    """Validate a vector GeoJSON file."""
    path = Path(filepath)
    if not path.is_file():
        return {"valid": False, "error": f"File does not exist: {path}"}

    size = path.stat().st_size
    if size == 0:
        return {"valid": False, "error": f"File is empty: {path}"}

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        features = data.get("features", [])
        valid_features = 0
        geom_types = set()

        for feat in features:
            geom_dict = feat.get("geometry")
            if geom_dict:
                geom = shape(geom_dict)
                if geom.is_valid:
                    valid_features += 1
                geom_types.add(geom.geom_type)

        return {
            "valid": True,
            "format": "GeoJSON",
            "feature_count": len(features),
            "valid_feature_count": valid_features,
            "geometry_types": list(geom_types),
            "size_bytes": size,
        }
    except Exception as e:
        return {"valid": False, "error": f"Failed to parse vector GeoJSON: {e}"}


def load_manifest(manifest_path: Path | str) -> dict:
    """Load acquisition manifest JSON."""
    path = Path(manifest_path)
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_manifest(manifest_path: Path | str, manifest_data: dict) -> None:
    """Safely write acquisition manifest JSON atomically."""
    path = Path(manifest_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)
    if path.exists():
        path.unlink()
    tmp_path.rename(path)


# Default Pune Climatological Seasons
DEFAULT_SEASONS = {
    "winter": {
        "name": "Winter / Post-Monsoon Dry",
        "start": "01-01",
        "end": "02-28",
    },
    "pre_monsoon_summer": {
        "name": "Pre-Monsoon / Summer Hot Season",
        "start": "03-01",
        "end": "05-31",
    },
    "monsoon": {
        "name": "Southwest Monsoon",
        "start": "06-01",
        "end": "09-30",
    },
    "post_monsoon": {
        "name": "Post-Monsoon Transition",
        "start": "10-01",
        "end": "12-31",
    },
}


def get_season_for_date(
    date_str: str,
    seasons: Optional[Dict[str, Dict[str, str]]] = None,
) -> Tuple[str, str]:
    """Determine the climatic season key and human-readable name for an ISO date string."""
    seasons_dict = seasons or DEFAULT_SEASONS
    clean_date = date_str[:10]
    month_day = clean_date[5:]  # MM-DD

    for s_key, s_info in seasons_dict.items():
        s_start = s_info.get("start", "01-01")
        s_end = s_info.get("end", "12-31")
        if s_start <= s_end:
            if s_start <= month_day <= s_end:
                return s_key, s_info.get("name", s_key)
        else:
            if month_day >= s_start or month_day <= s_end:
                return s_key, s_info.get("name", s_key)

    return "unassigned", "Unassigned Season"


def select_seasonal_candidates(
    candidates: List[Dict[str, Any]],
    seasons: Optional[Dict[str, Dict[str, str]]] = None,
    target_per_season: int = 1,
    existing_ids: Optional[set] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Deterministically select representative seasonal candidates.

    Deterministic ranking within each season:
    1. Already-downloaded bootstrap candidate (is_existing = True) gets top priority to preserve local lake.
    2. Cloud cover ascending (lowest cloud cover first).
    3. Candidate ID ascending (reproducible tie-breaker).
    """
    seasons_dict = seasons or DEFAULT_SEASONS
    existing = set(existing_ids or [])

    # Group candidates by season
    by_season: Dict[str, List[Dict[str, Any]]] = {k: [] for k in seasons_dict}

    for cand in candidates:
        d_val = cand.get("date", "")
        s_key, _ = get_season_for_date(d_val, seasons_dict)
        if s_key in by_season:
            by_season[s_key].append(cand)

    selected: List[Dict[str, Any]] = []
    seasonal_summary: Dict[str, Any] = {}

    for s_key, s_info in seasons_dict.items():
        s_name = s_info.get("name", s_key)
        cands_in_season = by_season.get(s_key, [])

        if not cands_in_season:
            seasonal_summary[s_key] = {
                "season_name": s_name,
                "candidates_count": 0,
                "selected_count": 0,
                "selected_ids": [],
                "note": "No candidate scenes passed quality/cloud filters for this season",
            }
            continue

        sorted_cands = sorted(
            cands_in_season,
            key=lambda c: (
                0 if c.get("id") in existing else 1,
                float(c.get("cloud_cover", 100.0)),
                str(c.get("id", "")),
            ),
        )

        chosen = sorted_cands[:target_per_season]
        chosen_ids = []

        for rank, ch in enumerate(chosen, 1):
            is_ext = ch.get("id") in existing
            ch_copy = dict(ch)
            ch_copy["selection_metadata"] = {
                "season_key": s_key,
                "season_name": s_name,
                "selection_strategy": "seasonal_representative",
                "selection_rank": rank,
                "is_existing_bootstrap": is_ext,
                "selection_reason": (
                    f"Selected for '{s_name}' (rank {rank}, cloud {ch.get('cloud_cover')}%, "
                    f"{'existing bootstrap scene' if is_ext else 'new seasonal candidate'})"
                ),
                "selection_parameters": {
                    "target_per_season": target_per_season,
                    "cloud_cover": ch.get("cloud_cover"),
                },
            }
            selected.append(ch_copy)
            chosen_ids.append(ch.get("id"))

        seasonal_summary[s_key] = {
            "season_name": s_name,
            "candidates_count": len(cands_in_season),
            "selected_count": len(chosen),
            "selected_ids": chosen_ids,
        }

    return selected, seasonal_summary


def build_provenance_record(
    dataset_id: str,
    provider: str,
    product: str,
    version: str,
    source: str,
    source_item_id: str,
    license_name: str,
    access_method: str,
    spatial_resolution: str,
    temporal_resolution: str,
    acquisition_date: str,
    observation_period: Dict[str, str],
    aoi: Dict[str, Any],
    cloud_cover: Optional[float],
    selection_strategy: str,
    selection_parameters: Dict[str, Any],
    required_assets: List[str],
    local_path: str,
    file_size_bytes: int,
    sha256: str,
    validation_status: str,
    s3_uri: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Construct an auditable, S3-compatible dataset/asset provenance record satisfying Section 22."""
    record = {
        "dataset_id": dataset_id,
        "provider": provider,
        "product": product,
        "version": version,
        "source": source,
        "source_item_id": source_item_id,
        "license": license_name,
        "access_method": access_method,
        "spatial_resolution": spatial_resolution,
        "temporal_resolution": temporal_resolution,
        "acquisition_date": acquisition_date,
        "observation_period": observation_period,
        "AOI": aoi,
        "cloud_cover": cloud_cover,
        "selection_strategy": selection_strategy,
        "selection_parameters": selection_parameters,
        "required_assets": required_assets,
        "local_path": local_path.replace("\\", "/"),
        "s3_uri": s3_uri,
        "storage_status": "local",
        "file_size_bytes": file_size_bytes,
        "sha256": sha256,
        "validation_status": validation_status,
    }
    if extra:
        record["details"] = extra
    return record

