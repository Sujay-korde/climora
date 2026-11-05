"""CLIMORA Trusted Authentication Service.

Implements cryptographically signed JWT Bearer token authentication.
Eliminates all reliance on untrusted client headers (X-Climora-Actor) and query parameters (?actor=).
Enforces zero test-mode authorization bypasses: all protected endpoints require authenticated principals.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
import os
from typing import Any, Dict, Optional, Tuple

import jwt

from services.cedar_service import DEMO_ACTORS
from services.exceptions import AuthenticationRequiredError, AuthorizationDeniedError

# Secret key for signing and verifying tokens
# In production, injected via CLIMORA_AUTH_SECRET environment variable.
JWT_SECRET_KEY = os.environ.get(
    "CLIMORA_AUTH_SECRET",
    "climora-production-security-secret-key-2026-audit-gate-freeze"
)
JWT_ALGORITHM = "HS256"
JWT_ISSUER = "climora-auth-service"
JWT_AUDIENCE = "climora-api"
DEFAULT_TOKEN_TTL_SECONDS = 86400  # 24 hours


def mint_actor_token(
    actor_id: str,
    ttl_seconds: int = DEFAULT_TOKEN_TTL_SECONDS,
    custom_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Mints a cryptographically signed JWT Bearer token for a registered actor."""
    if actor_id not in DEMO_ACTORS:
        raise ValueError(f"Unknown actor identifier '{actor_id}'. Must be a registered principal.")

    actor_info = DEMO_ACTORS[actor_id]
    now = datetime.now(timezone.utc)
    exp = now + timedelta(seconds=ttl_seconds)

    payload = {
        "sub": actor_id,
        "name": actor_info["name"],
        "role": actor_info["role"],
        "organization": actor_info["organization"],
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    if custom_claims:
        payload.update(custom_claims)

    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_bearer_token(auth_header: Optional[str]) -> Tuple[str, Dict[str, Any]]:
    """Validates an incoming Authorization header and resolves the authenticated principal.
    
    Returns:
        Tuple of (actor_id, actor_info_from_server_registry).
    
    Raises:
        AuthenticationRequiredError (HTTP 401) on missing, expired, forged, or invalid tokens.
    """
    if not auth_header or not isinstance(auth_header, str):
        raise AuthenticationRequiredError(
            message="Authentication required: Missing Authorization header with Bearer token.",
            details={"reason": "MISSING_AUTHORIZATION_HEADER"},
        )

    parts = auth_header.strip().split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthenticationRequiredError(
            message="Invalid Authorization header format. Must be: 'Bearer <token>'.",
            details={"reason": "INVALID_HEADER_FORMAT"},
        )

    token = parts[1]

    try:
        decoded = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
            options={"require": ["exp", "iss", "aud", "sub"]},
        )
    except jwt.ExpiredSignatureError:
        raise AuthenticationRequiredError(
            message="Authentication token has expired.",
            details={"reason": "TOKEN_EXPIRED"},
        )
    except jwt.InvalidSignatureError:
        raise AuthenticationRequiredError(
            message="Authentication token signature verification failed.",
            details={"reason": "INVALID_SIGNATURE"},
        )
    except jwt.InvalidTokenError as e:
        raise AuthenticationRequiredError(
            message=f"Invalid authentication token: {str(e)}",
            details={"reason": "INVALID_TOKEN"},
        )

    actor_id = decoded.get("sub")
    if not actor_id or actor_id not in DEMO_ACTORS:
        raise AuthenticationRequiredError(
            message=f"Principal '{actor_id}' is not recognized in the server identity registry.",
            details={"reason": "UNKNOWN_PRINCIPAL", "actor_id": actor_id},
        )

    # Server-side registry is the strict source of truth for principal role and metadata
    actor_info = DEMO_ACTORS[actor_id]
    return actor_id, actor_info


def create_auth_headers(actor_id: str) -> Dict[str, str]:
    """Helper for tests and trusted callers to generate valid Authorization headers."""
    token = mint_actor_token(actor_id)
    return {"Authorization": f"Bearer {token}"}

