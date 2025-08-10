"""Newsletter API routes"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from datetime import datetime

from ...data_models.api_models import (
    NewsletterSubscribePayload,
    NewsletterUnsubscribePayload,
    GetNewsletterSubscriptionsPayload,
    NewsletterGeneratePayload,
    NewsletterSubscribeResult,
    NewsletterUnsubscribeResult,
    GetNewsletterSubscriptionsResult,
    NewsletterGenerateResult
)
from ...data_models.enums import NewsletterFrequency, VisibilityCategoryType
from ...data_models.models import NewsletterConfig, VisibilityCategory
# from ...notifications.newsletter_service import NewsletterService  # TODO: Fix repository dependencies
from ...ai_engine.newsletter_generator import NewsletterGenerator
# from ...storage.repositories.newsletter_repository import NewsletterRepository  # TODO: Fix repository dependencies
# from ...storage.repositories.user_repository import UserRepository  # TODO: Fix repository dependencies
from ...storage.storage_factory import get_storage_service

router = APIRouter(prefix="/newsletter", tags=["newsletter"])


def get_newsletter_service():  # -> NewsletterService:
    """Dependency to get newsletter service"""
    # TODO: Uncomment when repository dependencies are fixed
    # storage_service = get_storage_service()
    # newsletter_repo = NewsletterRepository(storage_service)
    # user_repo = UserRepository(storage_service)
    # return NewsletterService(newsletter_repo, user_repo)
    raise HTTPException(status_code=501, detail="Newsletter service temporarily unavailable")


def get_newsletter_generator() -> NewsletterGenerator:
    """Dependency to get newsletter generator"""
    storage_service = get_storage_service()
    return NewsletterGenerator(storage_service)


@router.post("/generate", response_model=NewsletterGenerateResult)
async def generate_newsletter(
    payload: NewsletterGeneratePayload,
    newsletter_generator: NewsletterGenerator = Depends(get_newsletter_generator)
) -> NewsletterGenerateResult:
    """Generate a newsletter based on user's life events and configuration"""
    
    try:
        # Convert the payload newsletter_config dict to NewsletterConfig model
        config_data = payload.newsletter_config
        
        # Parse visibility categories
        visibility_categories = []
        for vis_config in config_data.get("visibility", []):
            visibility_categories.append(
                VisibilityCategory(
                    type=VisibilityCategoryType(vis_config.get("type")),
                    name=vis_config.get("name")
                )
            )
        
        # Create NewsletterConfig object
        newsletter_config = NewsletterConfig(
            instructions=config_data.get("instructions"),
            periodicity=config_data.get("periodicity", 24),  # Default to 24 hours
            start_date=datetime.fromisoformat(config_data.get("start_date")),
            visibility=visibility_categories,
            name=config_data.get("name", "Newsletter")
        )
        
        # Generate the newsletter
        result = await newsletter_generator.generate_newsletter(
            user_id=payload.user_id,
            newsletter_config=newsletter_config
        )
        
        return NewsletterGenerateResult(
            success=result.success,
            content=result.content,
            error_message=result.error_message,
            events_count=result.events_count,
            generation_summary=result.generation_summary
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/subscribe", response_model=NewsletterSubscribeResult)
async def subscribe_to_newsletter(
    payload: NewsletterSubscribePayload,
    newsletter_service = Depends(get_newsletter_service)
) -> NewsletterSubscribeResult:
    """Subscribe to a newsletter using a privacy code"""
    
    try:
        result = await newsletter_service.subscribe_to_newsletter(
            privacy_code=payload.privacy_code,
            subscriber_email=payload.subscriber_email,
            frequency=payload.frequency,
            subscriber_name=payload.subscriber_name
        )
        
        if result["success"]:
            return NewsletterSubscribeResult(
                success=True,
                subscription_id=result["subscription_id"],
                message=result["message"],
                unsubscribe_code=result["unsubscribe_code"]
            )
        else:
            return NewsletterSubscribeResult(
                success=False,
                subscription_id="",
                message=result["message"],
                unsubscribe_code=""
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/unsubscribe", response_model=NewsletterUnsubscribeResult)
async def unsubscribe_from_newsletter(
    payload: NewsletterUnsubscribePayload,
    newsletter_service = Depends(get_newsletter_service)
) -> NewsletterUnsubscribeResult:
    """Unsubscribe from a newsletter using subscription code"""
    
    try:
        result = await newsletter_service.unsubscribe_from_newsletter(
            subscription_code=payload.subscription_code
        )
        
        return NewsletterUnsubscribeResult(
            success=result["success"],
            message=result["message"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subscriptions/{user_id}", response_model=GetNewsletterSubscriptionsResult)
async def get_newsletter_subscriptions(
    user_id: str,
    newsletter_service = Depends(get_newsletter_service)
) -> GetNewsletterSubscriptionsResult:
    """Get all newsletter subscriptions for a user"""
    
    try:
        subscriptions = await newsletter_service.get_user_subscriptions(user_id)
        
        return GetNewsletterSubscriptionsResult(
            success=True,
            subscriptions=subscriptions,
            total_count=len(subscriptions)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-link")
async def create_subscription_link(
    user_id: str,
    privacy_level: VisibilityCategoryType,
    newsletter_service = Depends(get_newsletter_service)
) -> Dict[str, str]:
    """Create a subscription link for a specific privacy level"""
    
    try:
        link = await newsletter_service.create_subscription_link(user_id, privacy_level)
        return {"link": link}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/link/{link_code}")
async def get_subscription_info(
    link_code: str,
    newsletter_service = Depends(get_newsletter_service)
) -> Dict[str, Any]:
    """Get subscription information from a link code"""
    
    try:
        privacy_info = await newsletter_service.newsletter_repo.get_privacy_level_by_code(link_code)
        
        if not privacy_info:
            raise HTTPException(status_code=404, detail="Invalid subscription link")
        
        return {
            "username": privacy_info["username"],
            "privacy_level": privacy_info["privacy_level"],
            "available_frequencies": [freq.value for freq in NewsletterFrequency]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Admin/cron endpoints (should be secured in production)
@router.post("/admin/send-daily")
async def send_daily_newsletters(
    newsletter_service = Depends(get_newsletter_service)
) -> Dict[str, Any]:
    """Send all daily newsletters (for cron job)"""
    
    try:
        result = await newsletter_service.send_newsletters_by_frequency(NewsletterFrequency.DAILY)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/send-weekly")
async def send_weekly_newsletters(
    newsletter_service = Depends(get_newsletter_service)
) -> Dict[str, Any]:
    """Send all weekly newsletters (for cron job)"""
    
    try:
        result = await newsletter_service.send_newsletters_by_frequency(NewsletterFrequency.WEEKLY)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/send-monthly")
async def send_monthly_newsletters(
    newsletter_service = Depends(get_newsletter_service)
) -> Dict[str, Any]:
    """Send all monthly newsletters (for cron job)"""
    
    try:
        result = await newsletter_service.send_newsletters_by_frequency(NewsletterFrequency.MONTHLY)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
