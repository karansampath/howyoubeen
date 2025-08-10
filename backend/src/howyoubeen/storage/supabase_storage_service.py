"""
Supabase Storage Service Implementation

Production-ready storage using Supabase PostgreSQL database and file storage.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4
import logging

from .storage_service import StorageService
from .supabase_client import get_supabase_raw_client
from .repositories import UserRepository, OnboardingRepository, DocumentRepository, VisibilityRepository
from .supabase_storage import storage_manager

logger = logging.getLogger(__name__)


class SupabaseStorageService(StorageService):
    """Supabase storage implementation using PostgreSQL and Supabase Storage"""
    
    def __init__(self, use_service_key: bool = True):
        """
        Initialize Supabase storage service
        
        Args:
            use_service_key: Whether to use service role key for admin operations
        """
        self.use_service_key = use_service_key
        self._client = None
        
        # Initialize repositories
        self.user_repo = UserRepository(use_service_key)
        self.onboarding_repo = OnboardingRepository(use_service_key)
        self.document_repo = DocumentRepository(use_service_key)
        self.visibility_repo = VisibilityRepository(use_service_key)
        
        logger.info("Supabase storage service initialized")
    
    @property
    def client(self):
        """Get Supabase client"""
        if not self._client:
            self._client = get_supabase_raw_client(self.use_service_key)
        return self._client
    
    # User Management
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user"""
        return await self.user_repo.create_user(user_data)
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        return await self.user_repo.get_by_id(user_id)
    
    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        return await self.user_repo.get_by_username(username)
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        return await self.user_repo.get_by_email(email)
    
    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user data"""
        result = await self.user_repo.update_user(user_id, updates)
        return result is not None
    
    async def username_exists(self, username: str) -> bool:
        """Check if username exists"""
        return await self.user_repo.username_exists(username)
    
    async def email_exists(self, email: str) -> bool:
        """Check if email exists"""
        return await self.user_repo.email_exists(email)
    
    # Onboarding Session Management
    async def create_onboarding_session(self, user_id: Optional[str] = None) -> str:
        """Create a new onboarding session"""
        session = await self.onboarding_repo.create_session(user_id)
        return session["id"]
    
    async def update_onboarding_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Update onboarding session data"""
        return await self.onboarding_repo.update_session_data(session_id, data)
    
    async def get_onboarding_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get onboarding session data"""
        return await self.onboarding_repo.get_session_data(session_id)
    
    async def set_onboarding_step(self, session_id: str, step: str) -> bool:
        """Set onboarding step"""
        return await self.onboarding_repo.set_session_step(session_id, step)
    
    async def set_onboarding_user_id(self, session_id: str, user_id: str) -> bool:
        """Set user ID for session"""
        return await self.onboarding_repo.set_session_user_id(session_id, user_id)
    
    # File Management
    async def save_file(self, user_id: str, file_content: bytes, filename: str, 
                       description: str = "") -> Dict[str, Any]:
        """Save a file for a user using Supabase Storage"""
        try:
            # Upload to Supabase Storage
            storage_result = await storage_manager.upload_file(
                user_id=user_id,
                file_content=file_content,
                filename=filename
            )
            
            if not storage_result:
                raise Exception("Failed to upload file to Supabase Storage")
            
            return {
                "file_path": storage_result["file_path"],
                "original_filename": storage_result["original_filename"],
                "file_size": storage_result["file_size"],
                "content_type": storage_result["content_type"],
                "description": description,
                "public_url": storage_result.get("public_url")
            }
            
        except Exception as e:
            logger.error(f"Error saving file to Supabase Storage: {e}")
            raise
    
    async def get_file_url(self, file_path: str, expires_in: int = 3600) -> Optional[str]:
        """Get signed URL for accessing a file"""
        return await storage_manager.create_signed_url(file_path, expires_in)
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete a file from Supabase Storage"""
        return await storage_manager.delete_file(file_path)
    
    # Document Metadata Management
    async def create_document(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create document metadata record"""
        return await self.document_repo.create_document(document_data)
    
    async def get_documents_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all documents for a user"""
        return await self.document_repo.get_documents_for_user(user_id)
    
    # Visibility Categories
    async def create_visibility_categories(self, user_id: str, 
                                          categories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create visibility categories for a user"""
        return await self.visibility_repo.create_categories_for_user(user_id, categories)
    
    async def get_visibility_categories(self, user_id: str) -> List[Dict[str, Any]]:
        """Get visibility categories for a user"""
        return await self.visibility_repo.get_categories_for_user(user_id)
    
    # User Content (Diary Entries & Life Facts)
    async def create_diary_entry(self, entry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a diary entry"""
        try:
            response = (self.client.table("diary_entries")
                       .insert(entry_data)
                       .execute())
            
            if response.data:
                return response.data[0]
            else:
                raise Exception("Failed to create diary entry")
                
        except Exception as e:
            logger.error(f"Error creating diary entry: {e}")
            raise
    
    async def create_life_fact(self, fact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a life fact"""
        try:
            response = (self.client.table("life_facts")
                       .insert(fact_data)
                       .execute())
            
            if response.data:
                return response.data[0]
            else:
                raise Exception("Failed to create life fact")
                
        except Exception as e:
            logger.error(f"Error creating life fact: {e}")
            raise
    
    async def create_info_source(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an info source record"""
        try:
            response = (self.client.table("info_sources")
                       .insert(source_data)
                       .execute())
            
            if response.data:
                return response.data[0]
            else:
                raise Exception("Failed to create info source")
                
        except Exception as e:
            logger.error(f"Error creating info source: {e}")
            raise
    
    # Health and Diagnostics
    async def health_check(self) -> Dict[str, Any]:
        """Check Supabase storage service health"""
        try:
            # Test database connection
            response = (self.client.table("users")
                       .select("count", count="exact")
                       .limit(0)
                       .execute())
            
            db_healthy = response.count is not None
            
            # Test storage connection
            storage_healthy = await storage_manager.ensure_bucket_exists()
            
            return {
                "status": "healthy" if (db_healthy and storage_healthy) else "degraded",
                "backend": "supabase",
                "database_connection": db_healthy,
                "storage_connection": storage_healthy,
                "user_count": response.count if db_healthy else None
            }
            
        except Exception as e:
            logger.error(f"Supabase health check failed: {e}")
            return {
                "status": "unhealthy",
                "backend": "supabase",
                "error": str(e)
            }
    
    async def get_storage_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get storage usage statistics"""
        try:
            if user_id:
                # Get user-specific stats
                documents = await self.get_documents_for_user(user_id)
                storage_usage = await storage_manager.get_storage_usage(user_id)
                
                return {
                    "user_id": user_id,
                    "documents_count": len(documents),
                    "storage_usage": storage_usage
                }
            else:
                # Get overall stats
                user_count_response = (self.client.table("users")
                                     .select("count", count="exact")
                                     .limit(0)
                                     .execute())
                
                document_count_response = (self.client.table("documents")
                                         .select("count", count="exact")  
                                         .limit(0)
                                         .execute())
                
                session_count_response = (self.client.table("onboarding_sessions")
                                        .select("count", count="exact")
                                        .limit(0)
                                        .execute())
                
                return {
                    "backend": "supabase",
                    "total_users": user_count_response.count or 0,
                    "total_documents": document_count_response.count or 0,
                    "total_sessions": session_count_response.count or 0
                }
                
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {
                "backend": "supabase",
                "error": str(e)
            }
    
    # Cleanup Operations
    async def cleanup_expired_sessions(self, hours_old: int = 24) -> int:
        """Clean up expired onboarding sessions"""
        try:
            # Delete sessions older than specified hours
            response = (self.client.table("onboarding_sessions")
                       .delete()
                       .lt("created_at", f"now() - interval '{hours_old} hours'")
                       .execute())
            
            count = len(response.data) if response.data else 0
            logger.info(f"Cleaned up {count} expired Supabase sessions")
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
            return 0
    
    # Additional Supabase-specific methods
    async def get_user_with_related_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user with related data using Supabase joins"""
        return await self.user_repo.get_user_with_related_data(user_id)
    
    async def mark_onboarding_complete(self, user_id: str) -> bool:
        """Mark user onboarding as completed"""
        return await self.user_repo.mark_onboarding_complete(user_id)
    
    async def create_default_visibility_categories(self, user_id: str) -> List[Dict[str, Any]]:
        """Create default visibility categories for a new user"""
        return await self.visibility_repo.create_default_categories(user_id)
    
    # Query Methods
    async def get_diary_entries_for_user(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get diary entries for a user"""
        try:
            response = (self.client.table("diary_entries")
                       .select("*")
                       .eq("user_id", user_id)
                       .order("created_at", desc=True)
                       .range(offset, offset + limit - 1)
                       .execute())
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error getting diary entries for user {user_id}: {e}")
            return []
    
    async def get_life_facts_for_user(self, user_id: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get life facts for a user"""
        try:
            query = (self.client.table("life_facts")
                    .select("*")
                    .eq("user_id", user_id))
            
            if category:
                query = query.eq("category", category)
            
            response = query.order("created_at", desc=True).execute()
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error getting life facts for user {user_id}: {e}")
            return []
    
    async def get_info_sources_for_user(self, user_id: str, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get info sources for a user"""
        try:
            query = (self.client.table("info_sources")
                    .select("*")
                    .eq("user_id", user_id))
            
            if platform:
                query = query.eq("platform", platform)
            
            response = query.order("created_at", desc=True).execute()
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error getting info sources for user {user_id}: {e}")
            return []
    
    async def search_user_content(self, user_id: str, query: str, content_types: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Search across user's content"""
        results = {}
        search_types = content_types or ["diary_entries", "life_facts", "documents"]
        
        try:
            # Search diary entries
            if "diary_entries" in search_types:
                response = (self.client.table("diary_entries")
                           .select("*")
                           .eq("user_id", user_id)
                           .or_(f"summary.ilike.%{query}%,content.ilike.%{query}%")
                           .order("created_at", desc=True)
                           .execute())
                results["diary_entries"] = response.data or []
            
            # Search life facts
            if "life_facts" in search_types:
                response = (self.client.table("life_facts")
                           .select("*")
                           .eq("user_id", user_id)
                           .or_(f"summary.ilike.%{query}%,description.ilike.%{query}%")
                           .order("created_at", desc=True)
                           .execute())
                results["life_facts"] = response.data or []
            
            # Search documents
            if "documents" in search_types:
                response = (self.client.table("documents")
                           .select("*")
                           .eq("user_id", user_id)
                           .or_(f"filename.ilike.%{query}%,description.ilike.%{query}%")
                           .order("created_at", desc=True)
                           .execute())
                results["documents"] = response.data or []
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching user content: {e}")
            return {content_type: [] for content_type in search_types}
    
    async def get_user_activity_summary(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get user activity summary"""
        try:
            cutoff_date = f"now() - interval '{days} days'"
            
            # Get recent counts
            diary_count_response = (self.client.table("diary_entries")
                                  .select("count", count="exact")
                                  .eq("user_id", user_id)
                                  .gt("created_at", cutoff_date)
                                  .execute())
            
            facts_count_response = (self.client.table("life_facts")
                                  .select("count", count="exact")
                                  .eq("user_id", user_id)
                                  .gt("created_at", cutoff_date)
                                  .execute())
            
            docs_count_response = (self.client.table("documents")
                                 .select("count", count="exact")
                                 .eq("user_id", user_id)
                                 .gt("created_at", cutoff_date)
                                 .execute())
            
            # Get recent items
            recent_entries = await self.get_diary_entries_for_user(user_id, limit=3)
            recent_facts = await self.get_life_facts_for_user(user_id)
            recent_docs = await self.get_documents_for_user(user_id)
            
            # Get total counts
            total_diary_response = (self.client.table("diary_entries")
                                  .select("count", count="exact")
                                  .eq("user_id", user_id)
                                  .execute())
            
            total_facts_response = (self.client.table("life_facts")
                                  .select("count", count="exact")
                                  .eq("user_id", user_id)
                                  .execute())
            
            total_docs_response = (self.client.table("documents")
                                 .select("count", count="exact")
                                 .eq("user_id", user_id)
                                 .execute())
            
            diary_recent = diary_count_response.count or 0
            facts_recent = facts_count_response.count or 0
            docs_recent = docs_count_response.count or 0
            
            return {
                "user_id": user_id,
                "days": days,
                "activity_counts": {
                    "diary_entries": diary_recent,
                    "life_facts": facts_recent,
                    "documents": docs_recent,
                    "total": diary_recent + facts_recent + docs_recent
                },
                "recent_items": {
                    "diary_entries": recent_entries[:3],
                    "life_facts": recent_facts[:3],
                    "documents": recent_docs[:3]
                },
                "total_counts": {
                    "diary_entries": total_diary_response.count or 0,
                    "life_facts": total_facts_response.count or 0,
                    "documents": total_docs_response.count or 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting user activity summary: {e}")
            return {
                "user_id": user_id,
                "days": days,
                "error": str(e),
                "activity_counts": {"diary_entries": 0, "life_facts": 0, "documents": 0, "total": 0},
                "recent_items": {"diary_entries": [], "life_facts": [], "documents": []},
                "total_counts": {"diary_entries": 0, "life_facts": 0, "documents": 0}
            }