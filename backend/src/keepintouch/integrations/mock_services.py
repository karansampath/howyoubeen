"""
Mock external service integrations for development

These mock services simulate real integrations with external platforms
like Goodreads, Google Photos, LinkedIn, etc.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..data_models.models import InfoSource, Document
from ..data_models.enums import ContentType


class MockGoodreadsService:
    """Mock Goodreads integration"""
    
    async def connect(self, user_id: str, credentials: Dict[str, str]) -> InfoSource:
        """Mock Goodreads connection"""
        await asyncio.sleep(0.1)  # Simulate API call
        
        return InfoSource(
            platform="goodreads",
            url="https://www.goodreads.com/user/show/12345",
            info_description="Reading list and book reviews",
            last_checked=datetime.now()
        )
    
    async def get_reading_data(self, source: InfoSource) -> List[Dict[str, Any]]:
        """Mock fetching reading data"""
        await asyncio.sleep(0.2)
        
        return [
            {
                "type": "currently_reading",
                "books": ["The Pragmatic Programmer", "Clean Code", "Design Patterns"]
            },
            {
                "type": "favorite_books",
                "books": ["The Lord of the Rings", "Foundation Series", "Dune"]
            },
            {
                "type": "reading_goal",
                "goal": "52 books per year"
            }
        ]


class MockGooglePhotosService:
    """Mock Google Photos integration"""
    
    async def connect(self, user_id: str, credentials: Dict[str, str]) -> InfoSource:
        """Mock Google Photos connection"""
        await asyncio.sleep(0.1)
        
        return InfoSource(
            platform="google_photos",
            url="https://photos.google.com/",
            info_description="Personal photos and memories",
            last_checked=datetime.now()
        )
    
    async def get_recent_photos(self, source: InfoSource, limit: int = 10) -> List[Document]:
        """Mock fetching recent photos"""
        await asyncio.sleep(0.3)
        
        documents = []
        for i in range(min(limit, 5)):  # Return up to 5 mock photos
            documents.append(Document(
                url=f"https://photos.google.com/photo_{i+1}.jpg",
                content_type=ContentType.IMAGE,
                description=f"Recent photo {i+1} from Google Photos"
            ))
        
        return documents


class MockLinkedInService:
    """Mock LinkedIn integration"""
    
    async def connect(self, user_id: str, credentials: Dict[str, str]) -> InfoSource:
        """Mock LinkedIn connection"""
        await asyncio.sleep(0.1)
        
        return InfoSource(
            platform="linkedin",
            url="https://www.linkedin.com/in/username",
            info_description="Professional profile and network",
            last_checked=datetime.now()
        )
    
    async def get_profile_data(self, source: InfoSource) -> Dict[str, Any]:
        """Mock fetching LinkedIn profile data"""
        await asyncio.sleep(0.2)
        
        return {
            "current_position": "Senior Software Engineer at TechCorp",
            "location": "San Francisco, CA",
            "experience": [
                {"title": "Senior Software Engineer", "company": "TechCorp", "years": "2022-present"},
                {"title": "Software Engineer", "company": "StartupInc", "years": "2020-2022"}
            ],
            "education": "BS Computer Science, University of Technology",
            "skills": ["Python", "JavaScript", "Machine Learning", "System Design"]
        }


class MockGitHubService:
    """Mock GitHub integration"""
    
    async def connect(self, user_id: str, credentials: Dict[str, str]) -> InfoSource:
        """Mock GitHub connection"""
        await asyncio.sleep(0.1)
        
        return InfoSource(
            platform="github",
            url="https://github.com/username",
            info_description="Code repositories and projects",
            last_checked=datetime.now()
        )
    
    async def get_repository_data(self, source: InfoSource) -> Dict[str, Any]:
        """Mock fetching GitHub repository data"""
        await asyncio.sleep(0.2)
        
        return {
            "public_repos": 25,
            "top_languages": ["Python", "JavaScript", "TypeScript", "Go"],
            "recent_projects": [
                "AI Chat Application",
                "Personal Finance Tracker", 
                "Recipe Management System"
            ],
            "contribution_activity": "Active contributor with 500+ commits this year"
        }


class MockInstagramService:
    """Mock Instagram integration"""
    
    async def connect(self, user_id: str, credentials: Dict[str, str]) -> InfoSource:
        """Mock Instagram connection"""
        await asyncio.sleep(0.1)
        
        return InfoSource(
            platform="instagram", 
            url="https://www.instagram.com/username",
            info_description="Social photos and lifestyle updates",
            last_checked=datetime.now()
        )
    
    async def get_recent_posts(self, source: InfoSource, limit: int = 10) -> List[Dict[str, Any]]:
        """Mock fetching recent Instagram posts"""
        await asyncio.sleep(0.3)
        
        return [
            {
                "type": "photo",
                "caption": "Beautiful sunset from my weekend hike! 🌅",
                "location": "Golden Gate Park",
                "date": "2024-01-15"
            },
            {
                "type": "photo", 
                "caption": "Trying out a new recipe tonight - homemade pasta! 🍝",
                "date": "2024-01-12"
            },
            {
                "type": "photo",
                "caption": "Great coffee and productive morning at the local cafe ☕",
                "location": "Blue Bottle Coffee",
                "date": "2024-01-10"
            }
        ]


class MockServiceRegistry:
    """Registry for all mock services"""
    
    def __init__(self):
        self.services = {
            "goodreads": MockGoodreadsService(),
            "google_photos": MockGooglePhotosService(),
            "linkedin": MockLinkedInService(),
            "github": MockGitHubService(),
            "instagram": MockInstagramService()
        }
    
    def get_service(self, platform: str):
        """Get service by platform name"""
        return self.services.get(platform)
    
    def get_available_platforms(self) -> List[str]:
        """Get list of available platforms"""
        return list(self.services.keys())


# Global service registry
mock_services = MockServiceRegistry()