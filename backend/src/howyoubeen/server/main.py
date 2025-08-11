"""
FastAPI application factory and configuration
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import logging
from dotenv import load_dotenv

from .routes import onboarding, newsletter, user, chat, friends, auth, content

# Load environment variables
load_dotenv()  # Load .env first
load_dotenv(".env.local", override=True)  # Then load .env.local with override

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    app = FastAPI(
        title="HowYouBeen API", 
        description="AI companion that keeps your friends updated on your life",
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
    
    # Add authentication routes
    app.include_router(
        auth.router,
        prefix="/api/auth",
        tags=["authentication"]
    )
    
    # Use unified onboarding routes with automatic storage backend detection
    logger.info("Using unified onboarding service with automatic storage backend detection")
    app.include_router(
        onboarding.router,
        prefix="/api/onboarding",
        tags=["onboarding"]
    )
    
    # Add newsletter routes
    app.include_router(
        newsletter.router,
        prefix="/api/newsletter",
        tags=["newsletter"]
    )
    
    # Add user profile routes
    app.include_router(
        user.router,
        prefix="/api",
        tags=["users"]
    )
    
    # Add chat routes
    app.include_router(
        chat.router,
        prefix="/api",
        tags=["chat"]
    )
    
    # Add friends and timeline routes
    app.include_router(
        friends.router,
        prefix="/api",
        tags=["friends"]
    )
    
    # Add content routes for life events, life facts, and newsletter configurations
    app.include_router(
        content.router,
        prefix="/api/content",
        tags=["content"]
    )
    
    # Serve static files (frontend)
    static_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "static")
    if os.path.exists(static_dir):
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        # Detect backend based on environment variables
        use_supabase = bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_ANON_KEY"))
        
        return {
            "status": "healthy", 
            "service": "howyoubeen-api",
            "version": "0.2.0",
            "storage_backend": "supabase" if use_supabase else "local"
        }
    
    return app
