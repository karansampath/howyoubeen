"""
KeepInTouch Data Models

This module contains all Pydantic models used throughout the application.
"""

from .api_models import (
    APIRequest,
    APIResponse,
    AddFriendPayload,
    AddFriendResult,
    AuthenticationError,
    ChatPayload,
    ChatResult,
    ContentUploadPayload,
    ContentUploadResult,
    ErrorDetail,
    GetProfilePayload,
    GetProfileResult,
    KnowledgeUpdatePayload,
    KnowledgeUpdateResult,
    OnboardingPayload,
    OnboardingResult,
    RateLimitError,
    RequestType,
    UpdateFriendPayload,
    UpdateFriendResult,
    ValidationError,
)
from .enums import ContentType, VisibilityCategoryType
from .models import (
    Conversation,
    Content,
    LifeEvent,
    Document,
    Friend,
    FriendshipTier,
    InfoSource,
    LifeFact,
    User,
    VisibilityCategory,
)

__all__ = [
    # Enums
    "ContentType",
    "VisibilityCategoryType",
    # Core Models
    "Conversation",
    "Content",
    "LifeEvent", 
    "Document",
    "Friend",
    "FriendshipTier",
    "InfoSource",
    "LifeFact",
    "User",
    "VisibilityCategory",
    # API Models
    "APIRequest",
    "APIResponse", 
    "RequestType",
    # Payloads
    "AddFriendPayload",
    "ChatPayload",
    "ContentUploadPayload",
    "GetProfilePayload",
    "KnowledgeUpdatePayload",
    "OnboardingPayload",
    "UpdateFriendPayload",
    # Results
    "AddFriendResult",
    "ChatResult",
    "ContentUploadResult",
    "GetProfileResult", 
    "KnowledgeUpdateResult",
    "OnboardingResult",
    "UpdateFriendResult",
    # Error Models
    "AuthenticationError",
    "ErrorDetail",
    "RateLimitError",
    "ValidationError",
]