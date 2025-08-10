"""User profile routes"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any

from ...storage.storage_factory import get_storage_service, StorageService
from ...data_models.api_models import GetProfileResult

router = APIRouter()


def get_storage() -> StorageService:
    """Get storage service dependency"""
    return get_storage_service()


@router.get("/users/{username}", response_model=Dict[str, Any])
async def get_user_profile(
    username: str,
    storage: StorageService = Depends(get_storage)
) -> Dict[str, Any]:
    """Get user profile by username"""
    try:
        user = await storage.get_user_by_username(username)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Convert user object to dict for response
        if hasattr(user, '__dict__'):
            user_dict = user.__dict__
        else:
            # If it's already a dict from storage
            user_dict = dict(user)
            
        return {
            "user_id": user_dict.get("user_id") or user_dict.get("id"),
            "username": user_dict.get("username"),
            "email": user_dict.get("email"),
            "full_name": user_dict.get("full_name"),
            "bio": user_dict.get("bio", ""),
            "profile_image_url": user_dict.get("profile_image_url"),
            "is_public": user_dict.get("is_public", False),
            "onboarding_completed": user_dict.get("onboarding_completed", False),
            "created_at": user_dict.get("created_at", "").isoformat() if user_dict.get("created_at") else "",
            "knowledge_last_updated": user_dict.get("updated_at", "").isoformat() if user_dict.get("updated_at") else ""
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user: {str(e)}")


@router.get("/users/{user_id}/subscriptions")
async def get_user_subscriptions(
    user_id: str,
    storage: StorageService = Depends(get_storage)
) -> Dict[str, Any]:
    """Get newsletter subscriptions for a user"""
    try:
        # This would typically get subscriptions from the newsletter repository
        # For now, return empty list as the functionality is being built
        return {
            "subscriptions": [],
            "total_count": 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching subscriptions: {str(e)}")
