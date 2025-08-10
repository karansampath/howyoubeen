"""
Supabase client wrapper for KeepInTouch

This module provides a centralized Supabase client with configuration,
error handling, and connection management.
"""

import os
from typing import Optional
from dotenv import load_dotenv
from supabase import create_client, Client
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class SupabaseConfig:
    """Configuration for Supabase connection"""
    
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.anon_key = os.getenv("SUPABASE_ANON_KEY") 
        self.service_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not self.url:
            raise ValueError("SUPABASE_URL environment variable is required")
        if not self.anon_key:
            raise ValueError("SUPABASE_ANON_KEY environment variable is required")
    
    @property
    def is_configured(self) -> bool:
        """Check if Supabase is properly configured"""
        return bool(self.url and self.anon_key)


class SupabaseClient:
    """Wrapper for Supabase client with enhanced functionality"""
    
    def __init__(self, use_service_key: bool = False):
        """
        Initialize Supabase client
        
        Args:
            use_service_key: Whether to use service role key for admin operations
        """
        self.config = SupabaseConfig()
        self._client: Optional[Client] = None
        self.use_service_key = use_service_key
        
    @property
    def client(self) -> Client:
        """Get or create Supabase client"""
        if not self._client:
            key = self.config.service_key if self.use_service_key else self.config.anon_key
            if not key:
                raise ValueError(
                    f"Missing {'SUPABASE_SERVICE_KEY' if self.use_service_key else 'SUPABASE_ANON_KEY'} "
                    f"environment variable"
                )
            
            try:
                self._client = create_client(self.config.url, key)
                logger.info(f"Supabase client initialized with {'service' if self.use_service_key else 'anon'} key")
            except Exception as e:
                logger.error(f"Failed to create Supabase client: {e}")
                raise
                
        return self._client
    
    def test_connection(self) -> bool:
        """Test Supabase connection"""
        try:
            # Simple query to test connection
            response = self.client.table('users').select('count', count='exact').limit(0).execute()
            logger.info("Supabase connection test successful")
            return True
        except Exception as e:
            logger.error(f"Supabase connection test failed: {e}")
            return False
    
    def get_auth_user(self) -> Optional[dict]:
        """Get current authenticated user"""
        try:
            user = self.client.auth.get_user()
            return user.user if user else None
        except Exception as e:
            logger.error(f"Failed to get auth user: {e}")
            return None
    
    def set_auth_token(self, token: str):
        """Set authentication token for client"""
        try:
            self.client.postgrest.auth(token)
        except Exception as e:
            logger.error(f"Failed to set auth token: {e}")
            raise


# Global client instances
_anon_client = None
_service_client = None


def get_supabase_client(use_service_key: bool = False) -> SupabaseClient:
    """
    Get global Supabase client instance
    
    Args:
        use_service_key: Whether to use service role key
        
    Returns:
        SupabaseClient instance
    """
    global _anon_client, _service_client
    
    if use_service_key:
        if not _service_client:
            _service_client = SupabaseClient(use_service_key=True)
        return _service_client
    else:
        if not _anon_client:
            _anon_client = SupabaseClient(use_service_key=False)
        return _anon_client


def get_supabase_raw_client(use_service_key: bool = False) -> Client:
    """
    Get raw Supabase client for direct operations
    
    Args:
        use_service_key: Whether to use service role key
        
    Returns:
        Raw Supabase Client instance
    """
    return get_supabase_client(use_service_key).client


# Convenience functions for common operations
async def execute_query(table: str, query_builder, use_service_key: bool = False):
    """
    Execute a query with error handling
    
    Args:
        table: Table name
        query_builder: Query builder function that takes a table reference
        use_service_key: Whether to use service key
        
    Returns:
        Query result data
        
    Raises:
        Exception: If query fails
    """
    try:
        client = get_supabase_raw_client(use_service_key)
        table_ref = client.table(table)
        response = query_builder(table_ref).execute()
        return response.data
    except Exception as e:
        logger.error(f"Query failed on table '{table}': {e}")
        raise


async def insert_data(table: str, data: dict, use_service_key: bool = False):
    """
    Insert data with error handling
    
    Args:
        table: Table name
        data: Data to insert
        use_service_key: Whether to use service key
        
    Returns:
        Inserted data
    """
    return await execute_query(
        table,
        lambda t: t.insert(data),
        use_service_key
    )


async def update_data(table: str, data: dict, match_condition: dict, use_service_key: bool = False):
    """
    Update data with error handling
    
    Args:
        table: Table name
        data: Data to update
        match_condition: WHERE conditions
        use_service_key: Whether to use service key
        
    Returns:
        Updated data
    """
    def build_query(t):
        query = t.update(data)
        for key, value in match_condition.items():
            query = query.eq(key, value)
        return query
    
    return await execute_query(table, build_query, use_service_key)


async def select_data(table: str, columns: str = "*", filters: dict = None, use_service_key: bool = False):
    """
    Select data with error handling
    
    Args:
        table: Table name
        columns: Columns to select
        filters: WHERE conditions
        use_service_key: Whether to use service key
        
    Returns:
        Selected data
    """
    def build_query(t):
        query = t.select(columns)
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        return query
    
    return await execute_query(table, build_query, use_service_key)


async def delete_data(table: str, match_condition: dict, use_service_key: bool = False):
    """
    Delete data with error handling
    
    Args:
        table: Table name  
        match_condition: WHERE conditions
        use_service_key: Whether to use service key
        
    Returns:
        Deleted data
    """
    def build_query(t):
        query = t.delete()
        for key, value in match_condition.items():
            query = query.eq(key, value)
        return query
    
    return await execute_query(table, build_query, use_service_key)