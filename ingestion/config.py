"""Configuration loader for CLIMORA ingestion foundation."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml


@dataclass
class SourceConfig:
    enabled: bool = True
    collection: Optional[str] = None
    stac_api_url: Optional[str] = None
    cloud_cover_max: float = 20.0
    required_assets: List[str] = field(default_factory=list)
    required_bands: List[str] = field(default_factory=list)
    download_limit: int = 1
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IngestionConfig:
    project_root: Path
    aoi_path: Path
    data_root: Path
    raw_dir: Path
    manifests_dir: Path
    year: int
    start_date: str
    end_date: str
    sources: Dict[str, Any]
    study_area: str = "Pune"
    project_name: str = "CLIMORA"
    selection: Dict[str, Any] = field(default_factory=dict)
    storage: Dict[str, Any] = field(default_factory=dict)
    download_retries: int = 3
    download_timeout: int = 60
    chunk_size_bytes: int = 1048576

    @property
    def storage_warning_threshold_gb(self) -> float:
        return float(self.storage.get("warning_threshold_gb", 4.0))

    @property
    def selection_strategy(self) -> str:
        return str(self.selection.get("strategy", "seasonal_representative"))

    @property
    def target_per_season(self) -> int:
        return int(self.selection.get("target_per_season", 1))

    @property
    def seasons(self) -> Dict[str, Dict[str, str]]:
        return self.selection.get("seasons", {})

    def get_source_raw_dir(self, source_name: str, subpath: str = "") -> Path:
        """Return deterministic raw directory for a given data source."""
        base = self.raw_dir / source_name
        if subpath:
            base = base / subpath
        base.mkdir(parents=True, exist_ok=True)
        return base

    def get_manifest_path(self, filename: str = "pune_2025_acquisition_plan.json") -> Path:
        """Return the path to the acquisition manifest."""
        self.manifests_dir.mkdir(parents=True, exist_ok=True)
        return self.manifests_dir / filename


def load_config(config_path: Optional[Path | str] = None) -> IngestionConfig:
    """Load configuration from config.yaml with environment variable overrides."""
    # Find project root
    if config_path:
        cfg_file = Path(config_path).resolve()
        project_root = cfg_file.parent
    else:
        project_root = Path(__file__).resolve().parent.parent
        cfg_file = project_root / "config.yaml"

    if not cfg_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {cfg_file}")

    with open(cfg_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    # Path overrides via environment
    paths_data = data.get("paths", {})
    env_data_root = os.getenv("CLIMORA_DATA_ROOT")
    if env_data_root:
        data_root = Path(env_data_root).resolve()
    else:
        data_root = (project_root / paths_data.get("data_root", "data")).resolve()

    env_aoi = os.getenv("CLIMORA_AOI_PATH")
    if env_aoi:
        aoi_path = Path(env_aoi).resolve()
    else:
        aoi_path = (project_root / paths_data.get("aoi_path", "data/aoi/pune.geojson")).resolve()

    raw_dir = (project_root / paths_data.get("raw_dir", "data/raw")).resolve()
    manifests_dir = (project_root / paths_data.get("manifests_dir", "data/manifests")).resolve()

    temporal = data.get("temporal", {})
    year = int(temporal.get("year", 2025))
    start_date = str(temporal.get("start_date", f"{year}-01-01"))
    end_date = str(temporal.get("end_date", f"{year}-12-31"))

    download_cfg = data.get("download", {})

    proj_data = data.get("project", {})
    study_area = str(proj_data.get("study_area", "Pune"))
    project_name = str(proj_data.get("name", "CLIMORA"))
    selection_cfg = data.get("selection", {})
    storage_cfg = data.get("storage", {})

    return IngestionConfig(
        project_root=project_root,
        aoi_path=aoi_path,
        data_root=data_root,
        raw_dir=raw_dir,
        manifests_dir=manifests_dir,
        year=year,
        start_date=start_date,
        end_date=end_date,
        sources=data.get("sources", {}),
        study_area=study_area,
        project_name=project_name,
        selection=selection_cfg,
        storage=storage_cfg,
        download_retries=int(download_cfg.get("max_retries", 3)),
        download_timeout=int(download_cfg.get("timeout_seconds", 60)),
        chunk_size_bytes=int(download_cfg.get("chunk_size_bytes", 1048576)),
    )
