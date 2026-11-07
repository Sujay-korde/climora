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

# Enterprise OIDC Configuration
CLIMORA_AUTH_MODE = os.environ.get("CLIMORA_AUTH_MODE", "DEMO").upper()
OIDC_ISSUER = os.environ.get(
    "CLIMORA_OIDC_ISSUER",
    "https://cognito-idp.ap-south-1.amazonaws.com/ap-south-1_climora"
)
OIDC_AUDIENCE = os.environ.get("CLIMORA_OIDC_AUDIENCE", "climora-enterprise-pune")
OIDC_CLIENT_ID = os.environ.get("CLIMORA_OIDC_CLIENT_ID", "climora-web-app-client")
OIDC_SECRET_KEY = os.environ.get("CLIMORA_OIDC_SECRET", JWT_SECRET_KEY)

# IdP Group / Role to Climora Cedar RBAC mapping
DEFAULT_ROLE_MAPPINGS = {
    "pmc_urban_planners": "project_manager",
    "pmc-urban-planners": "project_manager",
    "project_manager": "project_manager",
    "planner": "project_manager",
    "pmc_municipal_officers": "municipal_officer",
    "pmc-municipal-officers": "municipal_officer",
    "municipal_officer": "municipal_officer",
    "commissioner": "municipal_officer",
    "pmc_field_contractors": "field_contractor",
    "pmc-field-contractors": "field_contractor",
    "field_contractor": "field_contractor",
    "contractor": "field_contractor",
    "iso_14064_auditors": "mrv_verifier",
    "iso-14064-auditors": "mrv_verifier",
    "mrv_verifier": "mrv_verifier",
    "verifier": "mrv_verifier",
    "auditor": "mrv_verifier",
    "citizens": "citizen_viewer",
    "citizen_viewer": "citizen_viewer",
    "viewer": "citizen_viewer",
}


