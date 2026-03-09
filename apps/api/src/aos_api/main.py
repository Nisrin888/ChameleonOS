"""
Adaptive-OS API — FastAPI Application
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from aos_api.config import settings
from aos_api.db.session import init_db, close_db
from aos_api.redis_client import init_redis, close_redis
from aos_api.routes import handshake, track, dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    print("[AOS] Starting Adaptive-OS API...")
    await init_db()
    await init_redis()
    print("[AOS] API ready.")
    yield
    print("[AOS] Shutting down...")
    await close_db()
    await close_redis()


app = FastAPI(
    title="Adaptive-OS API",
    description="Vibe-matched content routing for DTC brands",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — permissive in dev, per-tenant validation in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.environment == "development" else [],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

# Routes
app.include_router(handshake.router, prefix="/v1", tags=["handshake"])
app.include_router(track.router, prefix="/v1", tags=["tracking"])
app.include_router(dashboard.router, prefix="/v1/dashboard", tags=["dashboard"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "aos-api"}
