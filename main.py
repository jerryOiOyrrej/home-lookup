"""Marseille Apartment Search — Main application."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from api.database import init_db
from api.routes import router as api_router
from api.oidc import router as oidc_router
from api.middleware import AuthMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    init_db()
    yield


app = FastAPI(
    title="🏠 Home Lookup",
    description="Recherche d'appartement à Marseille — Jerry & JoC",
    version="0.1.0",
    lifespan=lifespan,
)

# Middleware order: add_middleware stacks in reverse, so AuthMiddleware
# must be added FIRST (runs second), then SessionMiddleware (runs first)
app.add_middleware(AuthMiddleware)

SESSION_SECRET = os.getenv("SESSION_SECRET", "change-me-in-production-please")
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)

# Routes
app.include_router(oidc_router)
app.include_router(api_router)

# Templates
templates = Jinja2Templates(directory="frontend/templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Dashboard principal."""
    user = request.session.get("user")
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": user,
    })


@app.get("/health")
async def health():
    """Health check for Coolify."""
    return {"status": "ok", "app": "home-lookup"}
