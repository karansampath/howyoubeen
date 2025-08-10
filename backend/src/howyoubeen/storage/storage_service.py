"""
Abstract Storage Service Interface

This module defines the abstract interface for storage operations,
allowing pluggable backends (Local, Supabase, etc.) with consistent API.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class StorageService(ABC):
    """Abstract base class for storage operations"""
    
    # User Management
    @abstractmethod
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user
        
        Args:
            user_data: User data including username, email, full_name, etc.
            
        Returns:
            Created user data with ID
            
        Raises:
            ValueError: If username or email already exists
        """
        pass
    
    @abstractmethod
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user by ID
        
        Args:
            user_id: User ID
            
        Returns:
            User data or None if not found
        """
        pass
    
    @abstractmethod
    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get user by username
        
        Args:
            username: Username to search for
            
        Returns:
            User data or None if not found
        """
        pass
    
    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email
        
        Args:
            email: Email to search for
            
        Returns:
            User data or None if not found
        """
        pass
    
    @abstractmethod
    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update user data
        
        Args:
            user_id: User ID
            updates: Data to update
            
        Returns:
            True if updated successfully, False if user not found
        """
        pass
    
    @abstractmethod
    async def username_exists(self, username: str) -> bool:
        """
        Check if username is already taken
        
        Args:
            username: Username to check
            
        Returns:
            True if username exists, False otherwise
        """
        pass
    
    @abstractmethod
    async def email_exists(self, email: str) -> bool:
        """
        Check if email is already registered
        
        Args:
            email: Email to check
            
        Returns:
            True if email exists, False otherwise
        """
        pass
    
    # Onboarding Session Management
    @abstractmethod
    async def create_onboarding_session(self, user_id: Optional[str] = None) -> str:
        """
        Create a new onboarding session
        
        Args:
            user_id: Optional user ID if user already exists
            
        Returns:
            Session ID
        """
        pass
    
    @abstractmethod
    async def update_onboarding_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """
        Update onboarding session data
        
        Args:
            session_id: Session ID
            data: Data to update/merge
            
        Returns:
            True if updated successfully, False if session not found
        """
        pass
    
    @abstractmethod
    async def get_onboarding_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get onboarding session data
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data or None if not found
        """
        pass
    
    @abstractmethod
    async def set_onboarding_step(self, session_id: str, step: str) -> bool:
        """
        Update onboarding session step
        
        Args:
            session_id: Session ID
            step: New step value
            
        Returns:
            True if updated successfully, False if session not found
        """
        pass
    
    @abstractmethod
    async def set_onboarding_user_id(self, session_id: str, user_id: str) -> bool:
        """
        Associate user ID with onboarding session
        
        Args:
            session_id: Session ID
            user_id: User ID to associate
            
        Returns:
            True if updated successfully, False if session not found
        """
        pass
    
    # File Management
    @abstractmethod
    async def save_file(self, user_id: str, file_content: bytes, filename: str, 
                       description: str = "") -> Dict[str, Any]:
        """
        Save a file for a user
        
        Args:
            user_id: User ID
            file_content: File content as bytes
            filename: Original filename
            description: Optional description
            
        Returns:
            File metadata including file_path and other details
        """
        pass
    
    @abstractmethod
    async def get_file_url(self, file_path: str, expires_in: int = 3600) -> Optional[str]:
        """
        Get URL for accessing a file
        
        Args:
            file_path: Path to the file
            expires_in: URL expiration time in seconds
            
        Returns:
            URL for file access or None if file not found
        """
        pass
    
    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if deleted successfully, False otherwise
        """
        pass
    
    # Document Metadata Management
    @abstractmethod
    async def create_document(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create document metadata record
        
        Args:
            document_data: Document metadata including user_id, file_path, etc.
            
        Returns:
            Created document record
        """
        pass
    
    @abstractmethod
    async def get_documents_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all documents for a user
        
        Args:
            user_id: User ID
            
        Returns:
            List of document records
        """
        pass
    
    # Visibility Categories
    @abstractmethod
    async def create_visibility_categories(self, user_id: str, 
                                          categories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create visibility categories for a user
        
        Args:
            user_id: User ID
            categories: List of category definitions
            
        Returns:
            List of created category records
        """
        pass
    
    @abstractmethod
    async def get_visibility_categories(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get visibility categories for a user
        
        Args:
            user_id: User ID
            
        Returns:
            List of visibility categories
        """
        pass
    
    # User Content (Life Events & Life Facts)
    @abstractmethod
    async def create_life_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a life event
        
        Args:
            event_data: Event data including user_id, summary, start_date, end_date, visibility, etc.
            
        Returns:
            Created life event record
        """
        pass
    
    @abstractmethod
    async def create_life_fact(self, fact_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a life fact
        
        Args:
            fact_data: Fact data including user_id, summary, category, etc.
            
        Returns:
            Created life fact record
        """
        pass
    
    @abstractmethod
    async def create_info_source(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an info source record
        
        Args:
            source_data: Source data including user_id, platform, url, etc.
            
        Returns:
            Created info source record
        """
        pass
    
    # Health and Diagnostics
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check storage service health
        
        Returns:
            Health status information
        """
        pass
    
    @abstractmethod
    async def get_storage_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get storage usage statistics
        
        Args:
            user_id: Optional user ID to get user-specific stats
            
        Returns:
            Storage statistics
        """
        pass
    
    # Cleanup Operations
    @abstractmethod
    async def cleanup_expired_sessions(self, hours_old: int = 24) -> int:
        """
        Clean up expired onboarding sessions
        
        Args:
            hours_old: Remove sessions older than this many hours
            
        Returns:
            Number of sessions cleaned up
        """
        pass
    
    # Query Methods
    @abstractmethod
    async def get_life_events_for_user(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get life events for a user
        
        Args:
            user_id: User ID
            limit: Maximum number of events to return
            offset: Number of events to skip
            
        Returns:
            List of life events
        """
        pass
    
    @abstractmethod
    async def get_life_facts_for_user(self, user_id: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get life facts for a user
        
        Args:
            user_id: User ID
            category: Optional category filter
            
        Returns:
            List of life facts
        """
        pass
    
    @abstractmethod
    async def get_info_sources_for_user(self, user_id: str, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get info sources for a user
        
        Args:
            user_id: User ID
            platform: Optional platform filter
            
        Returns:
            List of info sources
        """
        pass
    
    @abstractmethod
    async def search_user_content(self, user_id: str, query: str, content_types: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search across user's content
        
        Args:
            user_id: User ID
            query: Search query
            content_types: Optional list of content types to search ['life_events', 'life_facts', 'documents']
            
        Returns:
            Dictionary with content types as keys and matching items as values
        """
        pass
    
    @abstractmethod
    async def get_user_activity_summary(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get user activity summary
        
        Args:
            user_id: User ID
            days: Number of days to summarize
            
        Returns:
            Activity summary with counts and recent items
        """
        pass
    
    @abstractmethod
    async def get_life_events_by_date_range(
        self, 
        user_id: str, 
        start_date: datetime, 
        end_date: datetime,
        visibility_levels: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get life events for a user within a specific date range
        
        Args:
            user_id: User ID
            start_date: Start date for filtering events
            end_date: End date for filtering events  
            visibility_levels: Optional list of visibility level types to filter by
            
        Returns:
            List of life events within the date range and visibility filters
        """
        pass