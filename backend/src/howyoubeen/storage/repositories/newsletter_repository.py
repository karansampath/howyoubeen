"""Newsletter subscription repository for database operations"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import uuid4

from .base_repository import BaseRepository
from ...data_models.models import NewsletterSubscription, ReferralLink
from ...data_models.enums import VisibilityCategoryType, NewsletterFrequency, SubscriptionStatus


class NewsletterRepository(BaseRepository):
    """Repository for managing newsletter subscriptions"""

    async def create_subscription(
        self,
        source_user_id: str,
        source_username: str,
        subscriber_email: str,
        privacy_level: VisibilityCategoryType,
        frequency: NewsletterFrequency,
        subscriber_name: Optional[str] = None,
        referred_by_user_id: Optional[str] = None,
        referral_code: Optional[str] = None
    ) -> NewsletterSubscription:
        """Create a new newsletter subscription"""
        subscription = NewsletterSubscription(
            source_user_id=source_user_id,
            source_username=source_username,
            subscriber_email=subscriber_email,
            subscriber_name=subscriber_name,
            privacy_level=privacy_level,
            frequency=frequency,
            referred_by_user_id=referred_by_user_id,
            referral_code=referral_code
        )
        
        query = """
            INSERT INTO newsletter_subscriptions 
            (id, source_user_id, source_username, subscriber_email, subscriber_name, privacy_level, frequency, subscription_code, referred_by_user_id, referral_code, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING *
        """
        
        result = await self.storage_service.execute_query(
            query,
            subscription.subscription_id,
            subscription.source_user_id,
            subscription.source_username,
            subscription.subscriber_email,
            subscription.subscriber_name,
            subscription.privacy_level.value,
            subscription.frequency.value,
            subscription.subscription_code,
            subscription.referred_by_user_id,
            subscription.referral_code,
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
            subscriber_name=row.get('subscriber_name'),
            privacy_level=VisibilityCategoryType(row['privacy_level']),
            frequency=NewsletterFrequency(row['frequency']),
            status=SubscriptionStatus(row['status']),
            subscription_code=str(row['subscription_code']),
            referred_by_user_id=str(row['referred_by_user_id']) if row.get('referred_by_user_id') else None,
            referral_code=row.get('referral_code'),
            last_sent=row.get('last_sent'),
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    # Referral Link Methods
    async def create_referral_link(
        self,
        user_id: str,
        created_by_user_id: str,
        friend_name: str,
        privacy_level: VisibilityCategoryType,
        friend_email: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> ReferralLink:
        """Create a new referral link"""
        import secrets
        
        referral_link = ReferralLink(
            user_id=user_id,
            created_by_user_id=created_by_user_id,
            friend_name=friend_name,
            friend_email=friend_email,
            privacy_level=privacy_level,
            referral_code=secrets.token_urlsafe(16),  # Generate secure random code
            expires_at=expires_at
        )
        
        query = """
            INSERT INTO referral_links 
            (id, user_id, created_by_user_id, friend_name, friend_email, privacy_level, referral_code, created_at, expires_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING *
        """
        
        result = await self.storage_service.execute_query(
            query,
            referral_link.referral_id,
            referral_link.user_id,
            referral_link.created_by_user_id,
            referral_link.friend_name,
            referral_link.friend_email,
            referral_link.privacy_level.value,
            referral_link.referral_code,
            referral_link.created_at,
            referral_link.expires_at
        )
        
        if result:
            return self._row_to_referral_link(result[0])
        raise Exception("Failed to create referral link")

    async def get_referral_link_by_code(self, referral_code: str) -> Optional[ReferralLink]:
        """Get referral link by code"""
        query = "SELECT * FROM referral_links WHERE referral_code = $1 AND is_active = true"
        result = await self.storage_service.execute_query(query, referral_code)
        
        if result:
            return self._row_to_referral_link(result[0])
        return None

    async def get_user_referral_links(self, created_by_user_id: str) -> List[ReferralLink]:
        """Get all referral links created by a user"""
        query = "SELECT * FROM referral_links WHERE created_by_user_id = $1 AND is_active = true ORDER BY created_at DESC"
        results = await self.storage_service.execute_query(query, created_by_user_id)
        
        return [self._row_to_referral_link(row) for row in results or []]

    async def get_referrals_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all subscribers referred for a user's newsletter"""
        query = """
            SELECT ns.*, u.full_name as referrer_name
            FROM newsletter_subscriptions ns
            LEFT JOIN users u ON ns.referred_by_user_id = u.id
            WHERE ns.source_user_id = $1 AND ns.referred_by_user_id IS NOT NULL
            ORDER BY ns.created_at DESC
        """
        results = await self.storage_service.execute_query(query, user_id)
        
        referrals = []
        for row in results or []:
            referral_data = {
                'subscription_id': str(row['id']),
                'subscriber_email': row['subscriber_email'],
                'subscriber_name': row.get('subscriber_name'),
                'privacy_level': row['privacy_level'],
                'frequency': row['frequency'],
                'referral_code': row.get('referral_code'),
                'referred_by_user_id': str(row['referred_by_user_id']),
                'referrer_name': row.get('referrer_name'),
                'created_at': row['created_at']
            }
            referrals.append(referral_data)
        
        return referrals

    async def increment_referral_click(self, referral_code: str) -> bool:
        """Increment click count for referral link"""
        query = "UPDATE referral_links SET clicks = clicks + 1 WHERE referral_code = $1 AND is_active = true"
        result = await self.storage_service.execute_query(query, referral_code)
        return result is not None

    async def increment_referral_conversion(self, referral_code: str) -> bool:
        """Increment conversion count for referral link"""
        query = "UPDATE referral_links SET conversions = conversions + 1 WHERE referral_code = $1 AND is_active = true"
        result = await self.storage_service.execute_query(query, referral_code)
        return result is not None

    def _row_to_referral_link(self, row: Dict[str, Any]) -> ReferralLink:
        """Convert database row to ReferralLink model"""
        return ReferralLink(
            referral_id=str(row['id']),
            user_id=str(row['user_id']),
            created_by_user_id=str(row['created_by_user_id']),
            friend_name=row['friend_name'],
            friend_email=row.get('friend_email'),
            privacy_level=VisibilityCategoryType(row['privacy_level']),
            referral_code=row['referral_code'],
            clicks=row.get('clicks', 0),
            conversions=row.get('conversions', 0),
            is_active=row.get('is_active', True),
            created_at=row['created_at'],
            expires_at=row.get('expires_at')
        )
