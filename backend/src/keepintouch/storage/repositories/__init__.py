"""
Repository pattern implementation for KeepInTouch data access

This module provides repository classes that abstract database operations
and provide a clean interface for the application layer.
"""

from .user_repository import UserRepository
from .onboarding_repository import OnboardingRepository
from .document_repository import DocumentRepository
from .visibility_repository import VisibilityRepository

__all__ = [
    "UserRepository",
    "OnboardingRepository", 
    "DocumentRepository",
    "VisibilityRepository"
]