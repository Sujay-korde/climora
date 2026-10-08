"""CLIMORA Runtime Data Loader & S3 Integration Layer.

Supports dual-mode execution:
- LOCAL: Reads verified local canonical data (development & unit test baseline).
- S3 / AWS: Retrieves canonical artifacts from S3 scientific data lake via IAM Task Role,
  performs cryptographic SHA-256 validation on retrieval, and provides validated local runtime cache.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd

from processing.config import PROCESSED_DIR, PROJECT_ROOT

logger = logging.getLogger("climora.runtime_data")

# Canonical S3 working set definitions and expected SHA-256 digests
CANONICAL_EXPECTED_HASHES: Dict[str, str] = {
    "canonical_feature_matrix.parquet": "76f344b147b349f3887259f64c97923414c74fd9a97ec679844fb8d9109f7c01",
    "canonical_hev_components.parquet": "1970c2da7863f5771b223c2f265344129ea3f7ed1e5119ece98dc56e37fa2be9",
    "canonical_risk_surface.parquet": "e2d5df6c7a0a9584367a623b0722e87f3f4340ea5ebf297cb5aaed6533da5677",
    "canonical_spatial_autocorrelation.parquet": "47cc7025ef150aec3980928912e35c96c46da437efbbeccfe1fc142321315bbd",
    "canonical_optimization_allocation.parquet": "2519473a32a2b4a3a22bc8beb43525c3f21dc404783168f1edd6de7bc4bb5555",
    "project_pune_2025_tree_shade_10m.json": "bc60d8588e40946ad65ad293a0e330575f7f615cf6e7b4925378ac794c8c72dc",
    "pune.geojson": "94b72740b8eacf7f58d932ebe971964dddd72baa05569477027e0930ac52e84c",
}

DEFAULT_S3_BUCKET = "climora-scientific-lake-434658845459-pune25"
DEFAULT_S3_REGION = "ap-south-1"


def calculate_sha256(filepath: Path | str) -> str:
    """Calculates SHA-256 digest of a local file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


@dataclass(frozen=True)
class RuntimeDataPaths:
    """Container for resolved runtime data paths."""

    data_mode: str
    s3_bucket: Optional[str]
    feature_matrix: Path
    hev_components: Path
    risk_surface: Path
    spatial_autocorrelation: Path
    allocation_parquet: Path
    project_json: Path
    projects_dir: Path
    aoi_geojson: Path

    def get_query_artifacts_map(self) -> Dict[str, Tuple[Path, str]]:
        """Builds artifacts map compatible with ZonalQueryEngine."""
        return {
            "feature_matrix": (
                self.feature_matrix,
                CANONICAL_EXPECTED_HASHES["canonical_feature_matrix.parquet"],
            ),
            "hev_components": (
                self.hev_components,
                CANONICAL_EXPECTED_HASHES["canonical_hev_components.parquet"],
            ),
            "risk_surface": (
                self.risk_surface,
                CANONICAL_EXPECTED_HASHES["canonical_risk_surface.parquet"],
            ),
            "spatial_autocorrelation": (
                self.spatial_autocorrelation,
                CANONICAL_EXPECTED_HASHES["canonical_spatial_autocorrelation.parquet"],
            ),
            "optimization_allocation": (
                self.allocation_parquet,
                CANONICAL_EXPECTED_HASHES["canonical_optimization_allocation.parquet"],
            ),
        }

    def get_allocation_df(self) -> pd.DataFrame:
        """Reads and returns the immutable canonical allocation dataframe."""
        df = pd.read_parquet(self.allocation_parquet)
        df.attrs["is_immutable"] = True
        return df


