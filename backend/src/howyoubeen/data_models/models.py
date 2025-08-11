from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from .enums import ContentType, VisibilityCategoryType, NewsletterFrequency, SubscriptionStatus


def generate_uuid() -> str:
    """Generate a UUID string"""
    return str(uuid4())


class VisibilityCategory(BaseModel):
    """Defines who can see specific information"""
    type: VisibilityCategoryType
    name: Optional[str] = None  # Required if type is CUSTOM
    also_visible: List['VisibilityCategory'] = Field(default_factory=list)

    class Config:
        # Allow forward references for self-referencing models
        use_enum_values = True


class Document(BaseModel):
    """Generic document/content reference"""
    document_id: str = Field(default_factory=generate_uuid)
    url: Optional[str] = None
    file_path: Optional[str] = None
    content_type: ContentType
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class InfoSource(BaseModel):
    """External information source (social media, websites, etc.)"""
    source_id: str = Field(default_factory=generate_uuid)
    url: Optional[str] = None
    platform: str  # e.g., "linkedin", "github", "instagram"
    info_description: str
    last_checked: datetime = Field(default_factory=datetime.now)
    is_active: bool = True


class LifeEvent(BaseModel):
    """A specific life event with a clear date/timeframe"""
    event_id: str = Field(default_factory=generate_uuid)
    visibility: VisibilityCategory
    start_date: datetime
    end_date: Optional[datetime] = None
    summary: str
    associated_docs: List[Document] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class LifeFact(BaseModel):
    """A life fact not associated with a specific time frame"""
    fact_id: str = Field(default_factory=generate_uuid)
    visibility: VisibilityCategory
    date: datetime = Field(default_factory=datetime.now)
    summary: str
    category: Optional[str] = None  # e.g., "preferences", "background", "interests"
    associated_docs: List[Document] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class FriendshipTier(BaseModel):
    """Configuration for different friendship levels"""
    tier_id: str = Field(default_factory=generate_uuid)
    user_id: str
    level: VisibilityCategory
    name: str
    description: str
    sharing_guidelines: str
    sample_responses: Dict[str, str] = Field(default_factory=dict)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)


class Content(BaseModel):
    """User-generated content with AI analysis"""
    content_id: str = Field(default_factory=generate_uuid)
    user_id: str
    content_type: ContentType
    raw_content: str
    ai_extracted_info: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    visibility_levels: List[VisibilityCategory] = Field(default_factory=list)
    knowledge_contribution: List[str] = Field(default_factory=list)
    is_processed: bool = False


class Friend(BaseModel):
    """Friendship relationship and configuration"""
    friendship_id: str = Field(default_factory=generate_uuid)
    owner_user_id: str
    friend_email: str
    friend_name: str
    friendship_level: VisibilityCategory
    relationship_context: Optional[str] = None
    interaction_history: List[Dict[str, Any]] = Field(default_factory=list)
    newsletter_subscribed: bool = False
    added_at: datetime = Field(default_factory=datetime.now)
    last_interaction: Optional[datetime] = None
    is_active: bool = True


class Conversation(BaseModel):
    """Chat conversation between friend and user's AI"""
    conversation_id: str = Field(default_factory=generate_uuid)
    profile_username: str
    friend_identifier: Optional[str] = None  # email or session ID
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    last_message_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True

class NewsletterSubscription(BaseModel):
    """Newsletter subscription for friends"""
    subscription_id: str = Field(default_factory=generate_uuid)
    source_user_id: str  # User whose newsletter this is
    source_username: str  # Username for easy reference
    subscriber_email: str
    privacy_level: VisibilityCategoryType
    frequency: NewsletterFrequency
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    subscription_code: str = Field(default_factory=generate_uuid)  # Unique code for unsubscribe
    last_sent: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class NewsletterConfig(BaseModel):
    """Newsletter generation configuration for users"""
    instructions: Optional[str]
    periodicity: int # every x hours
    start_date: Optional[datetime]
    visibility: List[VisibilityCategory]
    name: str

class User(BaseModel):
    """Main user model with accumulated knowledge"""
    user_id: str = Field(default_factory=generate_uuid)
    username: str
    email: str
    password_hash: Optional[str] = None  # Optional for backward compatibility
    full_name: str
    google_account_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Core Profile
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    is_public: bool = True
    onboarding_completed: bool = False

    # Knowledge Base
    life_events: List[LifeEvent] = Field(default_factory=list)
    facts: List[LifeFact] = Field(default_factory=list)
    sources: List[InfoSource] = Field(default_factory=list)

    newsletters: List[NewsletterConfig] = Field(default_factory=list)
    newsletter_subscriptions: List[NewsletterSubscription] = Field(default_factory=list)  # Subscriptions to this user's newsletter

    # Settings
    friendship_tiers: List[FriendshipTier] = Field(default_factory=list)

    # Metadata
    knowledge_last_updated: datetime = Field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    is_active: bool = True


# Update forward references
VisibilityCategory.model_rebuild()
