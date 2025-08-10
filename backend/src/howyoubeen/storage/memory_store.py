"""
In-memory storage for development and testing

This provides a simple in-memory store for user data during development.
In production, this would be replaced with a proper database.
"""

import asyncio
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..data_models.models import User, Document, InfoSource, VisibilityCategory


class MemoryStore:
    """In-memory storage for development"""
    
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.onboarding_sessions: Dict[str, Dict[str, Any]] = {}
        self.documents: Dict[str, Document] = {}
        self.temp_files_dir = tempfile.mkdtemp(prefix="keepintouch_uploads_")
        
    async def create_onboarding_session(self, user_id: str) -> str:
        """Create a new onboarding session"""
        session_id = str(uuid4())
        self.onboarding_sessions[session_id] = {
            "user_id": user_id,
            "step": "start",
            "data": {},
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        return session_id
    
    async def get_onboarding_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get onboarding session by ID"""
        return self.onboarding_sessions.get(session_id)
    
    async def update_onboarding_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Update onboarding session data"""
        if session_id not in self.onboarding_sessions:
            return False
        
        session = self.onboarding_sessions[session_id]
        session["data"].update(data)
        session["updated_at"] = datetime.now()
        return True
    
    async def set_onboarding_step(self, session_id: str, step: str) -> bool:
        """Set the current onboarding step"""
        if session_id not in self.onboarding_sessions:
            return False
        
        self.onboarding_sessions[session_id]["step"] = step
        self.onboarding_sessions[session_id]["updated_at"] = datetime.now()
        return True
    
    async def create_user(self, user_data: Dict[str, Any]) -> User:
        """Create a new user"""
        user = User(**user_data)
        self.users[user.user_id] = user
        return user
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.users.get(user_id)
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        for user in self.users.values():
            if user.username == username:
                return user
        return None
    
    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user data"""
        if user_id not in self.users:
            return False
        
        user = self.users[user_id]
        for key, value in updates.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        user.updated_at = datetime.now()
        return True
    
    async def save_uploaded_file(self, file_content: bytes, filename: str) -> str:
        """Save uploaded file and return file path"""
        file_id = str(uuid4())
        file_ext = os.path.splitext(filename)[1]
        file_path = os.path.join(self.temp_files_dir, f"{file_id}{file_ext}")
        
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        return file_path
    
    async def create_document(self, document_data: Dict[str, Any]) -> Document:
        """Create a document record"""
        document = Document(**document_data)
        self.documents[document.document_id] = document
        return document
    
    async def get_documents_for_user(self, user_id: str) -> List[Document]:
        """Get all documents for a user"""
        user = await self.get_user(user_id)
        if not user:
            return []
        
        # Collect documents from diary entries and facts
        document_ids = []
        for entry in user.diary_entries:
            document_ids.extend([doc.document_id for doc in entry.associated_docs])
        
        for fact in user.facts:
            document_ids.extend([doc.document_id for doc in fact.associated_docs])
        
        return [self.documents[doc_id] for doc_id in document_ids if doc_id in self.documents]
    
    async def get_all_users(self) -> List[User]:
        """Get all users (for development/testing)"""
        return list(self.users.values())
    
    def cleanup(self):
        """Clean up temporary files"""
        import shutil
        if os.path.exists(self.temp_files_dir):
            shutil.rmtree(self.temp_files_dir)


# Global instance for development
store = MemoryStore()