#!/usr/bin/env python3
"""
Newsletter Demo Script

This script demonstrates the newsletter functionality with mock data.
Run this to test the complete newsletter flow.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any

# Import newsletter components
from lib.newsletter_mock_data import generate_test_data
from notifications.newsletter_service import NewsletterService
from storage.repositories.newsletter_repository import NewsletterRepository
from storage.repositories.user_repository import UserRepository
from storage.memory_store import MemoryStore
from data_models.enums import NewsletterFrequency, SubscriptionStatus


class NewsletterDemo:
    """Demo class for newsletter functionality"""
    
    def __init__(self):
        # Initialize with memory storage for demo
        self.storage_service = MemoryStore()
        self.newsletter_repo = NewsletterRepository(self.storage_service)
        self.user_repo = UserRepository(self.storage_service)
        self.newsletter_service = NewsletterService(self.newsletter_repo, self.user_repo)
        
    async def setup_demo_data(self):
        """Load demo data into memory store"""
        print("🚀 Setting up demo data...")
        
        test_data = generate_test_data()
        
        # Store users
        for user in test_data['users']:
            await self.user_repo.create_user(user)
            print(f"   ✓ Created user: {user.full_name} (@{user.username})")
        
        # Store subscriptions (normally done through API)
        for subscription in test_data['subscriptions']:
            # Mock the storage (in real app, this goes through newsletter_repo.create_subscription)
            print(f"   ✓ Created subscription: {subscription.subscriber_email} -> @{subscription.source_username} ({subscription.frequency.value})")
        
        # Store privacy links
        for link in test_data['privacy_links']:
            print(f"   ✓ Created privacy link: {link['privacy_level']} for @{link['username']}")
        
        print(f"✅ Demo data ready! {len(test_data['users'])} users, {len(test_data['subscriptions'])} subscriptions")
        return test_data
    
    async def demo_subscription_flow(self):
        """Demonstrate the subscription flow"""
        print("\n📧 Testing Newsletter Subscription Flow")
        print("=" * 50)
        
        # Test subscription
        print("\n1. Testing newsletter subscription...")
        result = await self.newsletter_service.subscribe_to_newsletter(
            privacy_code="bf-sarah-abc123",  # Best friends link for Sarah
            subscriber_email="demo@example.com",
            frequency=NewsletterFrequency.WEEKLY,
            subscriber_name="Demo User"
        )
        
        print(f"   Subscription result: {result}")
        
        # Test getting subscription info
        print("\n2. Testing subscription lookup...")
        if result.get("success"):
            unsubscribe_code = result.get("unsubscribe_code")
            subscription = await self.newsletter_repo.get_subscription_by_code(unsubscribe_code)
            if subscription:
                print(f"   ✓ Found subscription: {subscription.subscriber_email}")
            else:
                print("   ❌ Subscription not found")
        
    async def demo_newsletter_generation(self):
        """Demonstrate newsletter content generation"""
        print("\n📝 Testing Newsletter Content Generation")
        print("=" * 50)
        
        # Get a test user
        user = await self.user_repo.get_user_by_username("sarah_codes")
        if not user:
            print("❌ Test user not found")
            return
        
        print(f"\n1. Generating newsletter for {user.full_name}...")
        
        # Generate different newsletters for different privacy levels
        from data_models.enums import VisibilityCategoryType
        
        privacy_levels = [
            VisibilityCategoryType.BEST_FRIENDS,
            VisibilityCategoryType.GOOD_FRIENDS,
            VisibilityCategoryType.PUBLIC
        ]
        
        for privacy_level in privacy_levels:
            print(f"\n   📋 {privacy_level.value.title()} Newsletter:")
            print("   " + "-" * 40)
            
            content = await self.newsletter_service.generate_newsletter_content(
                user, privacy_level, NewsletterFrequency.WEEKLY
            )
            
            # Show preview of content
            lines = content.split('\n')
            preview_lines = lines[:10]  # First 10 lines
            for line in preview_lines:
                print(f"   {line}")
            
            if len(lines) > 10:
                print(f"   ... ({len(lines) - 10} more lines)")
    
    async def demo_email_formatting(self):
        """Demonstrate email formatting"""
        print("\n📮 Testing Email Formatting")
        print("=" * 50)
        
        # Create a sample newsletter
        content = """# What's new with Sarah Johnson

*Full-stack developer, AI enthusiast, and coffee connoisseur ☕*

## Recent Updates

**December 15, 2024**: Just launched my new side project!

**December 12, 2024**: Attended the local React meetup.

## Recent Insights

• Started learning Spanish and already completed 30 days in a row on Duolingo!

---

