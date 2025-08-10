"""
Onboarding repository for managing onboarding sessions
"""

from typing import Any, Dict, List, Optional
from uuid import UUID
import json
import logging

from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class OnboardingRepository(BaseRepository):
    """Repository for onboarding session operations"""
    
    @property
    def table_name(self) -> str:
        return "onboarding_sessions"
    
    async def create_session(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new onboarding session
        
        Args:
            user_id: Optional user ID if user already exists
            
        Returns:
            Created session data
        """
        session_data = {
            "user_id": user_id,
            "step": "start",
            "data": {}
        }
        
        return await self.create(session_data)
    
    async def update_session_data(self, session_id: str, data: Dict[str, Any]) -> bool:
        """
        Update session data (merge with existing data)
        
        Args:
            session_id: Session ID
            data: Data to merge into session
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current session
            session = await self.get_by_id(session_id)
            if not session:
                return False
            
            # Merge data with existing data
            current_data = session.get("data", {})
            if isinstance(current_data, str):
                current_data = json.loads(current_data) if current_data else {}
            
            current_data.update(data)
            
            # Update session
            result = await self.update(session_id, {"data": current_data})
            return result is not None
            
        except Exception as e:
            logger.error(f"Error updating session data for {session_id}: {e}")
            return False
    
    async def set_session_step(self, session_id: str, step: str) -> bool:
        """
        Update session step
        
        Args:
            session_id: Session ID
            step: New step value
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = await self.update(session_id, {"step": step})
            return result is not None
        except Exception as e:
            logger.error(f"Error setting session step for {session_id}: {e}")
            return False
    
    async def set_session_user_id(self, session_id: str, user_id: str) -> bool:
        """
        Set user ID for session
        
        Args:
            session_id: Session ID
            user_id: User ID to associate with session
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = await self.update(session_id, {"user_id": user_id})
            return result is not None
        except Exception as e:
            logger.error(f"Error setting user ID for session {session_id}: {e}")
            return False
    
    async def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data safely
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data dict or None if not found
        """
        session = await self.get_by_id(session_id)
        if not session:
            return None
        
        # Parse JSON data if it's a string
        data = session.get("data", {})
        if isinstance(data, str):
            try:
                data = json.loads(data) if data else {}
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON data in session {session_id}")
                data = {}
        
        return {
            "session_id": session["id"],
            "user_id": session.get("user_id"),
            "step": session.get("step"),
            "data": data,
            "created_at": session.get("created_at"),
            "updated_at": session.get("updated_at")
        }
    
    async def get_sessions_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all sessions for a user
        
        Args:
            user_id: User ID
            
        Returns:
            List of sessions for the user
        """
        return await self.find_by({"user_id": user_id})
    
    async def cleanup_old_sessions(self, days_old: int = 7) -> int:
        """
        Clean up old onboarding sessions
        
        Args:
            days_old: Remove sessions older than this many days
            
        Returns:
            Number of sessions cleaned up
        """
        try:
            # Delete sessions older than specified days
            response = (self.table()
                       .delete()
                       .lt("created_at", f"now() - interval '{days_old} days'")
                       .execute())
            
            count = len(response.data) if response.data else 0
            logger.info(f"Cleaned up {count} old onboarding sessions")
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up old sessions: {e}")
            return 0
    
    async def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session summary with progress information
        
        Args:
            session_id: Session ID
            
        Returns:
            Session summary with progress details
        """
        session = await self.get_session_data(session_id)
        if not session:
            return None
        
        data = session.get("data", {})
        
        return {
            "session_id": session_id,
            "step": session.get("step"),
            "progress": {
                "has_basic_info": "basic_info" in data,
                "data_sources_count": len(data.get("data_sources", [])),
                "documents_count": len(data.get("uploaded_documents", [])),
                "has_visibility_config": "visibility_categories" in data
            },
            "created_at": session.get("created_at"),
            "updated_at": session.get("updated_at")
        }
    
    async def is_session_expired(self, session_id: str, hours_limit: int = 24) -> bool:
        """
        Check if session is expired
        
        Args:
            session_id: Session ID
            hours_limit: Session expiry time in hours
            
        Returns:
            True if session is expired, False otherwise
        """
        try:
            session = await self.get_by_id(session_id)
            if not session:
                return True
            
            # Check if session is older than limit
            response = (self.table()
                       .select("id")
                       .eq("id", session_id)
                       .lt("updated_at", f"now() - interval '{hours_limit} hours'")
                       .execute())
            
            return len(response.data) > 0
            
        except Exception as e:
            logger.error(f"Error checking session expiry: {e}")
            return True