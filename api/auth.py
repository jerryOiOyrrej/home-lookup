"""Authentication via Pocket ID (OIDC) and API key."""

import os
from typing import Optional

import httpx
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Environment variables (configured in Coolify)
OIDC_ISSUER = os.getenv("OIDC_ISSUER", "https://pocketid.nieuviarts.fr")
OIDC_CLIENT_ID = os.getenv("OIDC_CLIENT_ID", "")
OIDC_CLIENT_SECRET = os.getenv("OIDC_CLIENT_SECRET", "")
API_KEY = os.getenv("API_KEY", "")
APP_URL = os.getenv("APP_URL", "http://localhost:8000")

security = HTTPBearer(auto_error=False)

# Cache for OIDC discovery
_oidc_config: Optional[dict] = None


async def get_oidc_config() -> dict:
    """Fetch OIDC discovery document."""
    global _oidc_config
    if _oidc_config:
        return _oidc_config
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{OIDC_ISSUER}/.well-known/openid-configuration")
        resp.raise_for_status()
        _oidc_config = resp.json()
        return _oidc_config


async def verify_api_key(request: Request) -> bool:
    """Check X-API-Key header."""
    api_key = request.headers.get("X-API-Key", "")
    if API_KEY and api_key == API_KEY:
        return True
    return False


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """
    Authenticate via:
    1. API key (X-API-Key header) — for JoC/programmatic access
    2. OIDC session cookie — for browser access
    3. Bearer token — for API clients
    """
    # 1. API Key
    if await verify_api_key(request):
        return {"sub": "api", "name": "JoC", "method": "api_key"}

    # 2. Session cookie (set after OIDC login)
    session_user = request.session.get("user") if hasattr(request, "session") else None
    if session_user:
        return session_user

    # 3. Bearer token — validate with OIDC userinfo
    if credentials:
        try:
            config = await get_oidc_config()
            userinfo_url = config.get("userinfo_endpoint")
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    userinfo_url,
                    headers={"Authorization": f"Bearer {credentials.credentials}"},
                )
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Non authentifié",
    )


async def optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    """Same as get_current_user but returns None instead of 401."""
    try:
        return await get_current_user(request, credentials)
    except HTTPException:
        return None
