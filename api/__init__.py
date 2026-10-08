"""CLIMORA Phase 2A Production API Package.

Provides clean HTTP service boundaries around the canonical scientific system.
"""

from api.app import create_app

__all__ = ["create_app"]
