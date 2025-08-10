"""Newsletter subscription repository for database operations"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import uuid4

from ..base_repository import BaseRepository
from ...data_models.models import NewsletterSubscription
from ...data_models.enums import VisibilityCategoryType, NewsletterFrequency, SubscriptionStatus


class NewsletterRepository(BaseRepository):
    """Repository for managing newsletter subscriptions"""

    async def create_subscription(
        self,
        source_user_id: str,
        source_username: str,
        subscriber_email: str,
        privacy_level: VisibilityCategoryType,
        frequency: NewsletterFrequency
    ) -> NewsletterSubscription:
        """Create a new newsletter subscription"""
        subscription = NewsletterSubscription(
            source_user_id=source_user_id,
            source_username=source_username,
            subscriber_email=subscriber_email,
            privacy_level=privacy_level,
            frequency=frequency
        )
        
        query = """
            INSERT INTO newsletter_subscriptions 
            (id, source_user_id, source_username, subscriber_email, privacy_level, frequency, subscription_code, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING *
        """
        
        result = await self.storage_service.execute_query(
            query,
            subscription.subscription_id,
            subscription.source_user_id,
            subscription.source_username,
            subscription.subscriber_email,
            subscription.privacy_level.value,
            subscription.frequency.value,
            subscription.subscription_code,
            subscription.created_at,
            subscription.updated_at
        )
        
        if result:
            return self._row_to_subscription(result[0])
        raise Exception("Failed to create subscription")

    async def get_subscription_by_code(self, subscription_code: str) -> Optional[NewsletterSubscription]:
        """Get subscription by unsubscribe code"""
        query = "SELECT * FROM newsletter_subscriptions WHERE subscription_code = $1"
        result = await self.storage_service.execute_query(query, subscription_code)
        
        if result:
            return self._row_to_subscription(result[0])
        return None

    async def get_subscriptions_by_user(self, user_id: str) -> List[NewsletterSubscription]:
        """Get all subscriptions for a user's newsletter"""
        query = """
            SELECT * FROM newsletter_subscriptions 
            WHERE source_user_id = $1 
            ORDER BY created_at DESC
        """
        result = await self.storage_service.execute_query(query, user_id)
        
        return [self._row_to_subscription(row) for row in result]

    async def get_active_subscriptions_by_frequency(
        self, frequency: NewsletterFrequency
    ) -> List[NewsletterSubscription]:
        """Get all active subscriptions for a specific frequency"""
        query = """
            SELECT * FROM newsletter_subscriptions 
            WHERE status = 'active' AND frequency = $1
            ORDER BY last_sent ASC NULLS FIRST
        """
        result = await self.storage_service.execute_query(query, frequency.value)
        
        return [self._row_to_subscription(row) for row in result]

    async def update_subscription_status(
        self, subscription_code: str, status: SubscriptionStatus
    ) -> bool:
        """Update subscription status"""
        query = """
            UPDATE newsletter_subscriptions 
            SET status = $1, updated_at = $2 
            WHERE subscription_code = $3
        """
        result = await self.storage_service.execute_query(
            query, status.value, datetime.now(), subscription_code
        )
        return bool(result)

    async def update_last_sent(self, subscription_id: str) -> bool:
        """Update last sent timestamp for a subscription"""
        query = """
            UPDATE newsletter_subscriptions 
            SET last_sent = $1, updated_at = $2 
            WHERE id = $3
        """
        result = await self.storage_service.execute_query(
            query, datetime.now(), datetime.now(), subscription_id
        )
        return bool(result)

    async def log_delivery(
        self,
        subscription_id: str,
        status: str,
        error_message: Optional[str] = None,
        content_preview: Optional[str] = None
    ) -> bool:
        """Log newsletter delivery attempt"""
        query = """
            INSERT INTO newsletter_delivery_log 
            (id, subscription_id, status, error_message, content_preview)
            VALUES ($1, $2, $3, $4, $5)
        """
        
        log_id = str(uuid4())
        result = await self.storage_service.execute_query(
            query, log_id, subscription_id, status, error_message, content_preview
        )
        return bool(result)

    async def create_privacy_link(
        self, user_id: str, privacy_level: VisibilityCategoryType
    ) -> str:
        """Create or get privacy level link code"""
        # First, check if link already exists
        query = """
            SELECT link_code FROM privacy_level_links 
            WHERE user_id = $1 AND privacy_level = $2 AND is_active = true
        """
        result = await self.storage_service.execute_query(query, user_id, privacy_level.value)
        
        if result:
            return str(result[0]['link_code'])
        
        # Create new link
        link_code = str(uuid4())
        insert_query = """
            INSERT INTO privacy_level_links (id, user_id, privacy_level, link_code)
            VALUES ($1, $2, $3, $4)
        """
        
        await self.storage_service.execute_query(
            insert_query, str(uuid4()), user_id, privacy_level.value, link_code
        )
        return link_code

    async def get_privacy_level_by_code(self, link_code: str) -> Optional[Dict[str, Any]]:
        """Get user and privacy level by link code"""
        query = """
            SELECT user_id, privacy_level, u.username
            FROM privacy_level_links pl
            JOIN users u ON pl.user_id = u.id
            WHERE pl.link_code = $1 AND pl.is_active = true
        """
        result = await self.storage_service.execute_query(query, link_code)
        
        if result:
            return {
                'user_id': str(result[0]['user_id']),
                'username': result[0]['username'],
                'privacy_level': result[0]['privacy_level']
            }
        return None

    def _row_to_subscription(self, row: Dict[str, Any]) -> NewsletterSubscription:
        """Convert database row to NewsletterSubscription model"""
        return NewsletterSubscription(
            subscription_id=str(row['id']),
            source_user_id=str(row['source_user_id']),
            source_username=row['source_username'],
            subscriber_email=row['subscriber_email'],
            privacy_level=VisibilityCategoryType(row['privacy_level']),
            frequency=NewsletterFrequency(row['frequency']),
            status=SubscriptionStatus(row['status']),
            subscription_code=str(row['subscription_code']),
            last_sent=row.get('last_sent'),
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
