"""Chat API routes for AI conversations with friends"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime

from ...storage.storage_factory import get_storage_service, StorageService
from ...data_models.api_models import ChatResponse

router = APIRouter()


class ChatMessageRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


def get_storage() -> StorageService:
    """Get storage service dependency"""
    return get_storage_service()


@router.post("/chat/{username}", response_model=ChatResponse)
async def send_message(
    username: str,
    request: ChatMessageRequest,
    storage: StorageService = Depends(get_storage)
) -> ChatResponse:
    """Send a message to user's AI and get response"""
    try:
        # First verify user exists
        user = await storage.get_user_by_username(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or f"conv_{uuid.uuid4().hex[:8]}"
        
        # For now, generate a simple AI response based on user data
        # In production, this would use a proper AI service with the user's data
        user_dict = user.__dict__ if hasattr(user, '__dict__') else dict(user)
        full_name = user_dict.get("full_name", username)
        bio = user_dict.get("bio", "")
        
        # Generate contextual response based on the question
        message_lower = request.message.lower()
        
        if any(word in message_lower for word in ["hello", "hi", "hey", "how are you"]):
            response_text = f"Hi! I'm {full_name}'s AI assistant. I can tell you about their recent activities and updates. What would you like to know?"
        elif any(word in message_lower for word in ["doing", "up to", "lately", "recent"]):
            response_text = f"Based on what I know about {full_name}, they've been keeping busy with various projects and activities. {bio} What specific aspect of their life are you curious about?"
        elif any(word in message_lower for word in ["work", "job", "project"]):
            response_text = f"I can share information about {full_name}'s professional activities. They're always working on interesting projects. Is there something specific you'd like to know about their work?"
        elif any(word in message_lower for word in ["hobby", "interest", "free time"]):
            response_text = f"Outside of work, {full_name} has various interests and hobbies. {bio} Would you like to know more about any particular interest?"
        else:
            response_text = f"That's an interesting question about {full_name}! Based on their recent updates and activities, I'd say they've been focusing on personal growth and various projects. What specifically would you like to know more about?"
        
        # Generate contextual suggested questions
        suggested_questions = [
            f"What has {full_name} been working on lately?",
            f"How is {full_name} doing?",
            f"Tell me about {full_name}'s recent interests",
            "What's new in their life?"
        ]
        
        # Store conversation (simplified - in production would store full conversation)
        # For now, just log that a conversation happened
        print(f"Chat conversation {conversation_id}: {username} received message: {request.message}")
        
        return ChatResponse(
            response=response_text,
            conversation_id=conversation_id,
            suggested_questions=suggested_questions
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")


@router.get("/chat/{username}/suggestions")
async def get_suggested_questions(
    username: str,
    storage: StorageService = Depends(get_storage)
) -> Dict[str, List[str]]:
    """Get suggested questions for chatting with user's AI"""
    try:
        # Verify user exists
        user = await storage.get_user_by_username(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_dict = user.__dict__ if hasattr(user, '__dict__') else dict(user)
        full_name = user_dict.get("full_name", username)
        
        suggestions = [
            f"How has {full_name} been doing lately?",
            f"What's {full_name} working on these days?",
            f"Tell me about {full_name}'s recent activities",
            f"What are {full_name}'s current interests?",
            "Any recent updates or achievements?",
            "What's new in their life?"
        ]
        
        return {"suggestions": suggestions}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting suggestions: {str(e)}")
