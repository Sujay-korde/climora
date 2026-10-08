"""CLIMORA Phase 1A.8 Temporal Processing, AOI Clipping & Spatial Harmonization.

Package providing reproducible, validated processing of the 2021-2025 Pune baseline.
"""

from processing.config import (
    PROCESSING_PHASE,
    PROCESSING_VERSION,
    LANDSAT_TEMPORAL_BASELINE,
)

__version__ = PROCESSING_VERSION
__all__ = ["PROCESSING_PHASE", "PROCESSING_VERSION", "LANDSAT_TEMPORAL_BASELINE"]
