"""
FastAPI application factory and configuration
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import logging
from dotenv import load_dotenv

from .routes import onboarding
from .routes import supabase_onboarding

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    app = FastAPI(
        title="KeepInTouch API", 
        description="AI-Powered Social Connection Platform with Supabase",
        version="0.2.0",
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
    
    # Check if Supabase is configured
    use_supabase = bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_ANON_KEY"))
    
    if use_supabase:
        logger.info("Using Supabase for data persistence")
        # Include Supabase-integrated API routers
        app.include_router(
            supabase_onboarding.router,
            prefix="/api/onboarding",
            tags=["onboarding-supabase"]
        )
    else:
        logger.info("Using in-memory storage (development mode)")
        # Include memory-based API routers  
        app.include_router(
            onboarding.router,
            prefix="/api/onboarding",
            tags=["onboarding-memory"]
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
        return {
            "status": "healthy", 
            "service": "keepintouch-api",
            "version": "0.2.0",
            "storage_backend": "supabase" if use_supabase else "memory"
        }
    
    return app