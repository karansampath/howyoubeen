"""
Local Storage Service Implementation

In-memory storage with local file system for development and prototyping.
"""

import asyncio
import json
import os
import tempfile
import shutil
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4
import logging

from .storage_service import StorageService

logger = logging.getLogger(__name__)


class LocalStorageService(StorageService):
    """Local storage implementation using in-memory data and local filesystem"""
    
    def __init__(self, backup_file: Optional[str] = None, temp_dir: Optional[str] = None):
        """
        Initialize local storage service
        
        Args:
            backup_file: Optional file path for data persistence
            temp_dir: Optional custom temporary directory
        """
        self.backup_file = backup_file
        self.temp_dir = temp_dir or tempfile.mkdtemp(prefix="howyoubeen_")
        
        # In-memory data stores
        self.users: Dict[str, Dict[str, Any]] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.visibility_categories: Dict[str, Dict[str, Any]] = {}
        self.diary_entries: Dict[str, Dict[str, Any]] = {}
        self.life_facts: Dict[str, Dict[str, Any]] = {}
        self.info_sources: Dict[str, Dict[str, Any]] = {}
        
        # Load data from backup if available
        if backup_file and os.path.exists(backup_file):
            self._load_from_backup()
        
        logger.info(f"Local storage initialized with temp dir: {self.temp_dir}")
    
    def _load_from_backup(self):
        """Load data from backup file"""
        try:
            with open(self.backup_file, 'r') as f:
                content = f.read().strip()
                
            # Handle empty file
            if not content:
                logger.info(f"Empty backup file: {self.backup_file}")
                return
                
            data = json.loads(content)
            
            self.users = data.get('users', {})
            self.sessions = data.get('sessions', {})
            self.documents = data.get('documents', {})
            self.visibility_categories = data.get('visibility_categories', {})
            self.diary_entries = data.get('diary_entries', {})
            self.life_facts = data.get('life_facts', {})
            self.info_sources = data.get('info_sources', {})
            
            logger.info(f"Loaded data from backup: {self.backup_file}")
            
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in backup file: {e}")
        except Exception as e:
            logger.warning(f"Failed to load backup file: {e}")
    
    def _save_to_backup(self):
        """Save data to backup file"""
        if not self.backup_file:
            return
        
        try:
            # Create backup directory if needed  
            backup_dir = os.path.dirname(self.backup_file)
            if backup_dir:
                os.makedirs(backup_dir, exist_ok=True)
            
            data = {
                'users': self.users,
                'sessions': self.sessions,
                'documents': self.documents,
                'visibility_categories': self.visibility_categories,
                'diary_entries': self.diary_entries,
                'life_facts': self.life_facts,
                'info_sources': self.info_sources
            }
            
            with open(self.backup_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.debug(f"Saved data to backup: {self.backup_file}")
            
        except Exception as e:
            logger.error(f"Failed to save backup file: {e}")
    
    # User Management
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user"""
        # Check for existing username
        if await self.username_exists(user_data.get("username", "")):
            raise ValueError(f"Username '{user_data['username']}' already exists")
        
        # Check for existing email
        if await self.email_exists(user_data.get("email", "")):
            raise ValueError(f"Email '{user_data['email']}' already exists")
        
        user_id = str(uuid4())
        user = {
            **user_data,
            "id": user_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self.users[user_id] = user
        self._save_to_backup()
        
        logger.info(f"Created user: {user_id}")
        return user
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        return self.users.get(user_id)
    
    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        for user in self.users.values():
            if user.get("username") == username:
                return user
        return None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        for user in self.users.values():
            if user.get("email") == email:
                return user
        return None
    
    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user data"""
        if user_id not in self.users:
            return False
        
        # Check username/email conflicts if updating them
        if "username" in updates:
            existing = await self.get_user_by_username(updates["username"])
            if existing and existing["id"] != user_id:
                raise ValueError(f"Username '{updates['username']}' already exists")
        
        if "email" in updates:
            existing = await self.get_user_by_email(updates["email"])
            if existing and existing["id"] != user_id:
                raise ValueError(f"Email '{updates['email']}' already exists")
        
        self.users[user_id].update(updates)
        self.users[user_id]["updated_at"] = datetime.now().isoformat()
        self._save_to_backup()
        
        logger.info(f"Updated user: {user_id}")
        return True
    
    async def username_exists(self, username: str) -> bool:
        """Check if username exists"""
        user = await self.get_user_by_username(username)
        return user is not None
    
    async def email_exists(self, email: str) -> bool:
        """Check if email exists"""
        user = await self.get_user_by_email(email)
        return user is not None
    
    # Onboarding Session Management
    async def create_onboarding_session(self, user_id: Optional[str] = None) -> str:
        """Create a new onboarding session"""
        session_id = str(uuid4())
        session = {
            "id": session_id,
            "user_id": user_id,
            "step": "start",
            "data": {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self.sessions[session_id] = session
        self._save_to_backup()
        
        logger.info(f"Created onboarding session: {session_id}")
        return session_id
    
    async def update_onboarding_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Update onboarding session data"""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        session["data"].update(data)
        session["updated_at"] = datetime.now().isoformat()
        self._save_to_backup()
        
        return True
    
    async def get_onboarding_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get onboarding session data"""
        return self.sessions.get(session_id)
    
    async def set_onboarding_step(self, session_id: str, step: str) -> bool:
        """Set onboarding step"""
        if session_id not in self.sessions:
            return False
        
        self.sessions[session_id]["step"] = step
        self.sessions[session_id]["updated_at"] = datetime.now().isoformat()
        self._save_to_backup()
        
        return True
    
    async def set_onboarding_user_id(self, session_id: str, user_id: str) -> bool:
        """Set user ID for session"""
        if session_id not in self.sessions:
            return False
        
        self.sessions[session_id]["user_id"] = user_id
        self.sessions[session_id]["updated_at"] = datetime.now().isoformat()
        self._save_to_backup()
        
        return True
    
    # File Management
    async def save_file(self, user_id: str, file_content: bytes, filename: str, 
                       description: str = "") -> Dict[str, Any]:
        """Save a file for a user"""
        # Create user directory
        user_dir = os.path.join(self.temp_dir, user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        # Generate unique filename
        file_id = str(uuid4())
        _, ext = os.path.splitext(filename)
        file_path = os.path.join(user_dir, f"{file_id}{ext}")
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        return {
            "file_path": file_path,
            "original_filename": filename,
            "file_size": len(file_content),
            "description": description
        }
    
    async def get_file_url(self, file_path: str, expires_in: int = 3600) -> Optional[str]:
        """Get URL for accessing a file (local file path for local storage)"""
        if os.path.exists(file_path):
            return f"file://{file_path}"
        return None
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete a file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
        
        return False
    
    # Document Metadata Management
    async def create_document(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create document metadata record"""
        doc_id = str(uuid4())
        document = {
            **document_data,
            "id": doc_id,
            "created_at": datetime.now().isoformat()
        }
        
        self.documents[doc_id] = document
        self._save_to_backup()
        
        return document
    
    async def get_documents_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all documents for a user"""
        return [
            doc for doc in self.documents.values() 
            if doc.get("user_id") == user_id
        ]
    
    # Visibility Categories
    async def create_visibility_categories(self, user_id: str, 
                                          categories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create visibility categories for a user"""
        created_categories = []
        
        for cat_data in categories:
            cat_id = str(uuid4())
            category = {
                **cat_data,
                "id": cat_id,
                "user_id": user_id,
                "created_at": datetime.now().isoformat()
            }
            
            self.visibility_categories[cat_id] = category
            created_categories.append(category)
        
        self._save_to_backup()
        return created_categories
    
    async def get_visibility_categories(self, user_id: str) -> List[Dict[str, Any]]:
        """Get visibility categories for a user"""
        return [
            cat for cat in self.visibility_categories.values()
            if cat.get("user_id") == user_id
        ]
    
    # User Content
    async def create_diary_entry(self, entry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a diary entry"""
        entry_id = str(uuid4())
        entry = {
            **entry_data,
            "id": entry_id,
            "created_at": datetime.now().isoformat()
        }
        
        self.diary_entries[entry_id] = entry
        self._save_to_backup()
        
        return entry
    
    async def create_life_fact(self, fact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a life fact"""
        fact_id = str(uuid4())
        fact = {
            **fact_data,
            "id": fact_id,
            "created_at": datetime.now().isoformat()
        }
        
        self.life_facts[fact_id] = fact
        self._save_to_backup()
        
        return fact
    
    async def create_info_source(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an info source record"""
        source_id = str(uuid4())
        source = {
            **source_data,
            "id": source_id,
            "created_at": datetime.now().isoformat()
        }
        
        self.info_sources[source_id] = source
        self._save_to_backup()
        
        return source
    
    # Health and Diagnostics
    async def health_check(self) -> Dict[str, Any]:
        """Check storage service health"""
        return {
            "status": "healthy",
            "backend": "local",
            "temp_dir": self.temp_dir,
            "backup_file": self.backup_file,
            "data_counts": {
                "users": len(self.users),
                "sessions": len(self.sessions),
                "documents": len(self.documents),
                "visibility_categories": len(self.visibility_categories),
                "diary_entries": len(self.diary_entries),
                "life_facts": len(self.life_facts),
                "info_sources": len(self.info_sources)
            }
        }
    
    async def get_storage_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get storage usage statistics"""
        if user_id:
            user_docs = await self.get_documents_for_user(user_id)
            user_dir = os.path.join(self.temp_dir, user_id)
            
            total_size = 0
            if os.path.exists(user_dir):
                for root, dirs, files in os.walk(user_dir):
                    total_size += sum(
                        os.path.getsize(os.path.join(root, file)) 
                        for file in files
                    )
            
            return {
                "user_id": user_id,
                "documents_count": len(user_docs),
                "total_size_bytes": total_size,
                "total_size_mb": total_size / (1024 * 1024) if total_size > 0 else 0
            }
        else:
            return {
                "backend": "local",
                "total_users": len(self.users),
                "total_documents": len(self.documents),
                "total_sessions": len(self.sessions)
            }
    
    # Cleanup Operations
    async def cleanup_expired_sessions(self, hours_old: int = 24) -> int:
        """Clean up expired onboarding sessions"""
        cutoff_time = datetime.now() - timedelta(hours=hours_old)
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            created_at = datetime.fromisoformat(session["created_at"])
            if created_at < cutoff_time:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        if expired_sessions:
            self._save_to_backup()
        
        logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        return len(expired_sessions)
    
    def cleanup(self):
        """Clean up temporary files and save backup"""
        try:
            self._save_to_backup()
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temp directory: {self.temp_dir}")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    # Query Methods
    async def get_diary_entries_for_user(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get diary entries for a user"""
        entries = [
            entry for entry in self.diary_entries.values()
            if entry.get("user_id") == user_id
        ]
        
        # Sort by created_at descending
        entries.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        # Apply pagination
        return entries[offset:offset + limit]
    
    async def get_life_facts_for_user(self, user_id: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get life facts for a user"""
        facts = [
            fact for fact in self.life_facts.values()
            if fact.get("user_id") == user_id
        ]
        
        if category:
            facts = [fact for fact in facts if fact.get("category") == category]
        
        # Sort by created_at descending
        facts.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return facts
    
    async def get_info_sources_for_user(self, user_id: str, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get info sources for a user"""
        sources = [
            source for source in self.info_sources.values()
            if source.get("user_id") == user_id
        ]
        
        if platform:
            sources = [source for source in sources if source.get("platform") == platform]
        
        # Sort by created_at descending
        sources.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return sources
    
    async def search_user_content(self, user_id: str, query: str, content_types: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Search across user's content"""
        results = {}
        query_lower = query.lower()
        
        search_types = content_types or ["diary_entries", "life_facts", "documents"]
        
        # Search diary entries
        if "diary_entries" in search_types:
            diary_matches = []
            for entry in self.diary_entries.values():
                if entry.get("user_id") == user_id:
                    entry_text = f"{entry.get('summary', '')} {entry.get('content', '')}".lower()
                    if query_lower in entry_text:
                        diary_matches.append(entry)
            results["diary_entries"] = diary_matches
        
        # Search life facts
        if "life_facts" in search_types:
            fact_matches = []
            for fact in self.life_facts.values():
                if fact.get("user_id") == user_id:
                    fact_text = f"{fact.get('summary', '')} {fact.get('description', '')}".lower()
                    if query_lower in fact_text:
                        fact_matches.append(fact)
            results["life_facts"] = fact_matches
        
        # Search documents
        if "documents" in search_types:
            doc_matches = []
            for doc in self.documents.values():
                if doc.get("user_id") == user_id:
                    doc_text = f"{doc.get('filename', '')} {doc.get('description', '')}".lower()
                    if query_lower in doc_text:
                        doc_matches.append(doc)
            results["documents"] = doc_matches
        
        return results
    
    async def get_user_activity_summary(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get user activity summary"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Count recent items
        recent_diary_entries = 0
        recent_life_facts = 0
        recent_documents = 0
        
        # Get recent diary entries
        for entry in self.diary_entries.values():
            if entry.get("user_id") == user_id:
                created_at = datetime.fromisoformat(entry.get("created_at", "1900-01-01"))
                if created_at > cutoff_date:
                    recent_diary_entries += 1
        
        # Get recent life facts
        for fact in self.life_facts.values():
            if fact.get("user_id") == user_id:
                created_at = datetime.fromisoformat(fact.get("created_at", "1900-01-01"))
                if created_at > cutoff_date:
                    recent_life_facts += 1
        
        # Get recent documents
        for doc in self.documents.values():
            if doc.get("user_id") == user_id:
                created_at = datetime.fromisoformat(doc.get("created_at", "1900-01-01"))
                if created_at > cutoff_date:
                    recent_documents += 1
        
        # Get most recent items
        recent_entries = await self.get_diary_entries_for_user(user_id, limit=5)
        recent_facts = await self.get_life_facts_for_user(user_id)
        recent_docs = await self.get_documents_for_user(user_id)
        
        return {
            "user_id": user_id,
            "days": days,
            "activity_counts": {
                "diary_entries": recent_diary_entries,
                "life_facts": recent_life_facts,
                "documents": recent_documents,
                "total": recent_diary_entries + recent_life_facts + recent_documents
            },
            "recent_items": {
                "diary_entries": recent_entries[:3],
                "life_facts": recent_facts[:3],
                "documents": recent_docs[:3]
            },
            "total_counts": {
                "diary_entries": len([e for e in self.diary_entries.values() if e.get("user_id") == user_id]),
                "life_facts": len([f for f in self.life_facts.values() if f.get("user_id") == user_id]),
                "documents": len([d for d in self.documents.values() if d.get("user_id") == user_id]),
            }
        }
    
    async def get_life_events_by_date_range(
        self, 
        user_id: str, 
        start_date: datetime, 
        end_date: datetime,
        visibility_levels: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get life events for a user within a specific date range"""
        matching_events = []
        
        for entry in self.diary_entries.values():
            if entry.get("user_id") != user_id:
                continue
                
            # Parse event start date
            try:
                event_start_date = datetime.fromisoformat(entry.get("start_date"))
            except (ValueError, TypeError):
                continue
                
            # Check if event falls within date range
            if not (start_date <= event_start_date <= end_date):
                continue
                
            # Check visibility level if specified
            if visibility_levels:
                visibility_type = entry.get("visibility", {}).get("type")
                if visibility_type not in visibility_levels:
                    continue
                    
            matching_events.append(entry)
        
        # Sort by start_date descending (most recent first)
        matching_events.sort(
            key=lambda x: datetime.fromisoformat(x.get("start_date")), 
            reverse=True
        )
        
        return matching_events