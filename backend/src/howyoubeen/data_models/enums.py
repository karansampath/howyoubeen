from enum import Enum


class VisibilityCategoryType(str, Enum):
    """How private/public information is categorized"""
    CLOSE_FAMILY = "close_family"
    BEST_FRIENDS = "best_friends"
    GOOD_FRIENDS = "good_friends"
    ACQUAINTANCES = "acquaintances"
    PUBLIC = "public"
    PRIVATE = "private"
    CUSTOM = "custom"


class ContentType(str, Enum):
    """Types of content that can be uploaded or shared"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    LINK = "link"
    AUDIO = "audio"
    DOCUMENT = "document"


class NewsletterFrequency(str, Enum):
    """Newsletter delivery frequency options"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class SubscriptionStatus(str, Enum):
    """Newsletter subscription status"""
    ACTIVE = "active"
    PAUSED = "paused"
    UNSUBSCRIBED = "unsubscribed"


