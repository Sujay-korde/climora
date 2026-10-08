"""CLIMORA Production Flask API Application Factory.

Phase 2A Service Boundary:
- Controlled interface around frozen scientific artifacts.
- Zero scientific calculation in route handlers.
- Unified structured JSON error handling.
- Sanitized responses preventing stack trace or internal path leaks.
"""

from __future__ import annotations

import importlib.metadata
from datetime import datetime, timezone
import os
from typing import Any, Dict, Optional
import werkzeug

# Flask 2.3.2 / Werkzeug 3.x compatibility patch for test_client
if not hasattr(werkzeug, "__version__"):
    try:
        werkzeug.__version__ = importlib.metadata.version("werkzeug")
    except Exception:
        werkzeug.__version__ = "3.1.3"

from flask import Flask, jsonify, make_response, request

from api.middleware import setup_observability_middleware
from api.openapi import get_openapi_spec, get_swagger_ui_html
from api.routes.projects import projects_bp
from services.allocation_service import AllocationDomainService
from services.baseline_service import BaselineDomainService
from services.exceptions import ClimoraServiceError
from services.mrv_service import MRVDomainService
from services.project_service import ProjectDomainService
from services.query_layer import ZonalQueryEngine
from services.runtime_data import get_runtime_data_paths


def create_app(config_dict: Optional[Dict[str, Any]] = None) -> Flask:
    """Creates and configures the CLIMORA Production Flask Application."""
    app = Flask(__name__)
    if config_dict:
        app.config.update(config_dict)

    # Attach observability, correlation ID, timing, and security headers middleware
    setup_observability_middleware(app)

    # Resolve runtime data paths (transparent LOCAL vs S3 data lake modes)
    if "RUNTIME_PATHS" not in app.config:
        app.config["RUNTIME_PATHS"] = get_runtime_data_paths()
    runtime_paths = app.config["RUNTIME_PATHS"]

    # Initialize shared ZonalQueryEngine
    if "QUERY_ENGINE" not in app.config:
        artifacts_map = runtime_paths.get_query_artifacts_map() if runtime_paths else None
        app.config["QUERY_ENGINE"] = ZonalQueryEngine(artifacts_map=artifacts_map)

    # Initialize and bind domain services
    if "MRV_SERVICE" not in app.config:
        alloc_df = runtime_paths.get_allocation_df() if runtime_paths else None
        app.config["MRV_SERVICE"] = MRVDomainService(allocation_df=alloc_df)
    if "PROJECT_SERVICE" not in app.config:
        proj_kwargs = {"mrv_service": app.config["MRV_SERVICE"]}
        if runtime_paths and runtime_paths.projects_dir:
            proj_kwargs["projects_dir"] = runtime_paths.projects_dir
        app.config["PROJECT_SERVICE"] = ProjectDomainService(**proj_kwargs)
    else:
        app.config["PROJECT_SERVICE"].set_mrv_service(app.config["MRV_SERVICE"])
    if "ALLOCATION_SERVICE" not in app.config:
        alloc_kwargs = {"query_engine": app.config["QUERY_ENGINE"]}
        if runtime_paths and runtime_paths.allocation_parquet:
            alloc_kwargs["allocation_parquet_path"] = runtime_paths.allocation_parquet
        app.config["ALLOCATION_SERVICE"] = AllocationDomainService(**alloc_kwargs)
    if "BASELINE_SERVICE" not in app.config:
        app.config["BASELINE_SERVICE"] = BaselineDomainService(query_engine=app.config["QUERY_ENGINE"])
    if "CEDAR_SERVICE" not in app.config:
        from services.cedar_service import CedarGovernanceService
        app.config["CEDAR_SERVICE"] = CedarGovernanceService()

    # Register blueprints
    app.register_blueprint(projects_bp, url_prefix="/projects")
    app.register_blueprint(projects_bp, url_prefix="/api/v1/projects", name="projects_v1")

    # ==========================================================================
    # Global Error Handlers (Unified Structured Error Contract)
    # ==========================================================================

    @app.errorhandler(ClimoraServiceError)
    def handle_climora_service_error(err: ClimoraServiceError):
        """Maps domain exceptions to the required JSON error envelope."""
        return jsonify({
            "error": {
                "code": err.code,
                "message": err.message,
                "details": err.details,
            }
        }), err.status_code

    @app.errorhandler(400)
    def handle_bad_request(err):
        return jsonify({
            "error": {
                "code": "BAD_REQUEST",
                "message": "The server could not understand the request or body format.",
                "details": {},
            }
        }), 400

    @app.errorhandler(404)
    def handle_not_found(err):
        return jsonify({
            "error": {
                "code": "RESOURCE_NOT_FOUND",
                "message": "The requested API endpoint or resource was not found.",
                "details": {},
            }
        }), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(err):
        return jsonify({
            "error": {
                "code": "METHOD_NOT_ALLOWED",
                "message": "HTTP method not allowed on this resource.",
                "details": {},
            }
        }), 405

    @app.errorhandler(422)
    def handle_unprocessable_entity(err):
        return jsonify({
            "error": {
                "code": "UNPROCESSABLE_ENTITY",
                "message": "The request payload was well-formed but contains semantic errors.",
                "details": {},
            }
        }), 422

    @app.errorhandler(500)
    def handle_internal_server_error(err):
        """Sanitizes internal server errors. Never leaks stack traces or local paths."""
        return jsonify({
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected internal error occurred. Operational details logged securely.",
                "details": {},
            }
        }), 500

    # ==========================================================================
    # Health & Meta Endpoints
    # ==========================================================================

    @app.before_request
    def handle_options_preflight():
        if request.method == "OPTIONS":
            resp = make_response("", 204)
            return resp

    @app.route("/", methods=["GET"])
    @app.route("/health", methods=["GET"])
    def health_check():
        engine = app.config.get("QUERY_ENGINE")
        cache_stats = engine.cache.stats if engine else {}
        runtime_paths = app.config.get("RUNTIME_PATHS")
        data_mode = runtime_paths.data_mode if runtime_paths else "LOCAL"
        s3_bucket = runtime_paths.s3_bucket if runtime_paths else None
        return jsonify({
            "status": "HEALTHY",
            "service": "CLIMORA Production API & Service Boundary",
            "version": "1.1.0",
            "phase": "Phase AWS-3 (Containerized & S3-Integrated)",
            "scientific_architecture": "FROZEN",
            "data_mode": data_mode,
            "s3_bucket": s3_bucket,
            "canonical_project_id": "PROJ-PUNE-2025-BA225D6A",
            "optimization_run_id": "OPT-PUNE-2025-SCENARIO-BA225D6A",
            "h3_resolution": 9,
            "cache": cache_stats,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }), 200

    @app.route("/cache/stats", methods=["GET"])
    def cache_stats():
        engine = app.config.get("QUERY_ENGINE")
        stats = engine.cache.stats if engine else {}
        return jsonify({
            "status": "SUCCESS",
            "cache": stats,
        }), 200

    @app.route("/openapi.json", methods=["GET"])
    def openapi_json():
        return jsonify(get_openapi_spec()), 200

    @app.route("/docs", methods=["GET"])
    def swagger_ui():
        resp = make_response(get_swagger_ui_html())
        resp.headers["Content-Type"] = "text/html; charset=utf-8"
        return resp

    # ==========================================================================
    # Security Headers & CORS
    # ==========================================================================

    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # CORS Support for local dev and cloud frontend
        allowed_origins_env = os.environ.get(
            "CLIMORA_CORS_ALLOWED_ORIGINS",
            "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173",
        )
        if allowed_origins_env == "*":
            response.headers["Access-Control-Allow-Origin"] = "*"
        else:
            allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
            request_origin = request.headers.get("Origin")
            if request_origin and (request_origin in allowed_origins or "*" in allowed_origins):
                response.headers["Access-Control-Allow-Origin"] = request_origin
                response.headers["Vary"] = "Origin"

        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = (
            "Content-Type, Authorization, X-Correlation-ID, X-Request-ID, X-Climora-Actor"
        )
        return response

    return app


if __name__ == "__main__":
    # Local dev server invocation
    app = create_app()
    app.run(host="0.0.0.0", port=8000, debug=False)
