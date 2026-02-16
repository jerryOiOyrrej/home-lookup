"""OIDC login/callback routes for Pocket ID."""

import os
import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from api.auth import get_oidc_config, OIDC_CLIENT_ID, OIDC_CLIENT_SECRET, APP_URL

router = APIRouter()


@router.get("/auth/login")
async def login(request: Request):
    """Redirect to Pocket ID for authentication."""
    config = await get_oidc_config()
    state = secrets.token_urlsafe(32)
    request.session["oauth_state"] = state

    params = {
        "response_type": "code",
        "client_id": OIDC_CLIENT_ID,
        "redirect_uri": f"{APP_URL}/auth/callback",
        "scope": "openid profile email",
        "state": state,
    }
    return RedirectResponse(f"{config['authorization_endpoint']}?{urlencode(params)}")


@router.get("/auth/callback")
async def callback(request: Request, code: str, state: str):
    """Handle OIDC callback from Pocket ID."""
    saved_state = request.session.get("oauth_state")
    if not saved_state or saved_state != state:
        return RedirectResponse("/?error=invalid_state")

    config = await get_oidc_config()

    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            config["token_endpoint"],
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": f"{APP_URL}/auth/callback",
                "client_id": OIDC_CLIENT_ID,
                "client_secret": OIDC_CLIENT_SECRET,
            },
        )
        if token_resp.status_code != 200:
            return RedirectResponse("/?error=token_exchange_failed")

        tokens = token_resp.json()
        access_token = tokens.get("access_token")

        # Get user info
        userinfo_resp = await client.get(
            config["userinfo_endpoint"],
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if userinfo_resp.status_code != 200:
            return RedirectResponse("/?error=userinfo_failed")

        user = userinfo_resp.json()

    # Store user in session
    request.session["user"] = {
        "sub": user.get("sub"),
        "name": user.get("name", user.get("preferred_username", "Unknown")),
        "email": user.get("email"),
        "method": "oidc",
    }

    return RedirectResponse("/")


@router.get("/auth/logout")
async def logout(request: Request):
    """Clear session."""
    request.session.clear()
    return RedirectResponse("/")


@router.get("/auth/me")
async def me(request: Request):
    """Return current user info."""
    user = request.session.get("user")
    if user:
        return user
    return {"authenticated": False}
