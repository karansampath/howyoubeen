"""
Chat API routes for user profile conversations
"""

from typing import Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from ...storage.storage_factory import get_storage_service
from ...storage.storage_service import StorageService

router = APIRouter(prefix="/api/chat", tags=["chat"])


# Request Models
class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    conversation_history: List[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    suggested_questions: List[str] = Field(default_factory=list)


# Dependencies
async def get_storage() -> StorageService:
    """Get storage service instance"""
    return get_storage_service()


@router.post("/{username}", response_model=ChatResponse)
async def chat_with_user(
    username: str,
    request: ChatRequest,
    storage: StorageService = Depends(get_storage)
) -> Dict:
    """Chat with a user's AI assistant using their username"""
    try:
        # Get user by username
        user = await storage.get_user_by_username(username)
        if not user:
            raise HTTPException(status_code=404, detail=f"User '{username}' not found")
        
        user_id = user.get('id') or user.get('user_id')
        if not user_id:
            raise HTTPException(status_code=500, detail="User ID not found")
        
        # Forward to the content question endpoint logic
        from .content import ChatQuestionRequest, ask_question
        
        # Convert chat history format
        conversation_history = []
        for msg in request.conversation_history:
            conversation_history.append({
                "role": msg.role,
                "content": msg.content
            })
        
        question_request = ChatQuestionRequest(
            user_id=user_id,
            question=request.message,
            conversation_history=conversation_history
        )
        
        # Use the content endpoint logic
        response = await ask_question(question_request, storage)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")