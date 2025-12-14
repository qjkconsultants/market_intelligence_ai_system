from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import httpx
import structlog
from jose import jwt
from jose.exceptions import JWTError

from .settings import settings

log = structlog.get_logger()

@dataclass(frozen=True)
class AuthContext:
    user_id: str
    tenant_id: str
    roles: List[str]
    groups: List[str]
    raw_claims: Dict[str, Any]

class JwksCache:
    """Tiny in-memory JWKS cache.

    Production note: in AWS you may prefer caching in-process with TTL, or use
    the IdP discovery document + library caches. This minimal cache keeps the
    scaffold self-contained.
    """
    def __init__(self):
        self._jwks: Optional[Dict[str, Any]] = None

    def get(self) -> Optional[Dict[str, Any]]:
        return self._jwks

    def set(self, jwks: Dict[str, Any]) -> None:
        self._jwks = jwks

_jwks_cache = JwksCache()

def _load_rbac_policy() -> Dict[str, List[str]]:
    try:
        data = json.loads(settings.rbac_policy_json or "{}")
        if not isinstance(data, dict):
            return {}
        # normalize: keys uppercase for easier matching
        return {str(k).upper(): [str(x) for x in v] for k, v in data.items()}
    except Exception:
        return {}

_RBAC = _load_rbac_policy()

def authorize_domain_access(domain_id: str, roles: List[str], groups: List[str]) -> None:
    """RBAC gate for domain_id.

    Rules:
      - If any role/group maps to ['*'] => allow all.
      - Else allow if domain_id appears in allowed list for any role/group.
      - If no policy configured => deny (safer default in prod).
    """
    dom = (domain_id or "").lower()
    if not _RBAC:
        # If you want a permissive dev-mode, keep AUTH_ENABLED=false.
        raise PermissionError("RBAC policy not configured")

    principals = [r.upper() for r in roles] + [g.upper() for g in groups]
    for p in principals:
        allowed = _RBAC.get(p, [])
        if "*" in allowed:
            return
        if dom in [a.lower() for a in allowed]:
            return
    raise PermissionError(f"Access denied for domain '{domain_id}'")

async def _fetch_jwks() -> Dict[str, Any]:
    if not settings.jwks_url:
        raise RuntimeError("JWKS_URL not set")
    cached = _jwks_cache.get()
    if cached:
        return cached
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(settings.jwks_url)
        resp.raise_for_status()
        jwks = resp.json()
        _jwks_cache.set(jwks)
        return jwks

async def authenticate_bearer_token(authorization_header: str) -> AuthContext:
    """Validate JWT and produce AuthContext.

    Production expectation:
      - AUTH_ENABLED=true
      - JWT_ISSUER/JWT_AUDIENCE set
      - JWKS_URL set (or you can derive from issuer's discovery endpoint)
    """
    if not authorization_header or not authorization_header.startswith("Bearer "):
        raise PermissionError("Missing or invalid Authorization header")
    token = authorization_header.split(" ", 1)[1].strip()

    jwks = await _fetch_jwks()
    try:
        claims = jwt.decode(
            token,
            jwks,
            algorithms=["RS256", "ES256"],
            issuer=settings.jwt_issuer or None,
            audience=settings.jwt_audience or None,
            options={
                "verify_signature": True,
                "verify_aud": bool(settings.jwt_audience),
                "verify_iss": bool(settings.jwt_issuer),
            },
        )
    except JWTError as e:
        log.warning("jwt_validation_failed", error=str(e))
        raise PermissionError("Invalid token") from e

    user_id = str(claims.get("sub", ""))
    tenant_id = str(claims.get(settings.tenant_claim, ""))
    roles = claims.get(settings.roles_claim, []) or []
    groups = claims.get(settings.groups_claim, []) or []
    if isinstance(roles, str):
        roles = [roles]
    if isinstance(groups, str):
        groups = [groups]

    if not user_id or not tenant_id:
        raise PermissionError("Token missing required claims")

    return AuthContext(
        user_id=user_id,
        tenant_id=tenant_id,
        roles=[str(x) for x in roles],
        groups=[str(x) for x in groups],
        raw_claims=claims,
    )
