"""
FastAPI main application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings


# Create FastAPI application
app = FastAPI(
    title="Chess 39 API",
    description="Backend API for Chess 39 - Random armies, infinite strategy",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """API root endpoint."""
    return {
        "message": "Chess 39 API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Include API routers
from app.api.routes import auth, games

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(games.router, prefix="/api/games", tags=["games"])
