"""
Visibility repository for managing user privacy categories
"""

from typing import Any, Dict, List, Optional
import logging

from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class VisibilityRepository(BaseRepository):
    """Repository for visibility category operations"""
    
    @property
    def table_name(self) -> str:
        return "visibility_categories"
    
    async def create_categories_for_user(self, user_id: str, categories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create multiple visibility categories for a user
        
        Args:
            user_id: User ID
            categories: List of category data (type, name, etc.)
            
        Returns:
            List of created categories
        """
        created_categories = []
        
        for category_data in categories:
            category = {
                "user_id": user_id,
                "type": category_data.get("type"),
                "name": category_data.get("name")
            }
            
            try:
                created = await self.create(category)
                created_categories.append(created)
            except Exception as e:
                logger.error(f"Error creating visibility category: {e}")
                # Continue creating other categories even if one fails
                continue
        
        return created_categories
    
    async def get_categories_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all visibility categories for a user
        
        Args:
            user_id: User ID
            
        Returns:
            List of user's visibility categories
        """
        return await self.find_by({"user_id": user_id})
    
    async def get_category_by_type(self, user_id: str, category_type: str) -> Optional[Dict[str, Any]]:
        """
        Get specific category by type for a user
        
        Args:
            user_id: User ID
            category_type: Category type (e.g., 'close_family', 'best_friends')
            
        Returns:
            Category data or None if not found
        """
        return await self.find_one_by({
            "user_id": user_id,
            "type": category_type
        })
    
    async def get_default_category_for_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get default visibility category for a user (usually 'public' or first created)
        
        Args:
            user_id: User ID
            
        Returns:
            Default category or None
        """
        # Try to get 'public' category first
        public_category = await self.get_category_by_type(user_id, "public")
        if public_category:
            return public_category
        
        # If no public category, get any category
        categories = await self.get_categories_for_user(user_id)
        return categories[0] if categories else None
    
    async def update_category(self, category_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update visibility category
        
        Args:
            category_id: Category ID
            updates: Data to update
            
        Returns:
            Updated category data
        """
        return await self.update(category_id, updates)
    
    async def delete_category(self, category_id: str) -> bool:
        """
        Delete visibility category
        
        Args:
            category_id: Category ID
            
        Returns:
            True if deleted successfully
        """
        return await self.delete(category_id)
    
    async def create_default_categories(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Create default visibility categories for a new user
        
        Args:
            user_id: User ID
            
        Returns:
            List of created default categories
        """
        default_categories = [
            {"type": "close_family", "name": None},
            {"type": "best_friends", "name": None},
            {"type": "good_friends", "name": None},
            {"type": "public", "name": None}
        ]
        
        return await self.create_categories_for_user(user_id, default_categories)
    
    async def get_category_usage_stats(self, user_id: str) -> Dict[str, int]:
        """
        Get usage statistics for visibility categories
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with category usage counts
        """
        try:
            # Get categories for user
            categories = await self.get_categories_for_user(user_id)
            
            stats = {}
            for category in categories:
                category_id = category["id"]
                category_type = category["type"]
                
                # Count diary entries using this category
                diary_count = await self._count_usage_in_table("diary_entries", category_id)
                
                # Count life facts using this category
                facts_count = await self._count_usage_in_table("life_facts", category_id)
                
                # Count friends using this category
                friends_count = await self._count_usage_in_table("friends", category_id)
                
                stats[category_type] = {
                    "diary_entries": diary_count,
                    "life_facts": facts_count,
                    "friends": friends_count,
                    "total": diary_count + facts_count + friends_count
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting category usage stats: {e}")
            return {}
    
    async def _count_usage_in_table(self, table_name: str, category_id: str) -> int:
        """
        Count usage of category in a specific table
        
        Args:
            table_name: Name of table to check
            category_id: Category ID
            
        Returns:
            Usage count
        """
        try:
            response = (self.client.table(table_name)
                       .select("*", count="exact")
                       .eq("visibility_category_id", category_id)
                       .limit(0)
                       .execute())
            
            return response.count or 0
            
        except Exception as e:
            logger.error(f"Error counting usage in {table_name}: {e}")
            return 0
    
    async def can_delete_category(self, category_id: str) -> bool:
        """
        Check if category can be safely deleted (not in use)
        
        Args:
            category_id: Category ID
            
        Returns:
            True if safe to delete, False otherwise
        """
        try:
            # Check diary entries
            diary_count = await self._count_usage_in_table("diary_entries", category_id)
            if diary_count > 0:
                return False
            
            # Check life facts
            facts_count = await self._count_usage_in_table("life_facts", category_id)
            if facts_count > 0:
                return False
            
            # Check friends
            friends_count = await self._count_usage_in_table("friends", category_id)
            if friends_count > 0:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking if category can be deleted: {e}")
            return False