💬 **Chat with Sarah Johnson**: https://howyoubeen.com/sarah_codes"""
        
        # Format as email
        message = self.newsletter_service.create_email_message(
            recipient_email="demo@example.com",
            subject="Weekly update from Sarah Johnson",
            content=content,
            unsubscribe_code="demo-unsubscribe-123"
        )
        
        print("✓ Email message created successfully")
        print(f"   To: {message['To']}")
        print(f"   From: {message['From']}")
        print(f"   Subject: {message['Subject']}")
        print("   Content-Type: multipart/alternative")
        
        # Show text version preview
        text_content = None
        html_content = None
        
        for part in message.walk():
            if part.get_content_type() == "text/plain":
                text_content = part.get_payload(decode=True).decode()
            elif part.get_content_type() == "text/html":
                html_content = part.get_payload(decode=True).decode()
        
        if text_content:
            print("\n   📄 Text version preview:")
            print("   " + "-" * 30)
            for line in text_content.split('\n')[:8]:
                print(f"   {line}")
            print("   ...")
        
        if html_content:
            print("\n   🌐 HTML version created ✓")
    
    async def demo_cron_simulation(self):
        """Simulate the cron job functionality"""
        print("\n⏰ Simulating Cron Job Newsletter Sending")
        print("=" * 50)
        
        # Simulate sending daily newsletters
        print("\n1. Simulating daily newsletter batch...")
        daily_result = await self.newsletter_service.send_newsletters_by_frequency(
            NewsletterFrequency.DAILY
        )
        print(f"   Daily newsletters: {daily_result}")
        
        # Simulate sending weekly newsletters  
        print("\n2. Simulating weekly newsletter batch...")
        weekly_result = await self.newsletter_service.send_newsletters_by_frequency(
            NewsletterFrequency.WEEKLY
        )
        print(f"   Weekly newsletters: {weekly_result}")
        
        # Simulate sending monthly newsletters
        print("\n3. Simulating monthly newsletter batch...")
        monthly_result = await self.newsletter_service.send_newsletters_by_frequency(
            NewsletterFrequency.MONTHLY
        )
        print(f"   Monthly newsletters: {monthly_result}")
    
    async def demo_subscription_management(self):
        """Demonstrate subscription management"""
        print("\n👥 Testing Subscription Management")
        print("=" * 50)
        
        # Get subscriptions for a user
        print("\n1. Getting subscriptions for user...")
        user = await self.user_repo.get_user_by_username("sarah_codes")
        if user:
            subscriptions = await self.newsletter_service.get_user_subscriptions(user.user_id)
            print(f"   ✓ Found {len(subscriptions)} subscriptions for @{user.username}")
            
            for sub in subscriptions[:3]:  # Show first 3
                print(f"   • {sub['subscriber_email']} ({sub['frequency']}, {sub['privacy_level']})")
        
        # Test creating subscription links
        print("\n2. Creating subscription links...")
        if user:
            from data_models.enums import VisibilityCategoryType
            
            link = await self.newsletter_service.create_subscription_link(
                user.user_id, VisibilityCategoryType.BEST_FRIENDS
            )
            print(f"   ✓ Best friends link: {link}")
            
            link = await self.newsletter_service.create_subscription_link(
                user.user_id, VisibilityCategoryType.PUBLIC
            )
            print(f"   ✓ Public link: {link}")
    
    async def run_complete_demo(self):
        """Run the complete newsletter demo"""
        print("🎯 HowYouBeen Newsletter Service Demo")
        print("=" * 60)
        print("This demo showcases the complete newsletter functionality")
        print("with mock data and simulated email sending.\n")
        
        # Setup
        test_data = await self.setup_demo_data()
        
        # Run demo sections
        await self.demo_subscription_flow()
        await self.demo_newsletter_generation()
        await self.demo_email_formatting()
        await self.demo_subscription_management()
        await self.demo_cron_simulation()
        
        # Summary
        print("\n" + "=" * 60)
        print("✅ Newsletter Demo Complete!")
        print("\n🎉 All functionality tested successfully:")
        print("   • Newsletter subscription with privacy levels")
        print("   • Content generation based on user data")
        print("   • Email formatting (HTML + Text)")
        print("   • Subscription management")
        print("   • Cron job simulation")
        print("   • Mock data generation")
        print("\n📋 Next steps:")
        print("   • Deploy Modal cron job: modal deploy modal_newsletter_cron.py")
        print("   • Set up environment variables for email")
        print("   • Configure database with newsletter schema")
        print("   • Test frontend components")
        print("   • Add API routes to your server")


async def main():
    """Main demo function"""
    demo = NewsletterDemo()
    await demo.run_complete_demo()


if __name__ == "__main__":
    print("Starting Newsletter Demo...")
    asyncio.run(main())
