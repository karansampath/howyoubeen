"""
Supabase Storage integration for file management

This module handles file uploads, downloads, and management using Supabase Storage.
"""

import os
import mimetypes
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4
import logging

from .supabase_client import get_supabase_raw_client

logger = logging.getLogger(__name__)


class SupabaseStorageManager:
    """Manager for Supabase Storage operations"""
    
    def __init__(self, bucket_name: str = "user-documents"):
        """
        Initialize storage manager
        
        Args:
            bucket_name: Name of the Supabase storage bucket
        """
        self.bucket_name = bucket_name
        self._client = None
    
    @property
    def client(self):
        """Get Supabase client"""
        if not self._client:
            self._client = get_supabase_raw_client(use_service_key=True)
        return self._client
    
    @property
    def storage(self):
        """Get storage client"""
        return self.client.storage
    
    async def ensure_bucket_exists(self) -> bool:
        """
        Ensure the storage bucket exists, create if it doesn't
        
        Returns:
            True if bucket exists or was created successfully
        """
        try:
            # Try to get bucket info
            response = self.storage.get_bucket(self.bucket_name)
            if response:
                return True
            
            # Bucket doesn't exist, create it
            logger.info(f"Creating bucket: {self.bucket_name}")
            self.storage.create_bucket(self.bucket_name, {
                "public": False,  # Private bucket
                "file_size_limit": 50 * 1024 * 1024,  # 50MB limit
                "allowed_mime_types": [
                    "image/*",
                    "video/*", 
                    "application/pdf",
                    "application/msword",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "text/plain",
                    "audio/*"
                ]
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error ensuring bucket exists: {e}")
            return False
    
    def generate_file_path(self, user_id: str, filename: str) -> str:
        """
        Generate a unique file path for storage
        
        Args:
            user_id: User ID for organizing files
            filename: Original filename
            
        Returns:
            Unique file path for storage
        """
        # Extract file extension
        _, ext = os.path.splitext(filename)
        
        # Generate unique filename
        unique_id = str(uuid4())
        unique_filename = f"{unique_id}{ext}"
        
        # Create user-specific path
        return f"{user_id}/{unique_filename}"
    
    async def upload_file(self, user_id: str, file_content: bytes, filename: str, 
                         content_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Upload a file to Supabase Storage
        
        Args:
            user_id: User ID for organizing files
            file_content: File content as bytes
            filename: Original filename
            content_type: MIME type (auto-detected if not provided)
            
        Returns:
            Upload result with file path and metadata, or None if failed
        """
        try:
            # Ensure bucket exists
            if not await self.ensure_bucket_exists():
                logger.error("Failed to ensure bucket exists")
                return None
            
            # Generate unique file path
            file_path = self.generate_file_path(user_id, filename)
            
            # Auto-detect content type if not provided
            if not content_type:
                content_type, _ = mimetypes.guess_type(filename)
                if not content_type:
                    content_type = "application/octet-stream"
            
            # Upload file
            response = self.storage.from_(self.bucket_name).upload(
                file_path,
                file_content,
                file_options={
                    "content-type": content_type,
                    "cache-control": "3600",
                    "upsert": False  # Don't overwrite existing files
                }
            )
            
            if response:
                logger.info(f"Successfully uploaded file: {file_path}")
                
                return {
                    "file_path": file_path,
                    "bucket": self.bucket_name,
                    "original_filename": filename,
                    "content_type": content_type,
                    "file_size": len(file_content),
                    "public_url": self.get_public_url(file_path)
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return None
    
    async def download_file(self, file_path: str) -> Optional[bytes]:
        """
        Download a file from Supabase Storage
        
        Args:
            file_path: Path to the file in storage
            
        Returns:
            File content as bytes, or None if failed
        """
        try:
            response = self.storage.from_(self.bucket_name).download(file_path)
            
            if response:
                logger.info(f"Successfully downloaded file: {file_path}")
                return response
            
            return None
            
        except Exception as e:
            logger.error(f"Error downloading file {file_path}: {e}")
            return None
    
    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from Supabase Storage
        
        Args:
            file_path: Path to the file in storage
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            response = self.storage.from_(self.bucket_name).remove([file_path])
            
            if response:
                logger.info(f"Successfully deleted file: {file_path}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False
    
    def get_public_url(self, file_path: str) -> Optional[str]:
        """
        Get public URL for a file (if bucket is public)
        
        Args:
            file_path: Path to the file in storage
            
        Returns:
            Public URL or None if not available
        """
        try:
            response = self.storage.from_(self.bucket_name).get_public_url(file_path)
            return response
        except Exception as e:
            logger.error(f"Error getting public URL for {file_path}: {e}")
            return None
    
    async def create_signed_url(self, file_path: str, expires_in: int = 3600) -> Optional[str]:
        """
        Create a signed URL for private file access
        
        Args:
            file_path: Path to the file in storage
            expires_in: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Signed URL or None if failed
        """
        try:
            response = self.storage.from_(self.bucket_name).create_signed_url(
                file_path, 
                expires_in
            )
            
            if response:
                return response.get("signed_url")
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating signed URL for {file_path}: {e}")
            return None
    
    async def list_user_files(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List all files for a user
        
        Args:
            user_id: User ID
            limit: Maximum number of files to return
            
        Returns:
            List of file metadata
        """
        try:
            response = self.storage.from_(self.bucket_name).list(
                path=user_id,
                limit=limit,
                sort_by={
                    "column": "created_at",
                    "order": "desc"
                }
            )
            
            if response:
                return response
            
            return []
            
        except Exception as e:
            logger.error(f"Error listing files for user {user_id}: {e}")
            return []
    
    async def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific file
        
        Args:
            file_path: Path to the file in storage
            
        Returns:
            File metadata or None if not found
        """
        try:
            # Extract user_id and filename from path
            path_parts = file_path.split("/")
            if len(path_parts) >= 2:
                user_id = path_parts[0]
                files = await self.list_user_files(user_id)
                
                for file_info in files:
                    if file_info.get("name") == file_path:
                        return file_info
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return None
    
    async def get_storage_usage(self, user_id: str) -> Dict[str, Any]:
        """
        Get storage usage statistics for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Storage usage statistics
        """
        try:
            files = await self.list_user_files(user_id)
            
            total_files = len(files)
            total_size = sum(file_info.get("metadata", {}).get("size", 0) for file_info in files)
            
            # Group by file type
            type_stats = {}
            for file_info in files:
                mime_type = file_info.get("metadata", {}).get("mimetype", "unknown")
                file_size = file_info.get("metadata", {}).get("size", 0)
                
                if mime_type not in type_stats:
                    type_stats[mime_type] = {"count": 0, "size": 0}
                
                type_stats[mime_type]["count"] += 1
                type_stats[mime_type]["size"] += file_size
            
            return {
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": total_size / (1024 * 1024) if total_size > 0 else 0,
                "by_type": type_stats,
                "bucket": self.bucket_name
            }
            
        except Exception as e:
            logger.error(f"Error getting storage usage for user {user_id}: {e}")
            return {
                "total_files": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0,
                "by_type": {},
                "bucket": self.bucket_name
            }
    
    async def cleanup_user_files(self, user_id: str) -> int:
        """
        Delete all files for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Number of files deleted
        """
        try:
            files = await self.list_user_files(user_id)
            
            if not files:
                return 0
            
            file_paths = [f"{user_id}/{file_info['name']}" for file_info in files]
            response = self.storage.from_(self.bucket_name).remove(file_paths)
            
            deleted_count = len(response) if response else 0
            logger.info(f"Deleted {deleted_count} files for user {user_id}")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up files for user {user_id}: {e}")
            return 0


# Global storage manager instance
storage_manager = SupabaseStorageManager()


# Convenience functions
async def upload_user_file(user_id: str, file_content: bytes, filename: str, 
                          content_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Convenience function to upload a file for a user
    
    Args:
        user_id: User ID
        file_content: File content as bytes
        filename: Original filename
        content_type: MIME type
        
    Returns:
        Upload result or None if failed
    """
    return await storage_manager.upload_file(user_id, file_content, filename, content_type)


async def get_user_file_url(file_path: str, expires_in: int = 3600) -> Optional[str]:
    """
    Get a signed URL for accessing a user file
    
    Args:
        file_path: Path to the file in storage
        expires_in: URL expiration time in seconds
        
    Returns:
        Signed URL or None if failed
    """
    return await storage_manager.create_signed_url(file_path, expires_in)