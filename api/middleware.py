"""Authentication middleware — protect all routes except health and auth."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse, JSONResponse

from api.auth import API_KEY


class AuthMiddleware(BaseHTTPMiddleware):
    """Require authentication on all routes except /health, /auth/*, /docs, /openapi.json."""

    OPEN_PATHS = ("/health", "/auth/", "/docs", "/openapi.json", "/redoc")

    async def dispatch(self, request, call_next):
        path = request.url.path

        # Allow open paths
        if any(path.startswith(p) for p in self.OPEN_PATHS):
            return await call_next(request)

        # Allow API key access
        api_key = request.headers.get("X-API-Key", "")
        if API_KEY and api_key == API_KEY:
            return await call_next(request)

        # Check session (OIDC login)
        user = request.session.get("user") if hasattr(request, "session") else None
        if user:
            return await call_next(request)

        # Not authenticated
        if path.startswith("/api/"):
            return JSONResponse(
                status_code=401,
                content={"detail": "Non authentifié"},
            )

        # Redirect browser to login
        return RedirectResponse("/auth/login")
