"""
Base repository class with common database operations
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from uuid import UUID
import logging

from ..supabase_client import get_supabase_raw_client

logger = logging.getLogger(__name__)


class BaseRepository(ABC):
    """Base repository class with common CRUD operations"""
    
    def __init__(self, use_service_key: bool = False):
        """
        Initialize repository
        
        Args:
            use_service_key: Whether to use service role key
        """
        self.use_service_key = use_service_key
        self._client = None
    
    @property
    def client(self):
        """Get Supabase client"""
        if not self._client:
            self._client = get_supabase_raw_client(self.use_service_key)
        return self._client
    
    @property
    @abstractmethod
    def table_name(self) -> str:
        """Table name for this repository"""
        pass
    
    def table(self):
        """Get table reference"""
        return self.client.table(self.table_name)
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new record
        
        Args:
            data: Data to insert
            
        Returns:
            Created record
            
        Raises:
            Exception: If creation fails
        """
        try:
            response = self.table().insert(data).execute()
            if response.data:
                logger.info(f"Created record in {self.table_name}: {response.data[0].get('id')}")
                return response.data[0]
            else:
                raise Exception(f"Failed to create record in {self.table_name}")
        except Exception as e:
            logger.error(f"Error creating record in {self.table_name}: {e}")
            raise
    
    async def get_by_id(self, record_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        """
        Get record by ID
        
        Args:
            record_id: Record ID
            
        Returns:
            Record data or None if not found
        """
        try:
            response = self.table().select("*").eq("id", str(record_id)).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error getting record from {self.table_name}: {e}")
            raise
    
    async def update(self, record_id: Union[str, UUID], data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update record by ID
        
        Args:
            record_id: Record ID
            data: Data to update
            
        Returns:
            Updated record or None if not found
        """
        try:
            response = self.table().update(data).eq("id", str(record_id)).execute()
            if response.data:
                logger.info(f"Updated record in {self.table_name}: {record_id}")
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error updating record in {self.table_name}: {e}")
            raise
    
    async def delete(self, record_id: Union[str, UUID]) -> bool:
        """
        Delete record by ID
        
        Args:
            record_id: Record ID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            response = self.table().delete().eq("id", str(record_id)).execute()
            if response.data:
                logger.info(f"Deleted record from {self.table_name}: {record_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting record from {self.table_name}: {e}")
            raise
    
    async def find_by(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find records by filters
        
        Args:
            filters: Filter conditions
            
        Returns:
            List of matching records
        """
        try:
            query = self.table().select("*")
            for key, value in filters.items():
                query = query.eq(key, value)
            
            response = query.execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error finding records in {self.table_name}: {e}")
            raise
    
    async def find_one_by(self, filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find single record by filters
        
        Args:
            filters: Filter conditions
            
        Returns:
            First matching record or None
        """
        records = await self.find_by(filters)
        return records[0] if records else None
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records with optional filters
        
        Args:
            filters: Optional filter conditions
            
        Returns:
            Number of matching records
        """
        try:
            query = self.table().select("*", count="exact")
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            response = query.limit(0).execute()
            return response.count or 0
        except Exception as e:
            logger.error(f"Error counting records in {self.table_name}: {e}")
            raise
    
    async def exists(self, filters: Dict[str, Any]) -> bool:
        """
        Check if record exists with filters
        
        Args:
            filters: Filter conditions
            
        Returns:
            True if record exists, False otherwise
        """
        count = await self.count(filters)
        return count > 0