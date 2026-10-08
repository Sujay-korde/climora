"""CLIMORA API Correlation & Observability Middleware.

Provides request correlation IDs, high-resolution execution timing,
safe telemetry logging, and security headers.
"""

from __future__ import annotations

import re
import time
import uuid
from typing import Optional
from flask import Flask, g, request

from ingestion.common import get_logger

logger = get_logger()

CORRELATION_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-\.]{8,64}$")


def get_current_correlation_id() -> str:
    """Returns the correlation ID for the current request context."""
    return getattr(g, "correlation_id", "UNKNOWN-CORRELATION")


def setup_observability_middleware(app: Flask) -> None:
    """Registers request correlation, execution timing, and structured telemetry handlers."""

    @app.before_request
    def before_request_hook():
        g.start_time = time.perf_counter()

        # Check for client-supplied correlation ID
        client_corr_id = request.headers.get("X-Correlation-ID") or request.headers.get("X-Request-ID")
        if client_corr_id and CORRELATION_ID_PATTERN.match(client_corr_id.strip()):
            corr_id = client_corr_id.strip()
        else:
            corr_id = f"corr-{uuid.uuid4().hex[:12]}"

        g.correlation_id = corr_id

    @app.after_request
    def after_request_hook(response):
        start_time = getattr(g, "start_time", None)
        corr_id = getattr(g, "correlation_id", "UNKNOWN-CORRELATION")

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 3) if start_time else 0.0

        # Inject correlation & performance headers
        response.headers["X-Correlation-ID"] = corr_id
        response.headers["X-Request-ID"] = corr_id
        response.headers["X-Response-Time-Ms"] = str(elapsed_ms)

        # Structured operational log without logging raw request bodies or secrets
        logger.info(
            f"correlation_id={corr_id} method={request.method} path={request.path} "
            f"status={response.status_code} elapsed_ms={elapsed_ms}"
        )

        return response
