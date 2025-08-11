"""
Storage Factory

Factory function to create appropriate storage service based on environment configuration.
Automatically detects and selects between Local and Supabase storage backends.
"""

import os
import logging
from typing import Optional

from .storage_service import StorageService
from .local_storage_service import LocalStorageService
from .supabase_storage_service import SupabaseStorageService

logger = logging.getLogger(__name__)


def get_storage_service(force_backend: Optional[str] = None) -> StorageService:
    """
    Factory function to get appropriate storage service
    
    Args:
        force_backend: Optional backend override ('local' or 'supabase')
        
    Returns:
        StorageService instance configured for the environment
    """
    
    # Check for environment variable override first
    env_backend = os.getenv("STORAGE_BACKEND", "").lower()
    if env_backend in ["local", "supabase"]:
        force_backend = env_backend
        logger.info(f"Using storage backend from environment: {env_backend}")
    
    # Check for forced backend
    if force_backend:
        if force_backend.lower() == "local":
            logger.info("Using forced local storage backend")
            return LocalStorageService()
        elif force_backend.lower() == "supabase":
            logger.info("Using forced Supabase storage backend")
            return SupabaseStorageService(use_service_key=True)
        else:
            logger.warning(f"Unknown forced backend '{force_backend}', using auto-detection")
    
    # Auto-detect backend based on environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    # Check if Supabase is configured
    if supabase_url and (supabase_anon_key or supabase_service_key):
        logger.info("Supabase configuration detected, using Supabase storage")
        return SupabaseStorageService(use_service_key=True)
    
    # Fall back to local storage
    logger.info("No Supabase configuration found, using local storage")
    return LocalStorageService(
        storage_root=os.getenv("LOCAL_STORAGE_ROOT")
    )


def get_development_storage() -> StorageService:
    """
    Get storage service configured for development
    
    Returns:
        Local storage service with backup enabled
    """
    logger.info("Creating development storage service")
    return LocalStorageService(
        storage_root=os.getenv("LOCAL_STORAGE_ROOT", "./storage")
    )


def get_production_storage() -> StorageService:
    """
    Get storage service configured for production
    
    Returns:
        Supabase storage service
        
    Raises:
        RuntimeError: If Supabase is not properly configured
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_service_key:
        raise RuntimeError(
            "Production storage requires SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables"
        )
    
    logger.info("Creating production storage service")
    return SupabaseStorageService(use_service_key=True)


def get_test_storage() -> StorageService:
    """
    Get storage service configured for testing
    
    Returns:
        Local storage service with no persistence
    """
    logger.info("Creating test storage service")
    return LocalStorageService()  # No backup file for testing


async def health_check_storage(storage: StorageService) -> dict:
    """
    Perform health check on storage service
    
    Args:
        storage: Storage service to check
        
    Returns:
        Health check results
    """
    try:
        health_result = await storage.health_check()
        logger.info(f"Storage health check: {health_result['status']}")
        return health_result
    except Exception as e:
        logger.error(f"Storage health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


def create_storage_from_config(config: dict) -> StorageService:
    """
    Create storage service from configuration dictionary
    
    Args:
        config: Configuration dictionary with storage settings
        
    Returns:
        Configured storage service
        
    Example:
        config = {
            "backend": "local",
            "local": {
                "storage_root": "./storage"
            }
        }
        
        config = {
            "backend": "supabase",
            "supabase": {
                "url": "https://...",
                "service_key": "eyJ..."
            }
        }
    """
    backend = config.get("backend", "auto")
    
    if backend == "local":
        local_config = config.get("local", {})
        logger.info("Creating local storage from config")
        return LocalStorageService(
            storage_root=local_config.get("storage_root")
        )
    
    elif backend == "supabase":
        supabase_config = config.get("supabase", {})
        
        # Set environment variables if provided in config
        if supabase_config.get("url"):
            os.environ["SUPABASE_URL"] = supabase_config["url"]
        if supabase_config.get("service_key"):
            os.environ["SUPABASE_SERVICE_KEY"] = supabase_config["service_key"]
        if supabase_config.get("anon_key"):
            os.environ["SUPABASE_ANON_KEY"] = supabase_config["anon_key"]
        
        logger.info("Creating Supabase storage from config")
        return SupabaseStorageService(use_service_key=True)
    
    else:
        # Auto-detect or unknown backend
        logger.info("Auto-detecting storage backend from config")
        return get_storage_service()