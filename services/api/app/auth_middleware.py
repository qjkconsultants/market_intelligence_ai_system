from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

from .settings import settings
from .auth import authenticate_bearer_token, AuthContext

log = structlog.get_logger()

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Dev mode: allow running locally without an IdP.
        if not settings.auth_enabled:
            request.state.auth = AuthContext(
                user_id="local-dev",
                tenant_id=request.headers.get("x-tenant-id", "local-tenant"),
                roles=["ADMIN"],
                groups=["ADMIN"],
                raw_claims={},
            )
            return await call_next(request)

        try:
            authz = request.headers.get("authorization", "")
            ctx = await authenticate_bearer_token(authz)
            request.state.auth = ctx
        except Exception as e:
            # Consistent 401/403 for auth failures
            log.info("auth_failed", path=str(request.url.path), error=str(e))
            from starlette.responses import JSONResponse
            return JSONResponse(status_code=401, content={"error": "unauthorized"})

        return await call_next(request)
