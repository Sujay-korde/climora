"""CLIMORA OpenAPI 3.0 Specification Generator.

Provides the machine-readable OpenAPI schema and interactive documentation page.
"""

from typing import Any, Dict


def get_openapi_spec() -> Dict[str, Any]:
    """Returns the official OpenAPI 3.0.0 JSON schema for the CLIMORA Phase 2B API."""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "CLIMORA Production API & Service Boundary",
            "version": "1.1.0",
            "description": (
                "Authoritative API interface around the frozen CLIMORA scientific and data intelligence system. "
                "Hardened for production with read-only zonal querying, SHA-keyed caching, deterministic pagination, "
                "strict input validation, request correlation, truth-layer taxonomy (OBSERVED, DERIVED, MODELED, VERIFIED), "
                "allocation immutability, metric-specific sensor compatibility, and strict MRV verification state machines."
            ),
            "contact": {
                "name": "CLIMORA Systems & Governance Architecture Team",
                "email": "architecture@climora.org",
            },
        },
        "servers": [
            {"url": "/", "description": "Local / Production Gateway"},
            {"url": "/api/v1", "description": "Versioned Gateway (v1)"},
        ],
        "tags": [
            {"name": "Projects", "description": "Bankable climate adaptation project lifecycle and representation"},
            {"name": "Allocation", "description": "Immutable optimization portfolio allocations and auditable revisions"},
            {"name": "Baseline", "description": "Multi-year thermal, ecological, demographic, and risk baseline evidence"},
            {"name": "MRV", "description": "Physical implementation events, observation audits, and verification gating"},
            {"name": "System", "description": "Service health, telemetry, and operational status"},
        ],
        "paths": {
            "/health": {
                "get": {
                    "tags": ["System"],
                    "summary": "System Health & Scientific Freeze Status",
                    "responses": {
                        "200": {"description": "Service is healthy and scientific pipeline is frozen"}
                    },
                }
            },
            "/cache/stats": {
                "get": {
                    "tags": ["System"],
                    "summary": "Cache Performance & Telemetry",
                    "description": "Returns query cache hit/miss counts, hit ratios, and memory occupancy.",
                    "responses": {
                        "200": {"description": "Cache statistics"}
                    },
                }
            },
            "/projects": {
                "get": {
                    "tags": ["Projects"],
                    "summary": "List Project Summaries",
                    "description": "Returns high-level project summaries adhering to frozen canonical contracts.",
                    "responses": {
                        "200": {"description": "Project summaries list"}
                    },
                }
            },
            "/projects/{project_id}": {
                "get": {
                    "tags": ["Projects"],
                    "summary": "Get Complete Project Representation",
                    "description": "Returns authoritative 13-section structured project proposal representation.",
                    "parameters": [
                        {"name": "project_id", "in": "path", "required": True, "schema": {"type": "string"}}
                    ],
                    "responses": {
                        "200": {"description": "Complete project representation"},
                        "400": {"description": "Validation error"},
                        "404": {"description": "Project not found"},
                    },
                }
            },
            "/projects/{project_id}/allocation": {
                "get": {
                    "tags": ["Allocation"],
                    "summary": "Get Canonical Allocation",
                    "description": "Reads the immutable canonical optimization allocation with bounded pagination. Does NOT silently recompute.",
                    "parameters": [
                        {"name": "project_id", "in": "path", "required": True, "schema": {"type": "string"}},
                        {"name": "page", "in": "query", "required": False, "schema": {"type": "integer", "default": 1, "minimum": 1}},
                        {"name": "page_size", "in": "query", "required": False, "schema": {"type": "integer", "default": 28, "minimum": 1, "maximum": 100}},
                        {"name": "h3_cell_id", "in": "query", "required": False, "schema": {"type": "string", "pattern": "^8[0-9a-fA-F]{14}$"}},
                    ],
                    "responses": {
                        "200": {"description": "Canonical allocation items and portfolio summary"},
                        "400": {"description": "Invalid query parameters"},
                        "404": {"description": "Project not found"},
                    },
                },
                "put": {
                    "tags": ["Allocation"],
                    "summary": "Prohibit Direct Allocation Overwrite",
                    "responses": {
                        "405": {"description": "Method Not Allowed. Canonical allocation is immutable."}
                    },
                },
                "patch": {
                    "tags": ["Allocation"],
                    "summary": "Prohibit Direct Allocation Mutation",
                    "responses": {
                        "405": {"description": "Method Not Allowed. Canonical allocation is immutable."}
                    },
                },
                "delete": {
                    "tags": ["Allocation"],
                    "summary": "Prohibit Allocation Deletion",
                    "responses": {
                        "405": {"description": "Method Not Allowed. Canonical allocation is immutable."}
                    },
                },
            },
            "/projects/{project_id}/baseline": {
                "get": {
                    "tags": ["Baseline"],
                    "summary": "Get Baseline Evidence",
                    "description": "Exposes baseline observational, derived, and modeled evidence with truth layers and bounded pagination.",
                    "parameters": [
                        {"name": "project_id", "in": "path", "required": True, "schema": {"type": "string"}},
                        {"name": "page", "in": "query", "required": False, "schema": {"type": "integer", "default": 1, "minimum": 1}},
                        {"name": "page_size", "in": "query", "required": False, "schema": {"type": "integer", "default": 28, "minimum": 1, "maximum": 100}},
                        {"name": "h3_cell_id", "in": "query", "required": False, "schema": {"type": "string", "pattern": "^8[0-9a-fA-F]{14}$"}},
                        {"name": "limit", "in": "query", "required": False, "schema": {"type": "integer", "minimum": 1, "maximum": 100}}
                    ],
                    "responses": {
                        "200": {"description": "Baseline summary and cell-level metrics"},
                        "400": {"description": "Invalid query parameters"},
                        "404": {"description": "Project not found"},
                    },
                }
            },
            "/projects/{project_id}/mrv": {
                "get": {
                    "tags": ["MRV"],
                    "summary": "Get MRV Tracking & Verification Readiness",
                    "description": "Returns implementation events, deviation metrics, and DID readiness status.",
                    "parameters": [
                        {"name": "project_id", "in": "path", "required": True, "schema": {"type": "string"}}
                    ],
                    "responses": {
                        "200": {"description": "MRV status, events, and DID status"},
                        "400": {"description": "Invalid project ID"},
                        "404": {"description": "Project not found"},
                    },
                }
            },
            "/projects/{project_id}/implementation-events": {
                "post": {
                    "tags": ["MRV"],
                    "summary": "Record Implementation Event",
                    "description": "Records real-world contractor physical deployment and computes physical deviation.",
                    "parameters": [
                        {"name": "project_id", "in": "path", "required": True, "schema": {"type": "string"}}
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["intervention_code", "h3_cell_id", "implemented_quantity", "completion_date", "evidence_uri"],
                                    "properties": {
                                        "intervention_code": {"type": "string"},
                                        "h3_cell_id": {"type": "string"},
                                        "implemented_quantity": {"type": "number", "minimum": 0.0},
                                        "quantity_unit": {"type": "string", "default": "tree_count"},
                                        "completion_date": {"type": "string", "format": "date"},
                                        "contractor_id": {"type": "string"},
                                        "evidence_uri": {"type": "string"},
                                        "is_synthetic_demo": {"type": "boolean", "default": False},
                                    },
                                }
                            }
                        },
                    },
                    "responses": {
                        "201": {"description": "Implementation event recorded"},
                        "400": {"description": "Validation error"},
                        "404": {"description": "Project not found"},
                    },
                }
            },
            "/projects/{project_id}/verification-events": {
                "post": {
                    "tags": ["MRV"],
                    "summary": "Submit Formal Verification Milestone",
                    "description": "Heavily guarded. Evaluates full MRV QC prerequisites, sensor compatibility, and anti-contamination rules.",
                    "parameters": [
                        {"name": "project_id", "in": "path", "required": True, "schema": {"type": "string"}}
                    ],
                    "responses": {
                        "201": {"description": "Verification certified"},
                        "400": {"description": "Validation error"},
                        "422": {"description": "Verification not eligible (prerequisites failed or synthetic data rejected)"},
                    },
                }
            },
            "/projects/{project_id}/transition": {
                "post": {
                    "tags": ["Projects"],
                    "summary": "Transition Project Lifecycle State",
                    "description": "Evaluates lifecycle transition against ProjectStateMachine governance rules.",
                    "parameters": [
                        {"name": "project_id", "in": "path", "required": True, "schema": {"type": "string"}}
                    ],
                    "responses": {
                        "200": {"description": "State transition authorized"},
                        "422": {"description": "Illegal state transition or missing prerequisites"},
                    },
                }
            },
            "/projects/{project_id}/revisions": {
                "post": {
                    "tags": ["Allocation"],
                    "summary": "Propose Allocation Revision",
                    "description": "Proposes a transparent human modification without mutating canonical optimization parquet.",
                    "parameters": [
                        {"name": "project_id", "in": "path", "required": True, "schema": {"type": "string"}}
                    ],
                    "responses": {
                        "201": {"description": "Revision recorded"},
                        "400": {"description": "Validation error"},
                    },
                }
            },
        },
    }


def get_swagger_ui_html() -> str:
    """Returns self-contained Swagger UI HTML."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>CLIMORA API Documentation — Phase 2A</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui.css" />
  <style>
    body { margin: 0; background: #0f172a; }
    .topbar { display: none !important; }
    .swagger-ui { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    .swagger-ui .info .title { color: #38bdf8; }
    .swagger-ui .scheme-container { background: #1e293b; color: #f8fafc; }
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui-bundle.js"></script>
  <script>
    window.onload = () => {
      window.ui = SwaggerUIBundle({
        url: '/openapi.json',
        dom_id: '#swagger-ui',
        deepLinking: true,
        presets: [SwaggerUIBundle.presets.apis],
      });
    };
  </script>
</body>
</html>
"""