def _sync_s3_artifacts(bucket_name: str, region: str, cache_dir: Path) -> None:
    """Downloads required canonical working set from S3 and cryptographically verifies digests."""
    try:
        import boto3
    except ImportError:
        raise RuntimeError("boto3 is required for S3 runtime data loading but is not installed.")

    s3 = boto3.client("s3", region_name=region)
    logger.info(f"Synchronizing canonical scientific artifacts from s3://{bucket_name} to {cache_dir}...")

    artifacts_to_sync = [
        ("processed/feature-matrix/canonical_feature_matrix.parquet", cache_dir / "canonical_feature_matrix.parquet"),
        ("processed/hev/canonical_hev_components.parquet", cache_dir / "hev" / "canonical_hev_components.parquet"),
        ("processed/risk/canonical_risk_surface.parquet", cache_dir / "risk" / "canonical_risk_surface.parquet"),
        ("processed/spatial-autocorrelation/canonical_spatial_autocorrelation.parquet", cache_dir / "risk" / "canonical_spatial_autocorrelation.parquet"),
        ("processed/optimization/canonical_optimization_allocation.parquet", cache_dir / "optimization" / "canonical_optimization_allocation.parquet"),
        ("projects/project_pune_2025_tree_shade_10m.json", cache_dir / "projects" / "project_pune_2025_tree_shade_10m.json"),
        ("raw/aoi/pune.geojson", cache_dir / "aoi" / "pune.geojson"),
    ]

    for s3_key, dest_path in artifacts_to_sync:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        filename = dest_path.name
        expected_sha = CANONICAL_EXPECTED_HASHES.get(filename)

        # Check if already cached and verified
        if dest_path.exists() and expected_sha:
            actual_sha = calculate_sha256(dest_path)
            if actual_sha == expected_sha:
                logger.debug(f"Cached artifact verified: {filename}")
                continue

        logger.info(f"Downloading s3://{bucket_name}/{s3_key} -> {dest_path}...")
        s3.download_file(bucket_name, s3_key, str(dest_path))

        actual_sha = calculate_sha256(dest_path)
        if expected_sha and actual_sha != expected_sha:
            raise RuntimeError(
                f"S3 ARTIFACT CORRUPTION: SHA-256 mismatch on {s3_key}! "
                f"Expected {expected_sha}, got {actual_sha}."
            )
        logger.info(f"Verified SHA-256 on {filename} ({actual_sha})")


def get_runtime_data_paths() -> RuntimeDataPaths:
    """Resolves runtime data paths based on CLIMORA_DATA_MODE and environment."""
    mode = os.environ.get("CLIMORA_DATA_MODE", "").lower()
    s3_bucket = os.environ.get("CLIMORA_S3_BUCKET")

    # If S3 mode explicitly requested or bucket configured in cloud environment
    if mode == "s3" or s3_bucket:
        bucket = s3_bucket or DEFAULT_S3_BUCKET
        region = os.environ.get("AWS_DEFAULT_REGION", DEFAULT_S3_REGION)
        cache_dir = Path(os.environ.get("CLIMORA_DATA_CACHE_DIR", "/tmp/climora_data_cache"))
        cache_dir.mkdir(parents=True, exist_ok=True)

        _sync_s3_artifacts(bucket, region, cache_dir)

        return RuntimeDataPaths(
            data_mode="S3",
            s3_bucket=bucket,
            feature_matrix=cache_dir / "canonical_feature_matrix.parquet",
            hev_components=cache_dir / "hev" / "canonical_hev_components.parquet",
            risk_surface=cache_dir / "risk" / "canonical_risk_surface.parquet",
            spatial_autocorrelation=cache_dir / "risk" / "canonical_spatial_autocorrelation.parquet",
            allocation_parquet=cache_dir / "optimization" / "canonical_optimization_allocation.parquet",
            project_json=cache_dir / "projects" / "project_pune_2025_tree_shade_10m.json",
            projects_dir=cache_dir / "projects",
            aoi_geojson=cache_dir / "aoi" / "pune.geojson",
        )

    # Local mode (development & unit tests)
    return RuntimeDataPaths(
        data_mode="LOCAL",
        s3_bucket=None,
        feature_matrix=PROCESSED_DIR / "canonical_feature_matrix.parquet",
        hev_components=PROCESSED_DIR / "hev" / "canonical_hev_components.parquet",
        risk_surface=PROCESSED_DIR / "risk" / "canonical_risk_surface.parquet",
        spatial_autocorrelation=PROCESSED_DIR / "risk" / "canonical_spatial_autocorrelation.parquet",
        allocation_parquet=PROCESSED_DIR / "optimization" / "canonical_optimization_allocation.parquet",
        project_json=PROCESSED_DIR / "projects" / "project_pune_2025_tree_shade_10m.json",
        projects_dir=PROCESSED_DIR / "projects",
        aoi_geojson=PROJECT_ROOT / "data" / "aoi" / "pune.geojson",
    )
