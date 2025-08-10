"""
Document repository for managing file metadata and storage
"""

from typing import Any, Dict, List, Optional
import logging

from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class DocumentRepository(BaseRepository):
    """Repository for document operations"""
    
    @property
    def table_name(self) -> str:
        return "documents"
    
    async def create_document(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a document record
        
        Args:
            document_data: Document data including user_id, file_path, content_type, etc.
            
        Returns:
            Created document data
        """
        return await self.create(document_data)
    
    async def get_documents_for_user(self, user_id: str, content_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all documents for a user, optionally filtered by content type
        
        Args:
            user_id: User ID
            content_type: Optional content type filter
            
        Returns:
            List of user's documents
        """
        filters = {"user_id": user_id}
        if content_type:
            filters["content_type"] = content_type
        
        try:
            response = (self.table()
                       .select("*")
                       .eq("user_id", user_id))
            
            if content_type:
                response = response.eq("content_type", content_type)
            
            response = response.order("created_at", desc=True).execute()
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error getting documents for user {user_id}: {e}")
            raise
    
    async def get_document_by_path(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get document by file path
        
        Args:
            file_path: File path to search for
            
        Returns:
            Document data or None if not found
        """
        return await self.find_one_by({"file_path": file_path})
    
    async def update_document(self, document_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update document metadata
        
        Args:
            document_id: Document ID
            updates: Data to update
            
        Returns:
            Updated document data
        """
        return await self.update(document_id, updates)
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete document record
        
        Args:
            document_id: Document ID
            
        Returns:
            True if deleted successfully
        """
        return await self.delete(document_id)
    
    async def get_documents_by_type(self, user_id: str, content_types: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get documents grouped by content type
        
        Args:
            user_id: User ID
            content_types: List of content types to retrieve
            
        Returns:
            Dictionary with content types as keys and document lists as values
        """
        result = {}
        
        for content_type in content_types:
            documents = await self.get_documents_for_user(user_id, content_type)
            result[content_type] = documents
        
        return result
    
    async def count_documents_by_type(self, user_id: str) -> Dict[str, int]:
        """
        Count documents by content type for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with content types and their counts
        """
        try:
            # Get document counts grouped by content type
            response = (self.client.table("documents")
                       .select("content_type", count="exact")
                       .eq("user_id", user_id)
                       .execute())
            
            # Group by content type manually since Supabase doesn't support GROUP BY in select
            documents = response.data or []
            counts = {}
            
            for doc in documents:
                content_type = doc.get("content_type", "unknown")
                counts[content_type] = counts.get(content_type, 0) + 1
            
            return counts
            
        except Exception as e:
            logger.error(f"Error counting documents by type for user {user_id}: {e}")
            return {}
    
    async def get_recent_documents(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most recently uploaded documents for a user
        
        Args:
            user_id: User ID
            limit: Number of documents to return
            
        Returns:
            List of recent documents
        """
        try:
            response = (self.table()
                       .select("*")
                       .eq("user_id", user_id)
                       .order("created_at", desc=True)
                       .limit(limit)
                       .execute())
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error getting recent documents for user {user_id}: {e}")
            raise
    
    async def search_documents(self, user_id: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search documents by description or filename
        
        Args:
            user_id: User ID
            query: Search query
            limit: Number of results to return
            
        Returns:
            List of matching documents
        """
        try:
            response = (self.table()
                       .select("*")
                       .eq("user_id", user_id)
                       .ilike("description", f"%{query}%")
                       .order("created_at", desc=True)
                       .limit(limit)
                       .execute())
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error searching documents for user {user_id}: {e}")
            raise
    
    async def get_document_storage_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get storage statistics for a user's documents
        
        Args:
            user_id: User ID
            
        Returns:
            Storage statistics
        """
        try:
            documents = await self.get_documents_for_user(user_id)
            
            total_files = len(documents)
            total_size = sum(doc.get("file_size", 0) for doc in documents if doc.get("file_size"))
            
            # Count by content type
            type_counts = {}
            type_sizes = {}
            
            for doc in documents:
                content_type = doc.get("content_type", "unknown")
                file_size = doc.get("file_size", 0)
                
                type_counts[content_type] = type_counts.get(content_type, 0) + 1
                type_sizes[content_type] = type_sizes.get(content_type, 0) + file_size
            
            return {
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": total_size / (1024 * 1024) if total_size > 0 else 0,
                "by_type": {
                    "counts": type_counts,
                    "sizes": type_sizes
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting storage stats for user {user_id}: {e}")
            return {
                "total_files": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0,
                "by_type": {"counts": {}, "sizes": {}}
            }
    
    async def cleanup_orphaned_documents(self) -> int:
        """
        Clean up documents that are not associated with any user
        
        Returns:
            Number of documents cleaned up
        """
        try:
            # Find documents with non-existent user_id
            response = (self.client.table("documents")
                       .delete()
                       .not_.in_("user_id", 
                                self.client.table("users").select("id"))
                       .execute())
            
            count = len(response.data) if response.data else 0
            logger.info(f"Cleaned up {count} orphaned documents")
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up orphaned documents: {e}")
            return 0