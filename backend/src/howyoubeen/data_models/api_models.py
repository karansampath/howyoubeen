import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Union

from pydantic import BaseModel, Field

from .enums import ContentType, VisibilityCategoryType, NewsletterFrequency


class RequestType(str, Enum):
    """Types of API requests supported by the system"""
    ONBOARDING = "onboarding"
    CHAT = "chat"
    CONTENT_UPLOAD = "content_upload"
    GET_PROFILE = "get_profile"
    ADD_FRIEND = "add_friend"
    UPDATE_FRIEND = "update_friend"
    KNOWLEDGE_UPDATE = "knowledge_update"
    NEWSLETTER_SUBSCRIBE = "newsletter_subscribe"
    NEWSLETTER_UNSUBSCRIBE = "newsletter_unsubscribe"
    GET_NEWSLETTER_SUBSCRIPTIONS = "get_newsletter_subscriptions"


# Specific Request Payloads
class OnboardingPayload(BaseModel):
    """Payload for user onboarding process"""
    user_id: str
    interview_responses: dict[str, str]
    data_sources: list[dict[str, str]] = Field(default_factory=list)
    friendship_tiers: list[dict[str, Any]] = Field(default_factory=list)


class ChatPayload(BaseModel):
    """Payload for friend chat interactions"""
    profile_username: str
    message: str
    requester_info: Optional[dict[str, str]] = None
    conversation_id: Optional[str] = None


class ContentUploadPayload(BaseModel):
    """Payload for uploading user content"""
    user_id: str
    content_type: ContentType
    data: str
    description: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    auto_categorize: bool = True


class GetProfilePayload(BaseModel):
    """Payload for retrieving user profile information"""
    username: str
    requester_info: Optional[dict[str, str]] = None


class AddFriendPayload(BaseModel):
    """Payload for adding a new friend"""
    user_id: str
    friend_email: str
    friend_name: str
    friendship_level: VisibilityCategoryType
    custom_description: Optional[str] = None


class UpdateFriendPayload(BaseModel):
    """Payload for updating friend information"""
    user_id: str
    friend_id: str
    new_friendship_level: Optional[VisibilityCategoryType] = None
    newsletter_subscription: Optional[bool] = None


class KnowledgeUpdatePayload(BaseModel):
    """Payload for updating user knowledge base"""
    user_id: str
    update_type: str
    content: str
    category: Optional[str] = None


class NewsletterSubscribePayload(BaseModel):
    """Payload for subscribing to a newsletter"""
    username: str
    subscriber_email: str
    privacy_code: str  # Encoded privacy level
    frequency: NewsletterFrequency
    subscriber_name: Optional[str] = None


class NewsletterUnsubscribePayload(BaseModel):
    """Payload for unsubscribing from a newsletter"""
    subscription_code: str


class GetNewsletterSubscriptionsPayload(BaseModel):
    """Payload for getting newsletter subscriptions"""
    user_id: str


# Specific Response Results
class OnboardingResult(BaseModel):
    """Result of user onboarding process"""
    success: bool
    profile_url: str
    next_steps: list[str] = Field(default_factory=list)
    ai_summary: str


class ChatResult(BaseModel):
    """Result of friend chat interaction"""
    response: str
    conversation_id: str
    friendship_level_detected: VisibilityCategoryType
    suggested_questions: list[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.8)


class ContentUploadResult(BaseModel):
    """Result of content upload"""
    success: bool
    content_id: str
    ai_summary: str
    updated_knowledge_areas: list[str] = Field(default_factory=list)


class GetProfileResult(BaseModel):
    """Result of profile retrieval"""
    username: str
    display_name: str
    bio: str
    recent_highlights: list[str] = Field(default_factory=list)
    available_time_periods: list[str] = Field(default_factory=list)
    friendship_level: VisibilityCategoryType


class AddFriendResult(BaseModel):
    """Result of adding a friend"""
    success: bool
    friendship_id: str
    message: str


class UpdateFriendResult(BaseModel):
    """Result of updating friend information"""
    success: bool
    updated_fields: list[str] = Field(default_factory=list)
    message: str


class KnowledgeUpdateResult(BaseModel):
    """Result of knowledge base update"""
    success: bool
    updated_summary: str
    affected_responses: list[str] = Field(default_factory=list)


class NewsletterSubscribeResult(BaseModel):
    """Result of newsletter subscription"""
    success: bool
    subscription_id: str
    message: str
    unsubscribe_code: str


class NewsletterUnsubscribeResult(BaseModel):
    """Result of newsletter unsubscription"""
    success: bool
    message: str


class GetNewsletterSubscriptionsResult(BaseModel):
    """Result of getting newsletter subscriptions"""
    success: bool
    subscriptions: list[dict[str, Any]] = Field(default_factory=list)
    total_count: int


# Top-Level Request/Response Models
class APIRequest(BaseModel):
    """Top-level API request structure"""
    request_type: RequestType
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    payload: Union[
        OnboardingPayload,
        ChatPayload,
        ContentUploadPayload,
        GetProfilePayload,
        AddFriendPayload,
        UpdateFriendPayload,
        KnowledgeUpdatePayload,
        NewsletterSubscribePayload,
        NewsletterUnsubscribePayload,
        GetNewsletterSubscriptionsPayload
    ]

    class Config:
        use_enum_values = True


class APIResponse(BaseModel):
    """Top-level API response structure"""
    request_id: str
    success: bool
    timestamp: datetime = Field(default_factory=datetime.now)
    result: Optional[Union[
        OnboardingResult,
        ChatResult,
        ContentUploadResult,
        GetProfileResult,
        AddFriendResult,
        UpdateFriendResult,
        KnowledgeUpdateResult,
        NewsletterSubscribeResult,
        NewsletterUnsubscribeResult,
        GetNewsletterSubscriptionsResult
    ]] = None
    error: Optional[str] = None
    error_code: Optional[str] = None

    class Config:
        use_enum_values = True


# Error Response Models
class ErrorDetail(BaseModel):
    """Detailed error information"""
    field: Optional[str] = None
    message: str
    error_type: str


class ValidationError(BaseModel):
    """Validation error response"""
    message: str = "Validation failed"
    details: list[ErrorDetail] = Field(default_factory=list)


class AuthenticationError(BaseModel):
    """Authentication error response"""
    message: str = "Authentication required"
    required_action: Optional[str] = None


class RateLimitError(BaseModel):
    """Rate limit error response"""
    message: str = "Rate limit exceeded"
    retry_after: Optional[int] = None  # seconds
    limit_type: str = "requests"