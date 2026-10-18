"""
SellerBoost AI — FastAPI Application Entry Point
"""
import logging
from contextlib import asynccontextmanager

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
    if settings.BACKBOARD_API_KEY:
        logger.info(f"Backboard configured: model={settings.BACKBOARD_DEFAULT_MODEL}")
    else:
        logger.warning("No BACKBOARD_API_KEY set — running in demo mode with synthetic responses")
    
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

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
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
