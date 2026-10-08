"""CLIMORA Baseline Domain Service.

Provides analytical baseline evidence across the 28 selected cells in the project footprint.
Adheres strictly to the Truth-Layer Contract (OBSERVED vs DERIVED vs MODELED).
Never exposes raw raster contents.
Delegates high-performance retrieval and caching to the ZonalQueryEngine.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from ingestion.common import get_logger
from services.query_layer import ZonalQueryEngine

logger = get_logger()


class BaselineDomainService:
    """Application service for querying baseline observational, derived, and modeled evidence."""

    def __init__(self, query_engine: Optional[ZonalQueryEngine] = None):
        self.query_engine = query_engine or ZonalQueryEngine()

    def get_project_baseline(
        self,
        project_id: str,
        h3_cell_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 28,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Returns structured analytical baseline evidence for the project's selected cells."""
        return self.query_engine.query_baseline(
            project_id=project_id,
            h3_cell_id=h3_cell_id,
            page=page,
            page_size=page_size,
            limit=limit,
        )

    def get_risk_surface(self, project_id: str) -> Dict[str, Any]:
        """Returns the complete citywide canonical risk surface across all H3 cells in the analytical mesh."""
        return self.query_engine.query_risk_surface(project_id=project_id)

    def get_boundary(self, project_id: str) -> Dict[str, Any]:
        """Returns the canonical Pune AOI GeoJSON boundary."""
        return self.query_engine.query_boundary(project_id=project_id)

