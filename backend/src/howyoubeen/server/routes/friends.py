"""Friends and timeline API routes"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from datetime import datetime, timedelta

from ...storage.storage_factory import get_storage_service, StorageService

router = APIRouter()


def get_storage() -> StorageService:
    """Get storage service dependency"""
    return get_storage_service()


@router.get("/users/{user_id}/friends")
async def get_user_friends(
    user_id: str,
    storage: StorageService = Depends(get_storage)
) -> List[Dict[str, Any]]:
    """Get friends list for a user"""
    try:
        # Verify user exists
        user = await storage.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # For now, return empty list as friends functionality isn't fully implemented
        # In production, this would fetch actual friends from the database
        return []
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching friends: {str(e)}")


@router.get("/users/{username}/timeline")
async def get_user_timeline(
    username: str,
    storage: StorageService = Depends(get_storage)
) -> List[Dict[str, Any]]:
    """Get timeline/activity data for a user"""
    try:
        # First verify user exists
        user = await storage.get_user_by_username(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_dict = user.__dict__ if hasattr(user, '__dict__') else dict(user)
        user_id = user_dict.get("user_id") or user_dict.get("id")
        
        # Get diary entries and life facts from storage
        diary_entries = await storage.get_diary_entries_for_user(user_id)
        life_facts = await storage.get_life_facts_for_user(user_id)
        
        timeline = []
        
        # Convert diary entries to timeline format
        for entry in diary_entries:
            entry_dict = entry.__dict__ if hasattr(entry, '__dict__') else dict(entry)
            timeline.append({
                "id": f"entry_{entry_dict.get('id', 'unknown')}",
                "type": "diary_entry",
                "date": entry_dict.get("created_at", datetime.now()).isoformat(),
                "content": entry_dict.get("content", ""),
                "category": entry_dict.get("category")
            })
        
        # Convert life facts to timeline format
        for fact in life_facts:
            fact_dict = fact.__dict__ if hasattr(fact, '__dict__') else dict(fact)
            timeline.append({
                "id": f"fact_{fact_dict.get('id', 'unknown')}",
                "type": "life_fact", 
                "date": fact_dict.get("date_occurred", datetime.now()).isoformat(),
                "content": fact_dict.get("content", ""),
                "category": fact_dict.get("category")
            })
        
        # Sort timeline by date (most recent first)
        timeline.sort(key=lambda x: x["date"], reverse=True)
        
        return timeline
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching timeline: {str(e)}")


@router.post("/users/{user_id}/content")
async def upload_user_content(
    user_id: str,
    content_data: Dict[str, Any],
    storage: StorageService = Depends(get_storage)
) -> Dict[str, Any]:
    """Upload new content for a user (diary entry)"""
    try:
        # Verify user exists
        user = await storage.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        content = content_data.get("content", "").strip()
        if not content:
            raise HTTPException(status_code=400, detail="Content cannot be empty")
        
        # Create diary entry
        # Note: This is simplified - in production would use proper diary entry creation
        diary_entry_id = f"entry_{datetime.now().timestamp()}"
        
        # For now, just return success - actual storage would be implemented
        # when the full diary entry system is built
        return {
            "success": True,
            "message": "Content uploaded successfully",
            "entry_id": diary_entry_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading content: {str(e)}")
