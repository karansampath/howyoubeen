"""
Newsletter Generator Service

Generates personalized newsletters using LLM based on NewsletterConfig and LifeEvent data.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from litellm import completion
from pydantic import BaseModel

from ..data_models.models import NewsletterConfig, LifeEvent, VisibilityCategory
from ..data_models.enums import VisibilityCategoryType
from ..storage.storage_service import StorageService

logger = logging.getLogger(__name__)

DEFAULT_NEWSLETTER_CONFIG = NewsletterConfig(
    instructions="Summarize the major life events of the past week as you would to friends.",
    periodicity=168, 
    name="Default", 
    start_date=None,
    visibility=[VisibilityCategory(type=VisibilityCategoryType.GOOD_FRIENDS)]
)

class NewsletterGenerationRequest(BaseModel):
    """Request payload for newsletter generation"""
    user_id: str
    newsletter_config: NewsletterConfig
    

class NewsletterGenerationResult(BaseModel):
    """Result of newsletter generation"""
    success: bool
    content: Optional[str] = None
    error_message: Optional[str] = None
    events_count: int = 0
    generation_summary: Dict[str, Any] = {}


class NewsletterGenerator:
    """Generates personalized newsletters using LLM"""
    
    def __init__(self, storage_service: StorageService):
        """
        Initialize the newsletter generator
        
        Args:
            storage_service: Storage service for data retrieval
        """
        self.storage_service = storage_service
        
        # Get LLM configuration from environment
        self.default_model = os.getenv("NEWSLETTER_LLM_MODEL", "claude-sonnet-4-20250514")
        self.temperature = float(os.getenv("NEWSLETTER_LLM_TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("NEWSLETTER_LLM_MAX_TOKENS", "2000"))
        
        logger.info(f"Newsletter generator initialized with model: {self.default_model}")
    
    async def generate_newsletter(
        self, 
        user_id: str, 
        newsletter_config: NewsletterConfig = None
    ) -> NewsletterGenerationResult:
        """
        Generate a newsletter based on user's life events and configuration
        
        Args:
            user_id: User ID to generate newsletter for
            newsletter_config: Configuration specifying instructions, periodicity, etc.
            
        Returns:
            NewsletterGenerationResult with generated content or error
        """
        try:
            logger.info(f"Generating newsletter for user {user_id} with config: {newsletter_config.name}")
            if not newsletter_config:
                newsletter_config = DEFAULT_NEWSLETTER_CONFIG
            # Calculate date range based on periodicity
            end_date = datetime.now()
            start_date = end_date - timedelta(hours=newsletter_config.periodicity)
            
            logger.info(f"Querying life events from {start_date} to {end_date}")
            
            # Extract visibility level types for filtering
            visibility_levels = []
            for vc in newsletter_config.visibility:
                if hasattr(vc.type, 'value'):
                    visibility_levels.append(vc.type.value)
                else:
                    visibility_levels.append(str(vc.type))
            
            # Debug logging can be enabled for troubleshooting
            # print(f"🔍 Newsletter Debug: Querying events from {start_date} to {end_date}")
            # print(f"🔍 Newsletter Debug: Visibility levels: {visibility_levels}")
            
            # Get life events within the date range
            life_events = await self.storage_service.get_life_events_by_date_range(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                visibility_levels=visibility_levels
            )
            
            logger.info(f"Found {len(life_events)} life events in date range")
            
            # Get user info for context
            user_data = await self.storage_service.get_user(user_id)
            if not user_data:
                return NewsletterGenerationResult(
                    success=False,
                    error_message="User not found",
                    events_count=0
                )
            
            # Generate newsletter content using LLM
            content = await self._generate_content_with_llm(
                user_data=user_data,
                life_events=life_events,
                newsletter_config=newsletter_config,
                date_range=(start_date, end_date)
            )
            
            return NewsletterGenerationResult(
                success=True,
                content=content,
                events_count=len(life_events),
                generation_summary={
                    "date_range": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat()
                    },
                    "visibility_levels": visibility_levels,
                    "events_processed": len(life_events),
                    "model_used": self.default_model
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to generate newsletter: {e}")
            return NewsletterGenerationResult(
                success=False,
                error_message=str(e),
                events_count=0
            )
    
    async def _generate_content_with_llm(
        self,
        user_data: Dict[str, Any],
        life_events: List[Dict[str, Any]],
        newsletter_config: NewsletterConfig,
        date_range: tuple[datetime, datetime]
    ) -> str:
        """Generate newsletter content using LLM"""
        
        # Prepare context for the LLM
        start_date, end_date = date_range
        date_range_text = f"{start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}"
        
        # Format life events for the prompt
        events_text = ""
        if life_events:
            events_text = "\n".join([
                f"- {event.get('start_date', 'Unknown date')}: {event.get('summary', 'No summary available')}"
                for event in life_events
            ])
        else:
            events_text = "No life events found in this time period."
        
        # Create the prompt
        system_prompt = f"""You are an AI assistant that creates personalized newsletters. 
You will be given a user's life events and specific instructions for how to format and present them.

Your goal is to create an engaging, personalized newsletter in markdown format that follows the user's instructions.

Key guidelines:
- Use markdown formatting (headers, bold, italic, lists, etc.)
- Be personal and engaging in tone
- Follow the user's specific instructions carefully
- If no events are provided, create a brief, friendly message acknowledging the quiet period
- Keep the newsletter focused and readable
- Include the date range being covered
"""
        
        user_prompt = f"""Please create a newsletter for {user_data.get('full_name', 'the user')} covering the period from {date_range_text}.

User Instructions: {newsletter_config.instructions or 'Create a friendly, engaging newsletter highlighting key life events.'}

Life Events in this period:
{events_text}

User Context:
- Name: {user_data.get('full_name', 'Unknown')}
- Bio: {user_data.get('bio', 'No bio available')}
- Newsletter Name: {newsletter_config.name}

Please generate a well-formatted markdown newsletter following the user's instructions. If there are no life events, create a brief, friendly message acknowledging the quiet period. This is from the user to their friends, frame it in the first person from the user's perspective, and be friendly and engaging."""
        
        try:
            logger.info(f"Calling LLM with model: {self.default_model}")
            
            response = completion(
                model=self.default_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            content = response.choices[0].message.content.strip()
            logger.info(f"Generated newsletter content: {len(content)} characters")
            
            return content
            
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            # Fallback to simple template
            return self._create_fallback_newsletter(
                user_data, life_events, newsletter_config, date_range_text
            )
    
    def _create_fallback_newsletter(
        self,
        user_data: Dict[str, Any],
        life_events: List[Dict[str, Any]],
        newsletter_config: NewsletterConfig,
        date_range_text: str
    ) -> str:
        """Create a simple fallback newsletter when LLM fails"""
        
        name = user_data.get('full_name', 'Friend')
        newsletter_name = newsletter_config.name or 'Life Update'
        
        content = f"# {newsletter_name}\n\n"
        content += f"## Update from {name}\n"
        content += f"*Period: {date_range_text}*\n\n"
        
        if life_events:
            content += "## Recent Happenings\n\n"
            for event in life_events:
                event_date = event.get('start_date', 'Unknown date')
                event_summary = event.get('summary', 'No details available')
                content += f"**{event_date}**: {event_summary}\n\n"
        else:
            content += "## A Quiet Period\n\n"
            content += f"No major events to report during this period, but {name} is still here and doing well!\n\n"
        
        content += "---\n\n"
        content += "*This newsletter was generated automatically. If you have any questions, please reach out!*\n"
        
        return content