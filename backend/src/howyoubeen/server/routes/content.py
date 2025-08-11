"""
Content API routes for managing life events and life facts
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4
import os
import logging

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import anthropic

from ...storage.storage_factory import get_storage_service
from ...storage.storage_service import StorageService

router = APIRouter(prefix="/content", tags=["content"])

logger = logging.getLogger(__name__)

# Initialize Anthropic client
anthropic_client = None
if os.getenv("ANTHROPIC_API_KEY"):
    anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
else:
    logger.warning("ANTHROPIC_API_KEY not set - chat functionality will be disabled")


# Request Models
class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatQuestionRequest(BaseModel):
    user_id: str
    question: str
    conversation_history: List[ChatMessage] = Field(default_factory=list)
    max_tokens: int = 1000


class ChatQuestionResponse(BaseModel):
    response: str
    conversation_id: str
    suggested_questions: List[str] = Field(default_factory=list)


class LifeEventRequest(BaseModel):
    user_id: str
    summary: str
    start_date: Optional[str] = None  # ISO format datetime
    end_date: Optional[str] = None    # ISO format datetime
    visibility: str = "friends_only"
    associated_docs: List[str] = Field(default_factory=list)


class LifeFactRequest(BaseModel):
    user_id: str
    summary: str
    category: Optional[str] = None
    visibility: str = "friends_only"
    associated_docs: List[str] = Field(default_factory=list)


class NewsletterConfigRequest(BaseModel):
    user_id: str
    name: str
    description: Optional[str] = None
    frequency: str = "weekly"  # daily, weekly, monthly
    privacy_level: str = "friends_only"
    is_active: bool = True


# Response Models
class LifeEventResponse(BaseModel):
    event_id: str
    user_id: str
    summary: str
    start_date: str
    end_date: Optional[str]
    visibility: str
    associated_docs: List[str]
    created_at: str
    updated_at: str


class LifeFactResponse(BaseModel):
    fact_id: str
    user_id: str
    summary: str
    category: Optional[str]
    visibility: str
    associated_docs: List[str]
    created_at: str
    updated_at: str


class NewsletterConfigResponse(BaseModel):
    config_id: str
    user_id: str
    name: str
    description: Optional[str]
    frequency: str
    privacy_level: str
    is_active: bool
    created_at: str
    updated_at: str


# Dependencies
async def get_storage() -> StorageService:
    """Get storage service instance"""
    return get_storage_service()


# Life Event Endpoints
@router.post("/life-events", response_model=LifeEventResponse)
async def create_life_event(
    request: LifeEventRequest,
    storage: StorageService = Depends(get_storage)
) -> Dict:
    """Create a new life event"""
    try:
        # Prepare event data
        event_data = {
            "user_id": request.user_id,
            "summary": request.summary,
            "start_date": request.start_date or datetime.now().isoformat(),
            "end_date": request.end_date,
            "visibility": request.visibility,
            "associated_docs": request.associated_docs
        }
        
        # Create the life event
        event = await storage.create_life_event(event_data)
        
        return event
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create life event: {str(e)}")


@router.get("/life-events/{user_id}", response_model=List[LifeEventResponse])
async def get_user_life_events(
    user_id: str,
    limit: int = 50,
    offset: int = 0,
    storage: StorageService = Depends(get_storage)
) -> List[Dict]:
    """Get life events for a user"""
    try:
        events = await storage.get_life_events_for_user(user_id, limit=limit, offset=offset)
        return events
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get life events: {str(e)}")


@router.get("/life-events/{user_id}/date-range", response_model=List[LifeEventResponse])
async def get_life_events_by_date_range(
    user_id: str,
    start_date: str,
    end_date: str,
    visibility_levels: Optional[str] = None,
    storage: StorageService = Depends(get_storage)
) -> List[Dict]:
    """Get life events for a user within a date range"""
    try:
        # Parse dates
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Parse visibility levels
        visibility_list = None
        if visibility_levels:
            visibility_list = visibility_levels.split(',')
        
        events = await storage.get_life_events_by_date_range(
            user_id=user_id,
            start_date=start_dt,
            end_date=end_dt,
            visibility_levels=visibility_list
        )
        
        return events
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get life events: {str(e)}")


# Life Fact Endpoints
@router.post("/life-facts", response_model=LifeFactResponse)
async def create_life_fact(
    request: LifeFactRequest,
    storage: StorageService = Depends(get_storage)
) -> Dict:
    """Create a new life fact"""
    try:
        # Prepare fact data
        fact_data = {
            "user_id": request.user_id,
            "summary": request.summary,
            "category": request.category,
            "visibility": request.visibility,
            "associated_docs": request.associated_docs
        }
        
        # Create the life fact
        fact = await storage.create_life_fact(fact_data)
        
        return fact
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create life fact: {str(e)}")


@router.get("/life-facts/{user_id}", response_model=List[LifeFactResponse])
async def get_user_life_facts(
    user_id: str,
    category: Optional[str] = None,
    storage: StorageService = Depends(get_storage)
) -> List[Dict]:
    """Get life facts for a user"""
    try:
        facts = await storage.get_life_facts_for_user(user_id, category=category)
        return facts
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get life facts: {str(e)}")


# Newsletter Configuration Endpoints
@router.post("/newsletter-configs", response_model=NewsletterConfigResponse)
async def create_newsletter_config(
    request: NewsletterConfigRequest,
    storage: StorageService = Depends(get_storage)
) -> Dict:
    """Create a new newsletter configuration"""
    try:
        # Prepare config data
        config_id = str(uuid4())
        config_data = {
            "config_id": config_id,
            "user_id": request.user_id,
            "name": request.name,
            "description": request.description,
            "frequency": request.frequency,
            "privacy_level": request.privacy_level,
            "is_active": request.is_active,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # For now, store in user data (extend storage service later for newsletter configs)
        # This is a placeholder implementation
        config = config_data
        
        return config
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create newsletter config: {str(e)}")


@router.get("/newsletter-configs/{user_id}", response_model=List[NewsletterConfigResponse])
async def get_user_newsletter_configs(
    user_id: str,
    storage: StorageService = Depends(get_storage)
) -> List[Dict]:
    """Get newsletter configurations for a user"""
    try:
        # Placeholder implementation - would extend storage service for newsletter configs
        configs = []
        return configs
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get newsletter configs: {str(e)}")


# Search and Query Endpoints
@router.get("/search/{user_id}")
async def search_user_content(
    user_id: str,
    query: str,
    content_types: Optional[str] = None,
    storage: StorageService = Depends(get_storage)
) -> Dict:
    """Search across user's content"""
    try:
        # Parse content types
        types_list = None
        if content_types:
            types_list = content_types.split(',')
        
        results = await storage.search_user_content(
            user_id=user_id,
            query=query,
            content_types=types_list
        )
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/activity-summary/{user_id}")
async def get_user_activity_summary(
    user_id: str,
    days: int = 30,
    storage: StorageService = Depends(get_storage)
) -> Dict:
    """Get user activity summary"""
    try:
        summary = await storage.get_user_activity_summary(user_id, days=days)
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get activity summary: {str(e)}")


