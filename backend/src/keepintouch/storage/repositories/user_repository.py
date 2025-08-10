"""
User repository for managing user data
"""

from typing import Any, Dict, List, Optional
from uuid import UUID
import logging

from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository):
    """Repository for user operations"""
    
    @property
    def table_name(self) -> str:
        return "users"
    
    async def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get user by username
        
        Args:
            username: Username to search for
            
        Returns:
            User data or None if not found
        """
        try:
            response = self.table().select("*").eq("username", username).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error getting user by username '{username}': {e}")
            raise
    
    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email
        
        Args:
            email: Email to search for
            
        Returns:
            User data or None if not found
        """
        try:
            response = self.table().select("*").eq("email", email).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error getting user by email '{email}': {e}")
            raise
    
    async def username_exists(self, username: str) -> bool:
        """
        Check if username is already taken
        
        Args:
            username: Username to check
            
        Returns:
            True if username exists, False otherwise
        """
        user = await self.get_by_username(username)
        return user is not None
    
    async def email_exists(self, email: str) -> bool:
        """
        Check if email is already registered
        
        Args:
            email: Email to check
            
        Returns:
            True if email exists, False otherwise
        """
        user = await self.get_by_email(email)
        return user is not None
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user with validation
        
        Args:
            user_data: User data including username, email, full_name, etc.
            
        Returns:
            Created user data
            
        Raises:
            ValueError: If username or email already exists
        """
        # Check for existing username
        if await self.username_exists(user_data.get("username", "")):
            raise ValueError(f"Username '{user_data['username']}' already exists")
        
        # Check for existing email
        if await self.email_exists(user_data.get("email", "")):
            raise ValueError(f"Email '{user_data['email']}' already exists")
        
        # Create user
        return await self.create(user_data)
    
    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update user with validation
        
        Args:
            user_id: User ID
            updates: Data to update
            
        Returns:
            Updated user data or None if not found
            
        Raises:
            ValueError: If username or email conflicts with existing users
        """
        # If updating username, check it's not taken by another user
        if "username" in updates:
            existing = await self.get_by_username(updates["username"])
            if existing and existing["id"] != user_id:
                raise ValueError(f"Username '{updates['username']}' already exists")
        
        # If updating email, check it's not taken by another user
        if "email" in updates:
            existing = await self.get_by_email(updates["email"])
            if existing and existing["id"] != user_id:
                raise ValueError(f"Email '{updates['email']}' already exists")
        
        return await self.update(user_id, updates)
    
    async def get_user_with_related_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user with related data (visibility categories, sources, etc.)
        
        Args:
            user_id: User ID
            
        Returns:
            User data with related information
        """
        try:
            # Get user with related data using Supabase joins
            response = (self.table()
                       .select("""
                           *,
                           visibility_categories(*),
                           info_sources(*),
                           diary_entries(*),
                           life_facts(*),
                           friends(*)
                       """)
                       .eq("id", user_id)
                       .execute())
            
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error getting user with related data: {e}")
            raise
    
    async def get_public_users(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get public users for discovery
        
        Args:
            limit: Number of users to return
            offset: Offset for pagination
            
        Returns:
            List of public users
        """
        try:
            response = (self.table()
                       .select("id, username, full_name, bio, profile_image_url")
                       .eq("is_public", True)
                       .eq("onboarding_completed", True)
                       .order("created_at", desc=True)
                       .range(offset, offset + limit - 1)
                       .execute())
            
            return response.data or []
        except Exception as e:
            logger.error(f"Error getting public users: {e}")
            raise
    
    async def search_users(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search users by name or username
        
        Args:
            query: Search query
            limit: Number of results to return
            
        Returns:
            List of matching users
        """
        try:
            response = (self.table()
                       .select("id, username, full_name, bio, profile_image_url")
                       .eq("is_public", True)
                       .eq("onboarding_completed", True)
                       .or_(f"username.ilike.%{query}%,full_name.ilike.%{query}%")
                       .limit(limit)
                       .execute())
            
            return response.data or []
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            raise
    
    async def mark_onboarding_complete(self, user_id: str) -> bool:
        """
        Mark user onboarding as completed
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = await self.update(user_id, {
                "onboarding_completed": True,
                "knowledge_last_updated": "now()"
            })
            return result is not None
        except Exception as e:
            logger.error(f"Error marking onboarding complete for user {user_id}: {e}")
            return False