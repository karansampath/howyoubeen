"""Newsletter service for generating and sending newsletters"""

import smtplib
import ssl
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional, Dict, Any
import os
import logging

from ..data_models.models import NewsletterSubscription, User, LifeEvent, LifeFact
from ..data_models.enums import VisibilityCategoryType, NewsletterFrequency, SubscriptionStatus
from ..storage.repositories.newsletter_repository import NewsletterRepository
from ..storage.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class NewsletterService:
    """Service for managing newsletter operations"""
    
    def __init__(
        self,
        newsletter_repo: NewsletterRepository,
        user_repo: UserRepository,
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 587
    ):
        self.newsletter_repo = newsletter_repo
        self.user_repo = user_repo
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        
        # Email credentials from environment
        self.sender_email = os.getenv("NEWSLETTER_EMAIL", "noreply@howyoubeen.com")
        self.sender_password = os.getenv("NEWSLETTER_PASSWORD")
        self.sender_name = os.getenv("NEWSLETTER_NAME", "HowYouBeen")

    async def subscribe_to_newsletter(
        self,
        privacy_code: str,
        subscriber_email: str,
        frequency: NewsletterFrequency,
        subscriber_name: Optional[str] = None,
        referral_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Subscribe to a user's newsletter using privacy code"""
        
        # Handle referral code if provided
        referral_info = None
        referred_by_user_id = None
        
        if referral_code:
            # First try to get referral link info
            referral_link = await self.newsletter_repo.get_referral_link_by_code(referral_code)
            if referral_link:
                referral_info = referral_link
                referred_by_user_id = referral_link.created_by_user_id
                
                # Increment click count
                await self.newsletter_repo.increment_referral_click(referral_code)
                
                # Use referral link's privacy level and user
                privacy_info = {
                    'user_id': referral_link.user_id,
                    'privacy_level': referral_link.privacy_level.value,
                }
                
                # Get username from user repository
                user = await self.user_repo.get_user_by_id(referral_link.user_id)
                if user:
                    privacy_info['username'] = user.username
                else:
                    return {"success": False, "message": "Invalid referral link - user not found"}
            else:
                # If referral_code doesn't match a referral link, treat it as a privacy code
                privacy_info = await self.newsletter_repo.get_privacy_level_by_code(referral_code)
                if not privacy_info:
                    return {"success": False, "message": "Invalid subscription link"}
        else:
            # Decode privacy level from privacy code
            privacy_info = await self.newsletter_repo.get_privacy_level_by_code(privacy_code)
            if not privacy_info:
                return {"success": False, "message": "Invalid subscription link"}
        
        try:
            subscription = await self.newsletter_repo.create_subscription(
                source_user_id=privacy_info['user_id'],
                source_username=privacy_info['username'],
                subscriber_email=subscriber_email,
                subscriber_name=subscriber_name,
                privacy_level=VisibilityCategoryType(privacy_info['privacy_level']),
                frequency=frequency,
                referred_by_user_id=referred_by_user_id,
                referral_code=referral_code
            )
            
            # If this was a referral, increment conversion count
            if referral_code and referral_info:
                await self.newsletter_repo.increment_referral_conversion(referral_code)
            
            message = f"Successfully subscribed to {privacy_info['username']}'s {frequency.value} newsletter"
            if referred_by_user_id:
                referrer = await self.user_repo.get_user_by_id(referred_by_user_id)
                if referrer:
                    message += f" (referred by {referrer.full_name})"
            
            return {
                "success": True,
                "subscription_id": subscription.subscription_id,
                "message": message,
                "unsubscribe_code": subscription.subscription_code
            }
            
        except Exception as e:
            logger.error(f"Failed to create subscription: {e}")
            return {"success": False, "message": "Subscription failed. You may already be subscribed."}

    async def unsubscribe_from_newsletter(self, subscription_code: str) -> Dict[str, Any]:
        """Unsubscribe from newsletter using subscription code"""
        
        subscription = await self.newsletter_repo.get_subscription_by_code(subscription_code)
        if not subscription:
            return {"success": False, "message": "Invalid unsubscribe link"}
        
        success = await self.newsletter_repo.update_subscription_status(
            subscription_code, SubscriptionStatus.UNSUBSCRIBED
        )
        
        if success:
            return {
                "success": True,
                "message": f"Successfully unsubscribed from {subscription.source_username}'s newsletter"
            }
        else:
            return {"success": False, "message": "Failed to unsubscribe"}

    async def get_user_subscriptions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all subscriptions for a user's newsletter"""
        
        subscriptions = await self.newsletter_repo.get_subscriptions_by_user(user_id)
        
        return [{
            "subscription_id": sub.subscription_id,
            "subscriber_email": sub.subscriber_email,
            "privacy_level": sub.privacy_level.value,
            "frequency": sub.frequency.value,
            "status": sub.status.value,
            "last_sent": sub.last_sent.isoformat() if sub.last_sent else None,
            "created_at": sub.created_at.isoformat()
        } for sub in subscriptions]

    async def generate_newsletter_content(
        self, user: User, privacy_level: VisibilityCategoryType, frequency: NewsletterFrequency
    ) -> str:
        """Generate newsletter content based on user's data and privacy level"""
        
        # Calculate time range based on frequency
        now = datetime.now()
        if frequency == NewsletterFrequency.DAILY:
            since_date = now - timedelta(days=1)
        elif frequency == NewsletterFrequency.WEEKLY:
            since_date = now - timedelta(weeks=1)
        else:  # MONTHLY
            since_date = now - timedelta(days=30)
        
        # Filter life events and facts by privacy level and date
        relevant_entries = [
            entry for entry in user.life_events
            if (entry.visibility.type == privacy_level or 
                privacy_level in [cat.type for cat in entry.visibility.also_visible]) and
               entry.start_date >= since_date
        ]
        
        relevant_facts = [
            fact for fact in user.facts
            if (fact.visibility.type == privacy_level or 
                privacy_level in [cat.type for cat in fact.visibility.also_visible]) and
               fact.date >= since_date
        ]
        
        # Generate content
        content = f"# What's new with {user.full_name}\n\n"
        
        if user.bio:
            content += f"*{user.bio}*\n\n"
        
        if relevant_entries:
            content += "## Recent Updates\n\n"
            for entry in sorted(relevant_entries, key=lambda x: x.start_date, reverse=True):
                date_str = entry.start_date.strftime("%B %d, %Y")
                content += f"**{date_str}**: {entry.summary}\n\n"
        
        if relevant_facts:
            content += "## Recent Insights\n\n"
            for fact in sorted(relevant_facts, key=lambda x: x.date, reverse=True):
                content += f"• {fact.summary}\n"
            content += "\n"
        
        if not relevant_entries and not relevant_facts:
            content += f"{user.full_name} hasn't shared any updates in the {frequency.value} period, but you can always chat with their AI to learn more!\n\n"
        
        content += f"---\n\n"
        content += f"💬 **Chat with {user.full_name}**: https://howyoubeen.com/{user.username}\n\n"
        content += f"*This is an automated newsletter from HowYouBeen. Reply to this email or visit the chat link above to connect directly.*"
        
        return content

    def create_email_message(
        self, 
        recipient_email: str, 
        subject: str, 
        content: str,
        unsubscribe_code: str
    ) -> MIMEMultipart:
        """Create email message with HTML and text versions"""
        
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{self.sender_name} <{self.sender_email}>"
        message["To"] = recipient_email
        
        # Create HTML version
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    {content.replace('\n', '<br>').replace('# ', '<h1>').replace('## ', '<h2>').replace('**', '<strong>').replace('**', '</strong>')}
                    
                    <hr style="margin: 30px 0;">
                    <p style="font-size: 12px; color: #666;">
                        <a href="https://howyoubeen.com/unsubscribe/{unsubscribe_code}" style="color: #666;">
                            Unsubscribe from this newsletter
                        </a>
                    </p>
                </div>
            </body>
        </html>
        """
        
        # Create text version
        text_content = content + f"\n\nUnsubscribe: https://howyoubeen.com/unsubscribe/{unsubscribe_code}"
        
        # Attach parts
        text_part = MIMEText(text_content, "plain")
        html_part = MIMEText(html_content, "html")
        
        message.attach(text_part)
        message.attach(html_part)
        
        return message

    async def send_newsletter(self, subscription: NewsletterSubscription) -> Dict[str, Any]:
        """Send newsletter to a single subscriber"""
        
        try:
            # Get user data
            user = await self.user_repo.get_user_by_id(subscription.source_user_id)
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Generate content
            content = await self.generate_newsletter_content(
                user, subscription.privacy_level, subscription.frequency
            )
            
            # Create subject
            frequency_text = subscription.frequency.value.title()
            subject = f"{frequency_text} update from {user.full_name}"
            
            # Create email
            message = self.create_email_message(
                subscription.subscriber_email,
                subject,
                content,
                subscription.subscription_code
            )
            
            # Send email
            if self.sender_password:
                context = ssl.create_default_context()
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls(context=context)
                    server.login(self.sender_email, self.sender_password)
                    server.send_message(message)
            else:
                # In development/testing, just log the email
                logger.info(f"Mock email sent to {subscription.subscriber_email}")
                logger.info(f"Subject: {subject}")
                logger.info(f"Content preview: {content[:200]}...")
            
            # Update last sent timestamp
            await self.newsletter_repo.update_last_sent(subscription.subscription_id)
            
            # Log successful delivery
            await self.newsletter_repo.log_delivery(
                subscription.subscription_id,
                "sent",
                content_preview=content[:200]
            )
            
            return {"success": True, "message": "Newsletter sent successfully"}
            
        except Exception as e:
            logger.error(f"Failed to send newsletter: {e}")
            
            # Log failed delivery
            await self.newsletter_repo.log_delivery(
                subscription.subscription_id,
                "failed",
                error_message=str(e)
            )
            
            return {"success": False, "error": str(e)}

    async def send_newsletters_by_frequency(self, frequency: NewsletterFrequency) -> Dict[str, Any]:
        """Send all newsletters for a specific frequency"""
        
        # Get active subscriptions for this frequency
        subscriptions = await self.newsletter_repo.get_active_subscriptions_by_frequency(frequency)
        
        sent_count = 0
        failed_count = 0
        
        for subscription in subscriptions:
            result = await self.send_newsletter(subscription)
            if result["success"]:
                sent_count += 1
            else:
                failed_count += 1
        
        return {
            "success": True,
            "total_subscriptions": len(subscriptions),
            "sent_count": sent_count,
            "failed_count": failed_count
        }

    async def create_subscription_link(
        self, user_id: str, privacy_level: VisibilityCategoryType
    ) -> str:
        """Create a subscription link for a specific privacy level"""
        
        link_code = await self.newsletter_repo.create_privacy_link(user_id, privacy_level)
        return f"https://howyoubeen.com/subscribe/{link_code}"

    # Referral Link Methods
    async def create_referral_link(
        self,
        user_id: str,
        created_by_user_id: str,
        friend_name: str,
        privacy_level: VisibilityCategoryType,
        friend_email: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Create a referral link for a friend"""
        
        try:
            referral_link = await self.newsletter_repo.create_referral_link(
                user_id=user_id,
                created_by_user_id=created_by_user_id,
                friend_name=friend_name,
                privacy_level=privacy_level,
                friend_email=friend_email,
                expires_at=expires_at
            )
            
            return {
                "success": True,
                "referral_link": f"https://howyoubeen.com/subscribe/{referral_link.referral_code}",
                "referral_code": referral_link.referral_code,
                "message": f"Referral link created for {friend_name}"
            }
        except Exception as e:
            logger.error(f"Failed to create referral link: {e}")
            return {
                "success": False,
                "referral_link": None,
                "referral_code": None,
                "message": "Failed to create referral link"
            }

    async def get_user_referral_links(self, created_by_user_id: str) -> List[Dict[str, Any]]:
        """Get all referral links created by a user"""
        
        referral_links = await self.newsletter_repo.get_user_referral_links(created_by_user_id)
        
        return [{
            "referral_id": link.referral_id,
            "user_id": link.user_id,
            "friend_name": link.friend_name,
            "friend_email": link.friend_email,
            "privacy_level": link.privacy_level.value,
            "referral_code": link.referral_code,
            "referral_link": f"https://howyoubeen.com/subscribe/{link.referral_code}",
            "clicks": link.clicks,
            "conversions": link.conversions,
            "is_active": link.is_active,
            "created_at": link.created_at.isoformat(),
            "expires_at": link.expires_at.isoformat() if link.expires_at else None
        } for link in referral_links]

    async def get_referrals_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all subscribers referred for a user's newsletter"""
        
        return await self.newsletter_repo.get_referrals_for_user(user_id)
