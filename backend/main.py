"""
SellerBoost AI — FastAPI Application Entry Point
"""
import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager

# Ensure backend directory is in sys.path regardless of execution working directory
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.routes import router
from app.database.db import init_db

# Logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("sellerboost")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: initialize DB on startup."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"AI Provider: {settings.AI_PROVIDER}")
    if settings.AI_PROVIDER == "backboard":
        if settings.BACKBOARD_API_KEY:
            logger.info(f"Backboard configured: model={settings.BACKBOARD_DEFAULT_MODEL}")
        else:
            logger.warning("No BACKBOARD_API_KEY set — live AI inference requires BACKBOARD_API_KEY. Configure BACKBOARD_API_KEY in environment variables.")
    elif settings.AI_PROVIDER == "mock":
        logger.info("AI Provider explicitly set to mock — running in demo mode with synthetic responses")
    
    await init_db()
    logger.info(f"Database initialized at {settings.DATABASE_PATH}")
    
    yield
    
    logger.info("Shutting down SellerBoost AI")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Open-Weight AI E-Commerce Listing Assistant for Small Sellers",
    lifespan=lifespan,
)

# CORS — allows configured origins and any Vercel domain (*.vercel.app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX if settings.CORS_ORIGIN_REGEX else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
app.include_router(router)


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Top-level health check endpoint for Render and uptime monitoring."""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", settings.PORT))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=settings.DEBUG)
