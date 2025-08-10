"""
FastAPI application factory and configuration
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from .routes import onboarding


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    app = FastAPI(
        title="KeepInTouch API",
        description="AI-Powered Social Connection Platform",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc"
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify allowed origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routers
    app.include_router(
        onboarding.router,
        prefix="/api/onboarding",
        tags=["onboarding"]
    )
    
    # TODO: Add chat, profile, and friends routes when implemented
    # For now, frontend will use dummy data
    
    # Serve static files (frontend)
    static_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "static")
    if os.path.exists(static_dir):
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy", "service": "keepintouch-api"}
    
    return app