# AI Chat/Question Endpoint
@router.post("/question", response_model=ChatQuestionResponse)
async def ask_question(
    request: ChatQuestionRequest,
    storage: StorageService = Depends(get_storage)
) -> Dict:
    """Ask a question about the user using AI with their life context"""
    try:
        if not anthropic_client:
            raise HTTPException(status_code=503, detail="AI service not available - ANTHROPIC_API_KEY not configured")
        
        # Get user data
        user = await storage.get_user(request.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Retrieve user's life events and facts for context
        life_events = await storage.get_life_events_for_user(request.user_id, limit=100)
        life_facts = await storage.get_life_facts_for_user(request.user_id)
        
        # Build context for the AI
        context_sections = []
        
        # User profile info
        user_info = f"User: {user.get('full_name', user.get('username', 'Unknown'))}"
        if user.get('bio'):
            user_info += f"\nBio: {user['bio']}"
        context_sections.append(user_info)
        
        # Life events context
        if life_events:
            events_context = "Recent Life Events:\n"
            for event in life_events[:20]:  # Limit to most recent 20 events
                event_text = f"- {event.get('summary', 'No summary')}"
                if event.get('start_date'):
                    try:
                        event_date = datetime.fromisoformat(event['start_date'].replace('Z', '+00:00'))
                        event_text += f" ({event_date.strftime('%Y-%m-%d')})"
                    except:
                        pass
                events_context += event_text + "\n"
            context_sections.append(events_context)
        
        # Life facts context
        if life_facts:
            facts_context = "Life Facts & Background:\n"
            for fact in life_facts[:30]:  # Limit to 30 facts
                fact_text = f"- {fact.get('summary', 'No summary')}"
                if fact.get('category'):
                    fact_text += f" (Category: {fact['category']})"
                facts_context += fact_text + "\n"
            context_sections.append(facts_context)
        
        # Build the full prompt
        context = "\n\n".join(context_sections)
        
        # Build conversation history
        messages = []
        
        # System message with context
        system_prompt = f"""You are an AI assistant representing this user in conversations with their friends and family. Answer questions about the user based on the provided context.

Keep responses natural, friendly, and personal. If you don't have specific information about something, say so politely rather than making things up.

User Context:
{context}

Instructions:
- Answer as if you're speaking on behalf of the user
- Be conversational and natural
- Use the life events and facts to provide detailed, personal responses
- If asked about something not in the context, politely say you don't have that information
- Keep responses concise but informative"""
        
        messages.append({
            "role": "system",
            "content": system_prompt
        })
        
        # Add conversation history
        for msg in request.conversation_history:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Add the current question
        messages.append({
            "role": "user", 
            "content": request.question
        })
        
        # Call Anthropic API
        response = anthropic_client.messages.create(
            model="claude-3-haiku-20240307",  # Using Haiku for faster/cheaper responses
            max_tokens=request.max_tokens,
            temperature=0.7,
            messages=messages
        )
        
        ai_response = response.content[0].text
        
        # Generate suggested follow-up questions
        suggested_questions = [
            "What else has been happening lately?",
            "Tell me more about recent projects or interests",
            "How are things going overall?"
        ]
        
        # Try to generate more personalized suggestions based on the context
        if life_events:
            recent_event = life_events[0]
            if recent_event.get('summary'):
                suggested_questions.insert(0, f"Tell me more about {recent_event['summary'][:50]}...")
        
        conversation_id = str(uuid4())
        
        return {
            "response": ai_response,
            "conversation_id": conversation_id,
            "suggested_questions": suggested_questions[:3]  # Limit to 3 suggestions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in AI chat: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process question: {str(e)}")