class OIDCAuthenticationProvider:
    """Enterprise OIDC Authentication Provider for Multi-Tenant Municipal Deployments.
    
    Validates enterprise OpenID Connect ID/Access tokens issued by accredited identity providers
    (e.g., AWS Cognito User Pools, Azure AD / Microsoft Entra, Okta, Keycloak).
    Maps enterprise identity claims and security groups to Climora Cedar RBAC roles.
    """

    def __init__(
        self,
        issuer: str = OIDC_ISSUER,
        audience: str = OIDC_AUDIENCE,
        secret_key: str = OIDC_SECRET_KEY,
        algorithm: str = JWT_ALGORITHM,
        role_mappings: Optional[Dict[str, str]] = None,
    ):
        self.issuer = issuer
        self.audience = audience
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.role_mappings = role_mappings or DEFAULT_ROLE_MAPPINGS

    def map_claims_to_role(self, claims: Dict[str, Any]) -> str:
        """Resolves Climora Cedar RBAC role from OIDC token claims."""
        # 1. Inspect explicit Climora role claim
        if "role" in claims and str(claims["role"]).lower() in self.role_mappings:
            return self.role_mappings[str(claims["role"]).lower()]

        # 2. Inspect Cognito / IdP security groups
        groups = claims.get("cognito:groups") or claims.get("groups") or claims.get("roles") or []
        if isinstance(groups, str):
            groups = [groups]
        for g in groups:
            g_norm = str(g).lower().strip()
            if g_norm in self.role_mappings:
                return self.role_mappings[g_norm]

        # 3. Inspect custom:role or scp
        custom_role = str(claims.get("custom:role", "")).lower().strip()
        if custom_role in self.role_mappings:
            return self.role_mappings[custom_role]

        # Default fallback to read-only citizen viewer
        return "citizen_viewer"

    def verify_oidc_token(self, token: str) -> Tuple[str, Dict[str, Any]]:
        """Verifies an enterprise OIDC token and returns the authenticated principal."""
        try:
            decoded = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                audience=self.audience,
                issuer=self.issuer,
                options={"require": ["exp", "iss", "aud", "sub"]},
            )
        except jwt.ExpiredSignatureError:
            raise AuthenticationRequiredError(
                message="Enterprise OIDC token has expired.",
                details={"reason": "OIDC_TOKEN_EXPIRED", "issuer": self.issuer},
            )
        except jwt.InvalidSignatureError:
            raise AuthenticationRequiredError(
                message="Enterprise OIDC token signature verification failed.",
                details={"reason": "OIDC_INVALID_SIGNATURE", "issuer": self.issuer},
            )
        except jwt.InvalidTokenError as e:
            raise AuthenticationRequiredError(
                message=f"Invalid enterprise OIDC token: {str(e)}",
                details={"reason": "OIDC_INVALID_TOKEN", "issuer": self.issuer},
            )

        sub = decoded.get("sub")
        if not sub:
            raise AuthenticationRequiredError(
                message="Enterprise OIDC token missing 'sub' subject claim.",
                details={"reason": "OIDC_MISSING_SUB"},
            )

        email = decoded.get("email") or f"{sub}@pmc.gov.in"
        name = decoded.get("name") or decoded.get("preferred_username") or email
        org = decoded.get("organization") or "Pune Municipal Corporation (PMC)"
        climora_role = self.map_claims_to_role(decoded)

        actor_info = {
            "name": name,
            "role": climora_role,
            "organization": org,
            "email": email,
            "sub": sub,
            "auth_provider": "OIDC",
            "issuer": self.issuer,
        }

        # Sub is treated as the actor principal ID in enterprise mode
        actor_id = f"oidc_{sub}"
        return actor_id, actor_info

    def mint_test_oidc_token(
        self,
        sub: str,
        role: str,
        email: Optional[str] = None,
        name: Optional[str] = None,
        ttl_seconds: int = 3600,
    ) -> str:
        """Helper to mint simulated enterprise OIDC tokens for testing and verification."""
        now = datetime.now(timezone.utc)
        exp = now + timedelta(seconds=ttl_seconds)
        payload = {
            "sub": sub,
            "email": email or f"{sub}@pmc.gov.in",
            "name": name or f"Enterprise User ({sub})",
            "cognito:groups": [role],
            "organization": "Pune Municipal Corporation (Enterprise)",
            "iss": self.issuer,
            "aud": self.audience,
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)


# Global enterprise OIDC provider instance
oidc_provider = OIDCAuthenticationProvider()


def get_oidc_provider() -> OIDCAuthenticationProvider:
    return oidc_provider


def get_auth_mode() -> str:
    return os.environ.get("CLIMORA_AUTH_MODE", CLIMORA_AUTH_MODE).upper()


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
    
    Supports both local DEMO authentication and enterprise OIDC authentication.
    
    Returns:
        Tuple of (actor_id, actor_info).
    
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
    mode = get_auth_mode()

    # 1. Strict Enterprise OIDC Mode
    if mode == "OIDC":
        return oidc_provider.verify_oidc_token(token)

    # 2. Demo Mode (with transparent fallback to OIDC if token was issued by IdP)
    try:
        decoded = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
            options={"require": ["exp", "iss", "aud", "sub"]},
        )
    except jwt.InvalidIssuerError:
        # Check if this is an enterprise OIDC token
        try:
            return oidc_provider.verify_oidc_token(token)
        except Exception:
            raise AuthenticationRequiredError(
                message="Authentication token issuer is invalid.",
                details={"reason": "INVALID_ISSUER"},
            )
    except jwt.InvalidAudienceError:
        # Check if audience matches enterprise OIDC audience
        try:
            return oidc_provider.verify_oidc_token(token)
        except Exception:
            raise AuthenticationRequiredError(
                message="Authentication token audience is invalid.",
                details={"reason": "INVALID_AUDIENCE"},
            )
    except jwt.ExpiredSignatureError:
        raise AuthenticationRequiredError(
            message="Authentication token has expired.",
            details={"reason": "TOKEN_EXPIRED"},
        )
    except jwt.InvalidSignatureError:
        # Check if signed with OIDC secret
        try:
            return oidc_provider.verify_oidc_token(token)
        except Exception:
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

