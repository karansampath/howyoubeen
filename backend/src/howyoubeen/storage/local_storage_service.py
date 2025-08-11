"""
Local Storage Service Implementation

Persistent file-based storage using storage/<user-id>/ directories for MVP/prototyping.
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
    """Local storage implementation using persistent user directories"""
    
    def __init__(self, storage_root: Optional[str] = None):
        """
        Initialize local storage service
        
        Args:
            storage_root: Root directory for storage (defaults to ./storage)
        """
        self.storage_root = storage_root or os.path.join(os.getcwd(), "storage")
        
        # Ensure storage directory exists
        os.makedirs(self.storage_root, exist_ok=True)
        
        # In-memory caches for sessions and cross-user lookups
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self._username_to_user_id: Dict[str, str] = {}
        self._email_to_user_id: Dict[str, str] = {}
        
        # Load existing user mappings
        self._load_user_mappings()
        
        logger.info(f"Local storage initialized with storage root: {self.storage_root}")

    def _load_user_mappings(self):
        """Load existing username/email to user_id mappings"""
        mappings_file = os.path.join(self.storage_root, "user_mappings.json")
        if os.path.exists(mappings_file):
            try:
                with open(mappings_file, 'r') as f:
                    data = json.load(f)
                self._username_to_user_id = data.get('usernames', {})
                self._email_to_user_id = data.get('emails', {})
                logger.info(f"Loaded mappings for {len(self._username_to_user_id)} users")
            except Exception as e:
                logger.warning(f"Failed to load user mappings: {e}")

    def _save_user_mappings(self):
        """Save username/email to user_id mappings"""
        mappings_file = os.path.join(self.storage_root, "user_mappings.json")
        try:
            data = {
                'usernames': self._username_to_user_id,
                'emails': self._email_to_user_id,
                'last_updated': datetime.now().isoformat()
            }
            with open(mappings_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug("Saved user mappings")
        except Exception as e:
            logger.error(f"Failed to save user mappings: {e}")

    def _get_user_dir(self, user_id: str) -> str:
        """Get user-specific storage directory"""
        return os.path.join(self.storage_root, user_id)

    def _ensure_user_dir(self, user_id: str) -> str:
        """Ensure user directory exists and return path"""
        user_dir = self._get_user_dir(user_id)
        os.makedirs(user_dir, exist_ok=True)
        return user_dir

    def _save_user_data(self, user_id: str, filename: str, data: Any):
        """Save data to user-specific file"""
        user_dir = self._ensure_user_dir(user_id)
        filepath = os.path.join(user_dir, filename)
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.debug(f"Saved {filename} for user {user_id[:8]}...")
        except Exception as e:
            logger.error(f"Failed to save {filename} for user {user_id[:8]}...: {e}")

    def _load_user_data(self, user_id: str, filename: str) -> Any:
        """Load data from user-specific file"""
        user_dir = self._get_user_dir(user_id)
        filepath = os.path.join(user_dir, filename)
        if not os.path.exists(filepath):
            return None
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load {filename} for user {user_id[:8]}...: {e}")
            return None

    def _list_user_data(self, user_id: str, filename: str) -> List[Any]:
        """Load list data from user-specific file, return empty list if not found"""
        data = self._load_user_data(user_id, filename)
        return data if data is not None else []

    def _append_user_data(self, user_id: str, filename: str, item: Dict[str, Any]):
        """Append item to user data list file"""
        current_data = self._list_user_data(user_id, filename)
        current_data.append(item)
        self._save_user_data(user_id, filename, current_data)

    # User Management
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user"""
        username = user_data.get("username", "")
        email = user_data.get("email", "")
        
        # Check for existing username
        if await self.username_exists(username):
            raise ValueError(f"Username '{username}' already exists")
        
        # Check for existing email
        if await self.email_exists(email):
            raise ValueError(f"Email '{email}' already exists")
        
        user_id = str(uuid4())
        user = {
            **user_data,
            "id": user_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Save user data to their directory
        self._save_user_data(user_id, "user.json", user)
        
        # Update mappings
        self._username_to_user_id[username] = user_id
        self._email_to_user_id[email] = user_id
        self._save_user_mappings()
        
        logger.info(f"Created user: {username} ({user_id})")
        return user

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        return self._load_user_data(user_id, "user.json")

    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        user_id = self._username_to_user_id.get(username)
        if user_id:
            return await self.get_user(user_id)
        return None

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        user_id = self._email_to_user_id.get(email)
        if user_id:
            return await self.get_user(user_id)
        return None

    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user data"""
        user = await self.get_user(user_id)
        if not user:
            return False
        
        # Update user data
        user.update(updates)
        user["updated_at"] = datetime.now().isoformat()
        
        # Save updated user
        self._save_user_data(user_id, "user.json", user)
        
        # Update mappings if username or email changed
        if "username" in updates:
            old_username = None
            for username, uid in self._username_to_user_id.items():
                if uid == user_id:
                    old_username = username
                    break
            if old_username:
                del self._username_to_user_id[old_username]
            self._username_to_user_id[updates["username"]] = user_id
            
        if "email" in updates:
            old_email = None
            for email, uid in self._email_to_user_id.items():
                if uid == user_id:
                    old_email = email
                    break
            if old_email:
                del self._email_to_user_id[old_email]
            self._email_to_user_id[updates["email"]] = user_id
            
        if "username" in updates or "email" in updates:
            self._save_user_mappings()
        
        return True

    async def username_exists(self, username: str) -> bool:
        """Check if username is already taken"""
        return username in self._username_to_user_id

    async def email_exists(self, email: str) -> bool:
        """Check if email is already registered"""
        return email in self._email_to_user_id

    # Onboarding Session Management (in-memory for now)
    async def create_onboarding_session(self, user_id: Optional[str] = None) -> str:
        """Create a new onboarding session"""
        session_id = str(uuid4())
        session = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "step": "start",
            "data": {}
        }
        self.sessions[session_id] = session
        return session_id

    async def update_onboarding_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Update onboarding session data"""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        session["data"].update(data)
        session["updated_at"] = datetime.now().isoformat()
        return True

    async def get_onboarding_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get onboarding session data"""
        return self.sessions.get(session_id)

    async def set_onboarding_step(self, session_id: str, step: str) -> bool:
        """Update onboarding session step"""
        if session_id not in self.sessions:
            return False
        
        self.sessions[session_id]["step"] = step
        self.sessions[session_id]["updated_at"] = datetime.now().isoformat()
        return True

    async def set_onboarding_user_id(self, session_id: str, user_id: str) -> bool:
        """Associate user ID with onboarding session"""
        if session_id not in self.sessions:
            return False
        
        self.sessions[session_id]["user_id"] = user_id
        self.sessions[session_id]["updated_at"] = datetime.now().isoformat()
        return True

    # File Management
    async def save_file(self, user_id: str, file_content: bytes, filename: str, 
                       description: str = "") -> Dict[str, Any]:
        """Save a file for a user"""
        user_dir = self._ensure_user_dir(user_id)
        files_dir = os.path.join(user_dir, "files")
        os.makedirs(files_dir, exist_ok=True)
        
        # Generate unique filename
        file_id = str(uuid4())
        file_ext = os.path.splitext(filename)[1]
        stored_filename = f"{file_id}{file_ext}"
        file_path = os.path.join(files_dir, stored_filename)
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        file_metadata = {
            "file_id": file_id,
            "original_filename": filename,
            "stored_filename": stored_filename,
            "file_path": file_path,
            "description": description,
            "size": len(file_content),
            "created_at": datetime.now().isoformat()
        }
        
        logger.info(f"Saved file {filename} for user {user_id[:8]}...")
        return file_metadata

    async def get_file_url(self, file_path: str, expires_in: int = 3600) -> Optional[str]:
        """Get URL for accessing a file (returns local file path for local storage)"""
        if os.path.exists(file_path):
            return f"file://{file_path}"
        return None

    async def delete_file(self, file_path: str) -> bool:
        """Delete a file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False

    # Document Metadata Management
    async def create_document(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create document metadata record"""
        user_id = document_data.get("user_id")
        if not user_id:
            raise ValueError("user_id is required for document")
        
        document_id = str(uuid4())
        document = {
            **document_data,
            "document_id": document_id,
            "created_at": datetime.now().isoformat()
        }
        
        self._append_user_data(user_id, "documents.json", document)
        logger.info(f"Created document {document_id} for user {user_id[:8]}...")
        return document

    async def get_documents_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all documents for a user"""
        return self._list_user_data(user_id, "documents.json")

    # Visibility Categories
    async def create_visibility_categories(self, user_id: str, 
                                          categories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create visibility categories for a user"""
        created_categories = []
        for category_data in categories:
            category_id = str(uuid4())
            category = {
                **category_data,
                "category_id": category_id,
                "user_id": user_id,
                "created_at": datetime.now().isoformat()
            }
            created_categories.append(category)
        
        self._save_user_data(user_id, "visibility_categories.json", created_categories)
        logger.info(f"Created {len(created_categories)} visibility categories for user {user_id[:8]}...")
        return created_categories

    async def get_visibility_categories(self, user_id: str) -> List[Dict[str, Any]]:
        """Get visibility categories for a user"""
        return self._list_user_data(user_id, "visibility_categories.json")

    # User Content (Life Events & Life Facts)
    async def create_life_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a life event"""
        user_id = event_data.get("user_id")
        if not user_id:
            raise ValueError("user_id is required for life event")
        
        event_id = str(uuid4())
        event = {
            "event_id": event_id,
            "user_id": user_id,
            "summary": event_data["summary"],
            "start_date": event_data.get("start_date", datetime.now().isoformat()),
            "end_date": event_data.get("end_date"),
            "visibility": event_data.get("visibility", "friends_only"),
            "associated_docs": event_data.get("associated_docs", []),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self._append_user_data(user_id, "life_events.json", event)
        logger.info(f"Created life event {event_id} for user {user_id[:8]}...")
        return event

    async def create_life_fact(self, fact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a life fact"""
        user_id = fact_data.get("user_id")
        if not user_id:
            raise ValueError("user_id is required for life fact")
        
        fact_id = str(uuid4())
        fact = {
            **fact_data,
            "fact_id": fact_id,
            "created_at": datetime.now().isoformat()
        }
        
        self._append_user_data(user_id, "life_facts.json", fact)
        logger.info(f"Created life fact {fact_id} for user {user_id[:8]}...")
        return fact

    async def create_info_source(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an info source record"""
        user_id = source_data.get("user_id")
        if not user_id:
            raise ValueError("user_id is required for info source")
        
        source_id = str(uuid4())
        source = {
            **source_data,
            "source_id": source_id,
            "created_at": datetime.now().isoformat()
        }
        
        self._append_user_data(user_id, "info_sources.json", source)
        logger.info(f"Created info source {source_id} for user {user_id[:8]}...")
        return source

    # Health and Diagnostics
    async def health_check(self) -> Dict[str, Any]:
        """Check storage service health"""
        try:
            # Check if storage directory is accessible
            test_file = os.path.join(self.storage_root, ".health_check")
            with open(test_file, 'w') as f:
                f.write(datetime.now().isoformat())
            os.remove(test_file)
            
            # Count users
            user_count = len(self._username_to_user_id)
            session_count = len(self.sessions)
            
            return {
                "status": "healthy",
                "storage_type": "local_directories",
                "storage_root": self.storage_root,
                "user_count": user_count,
                "active_sessions": session_count,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def get_storage_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get storage usage statistics"""
        if user_id:
            # User-specific stats
            user_dir = self._get_user_dir(user_id)
            if not os.path.exists(user_dir):
                return {"user_id": user_id, "exists": False}
            
            stats = {"user_id": user_id, "exists": True}
            for filename in ["life_events.json", "life_facts.json", "documents.json"]:
                data = self._list_user_data(user_id, filename)
                stats[filename.replace(".json", "_count")] = len(data)
            
            return stats
        else:
            # Global stats
            return {
                "total_users": len(self._username_to_user_id),
                "active_sessions": len(self.sessions),
                "storage_directories": len([d for d in os.listdir(self.storage_root) 
                                          if os.path.isdir(os.path.join(self.storage_root, d))])
            }

    # Cleanup Operations
    async def cleanup_expired_sessions(self, hours_old: int = 24) -> int:
        """Clean up expired onboarding sessions"""
        cutoff_time = datetime.now() - timedelta(hours=hours_old)
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            try:
                updated_at = datetime.fromisoformat(session["updated_at"])
                if updated_at < cutoff_time:
                    expired_sessions.append(session_id)
            except (ValueError, KeyError):
                # Invalid timestamp, mark for cleanup
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        return len(expired_sessions)

    # Query Methods
    async def get_life_events_for_user(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get life events for a user"""
        all_entries = self._list_user_data(user_id, "life_events.json")
        
        # Sort by start_date descending
        try:
            all_entries.sort(key=lambda x: x.get("start_date", ""), reverse=True)
        except:
            pass  # If sorting fails, return as-is
        
        return all_entries[offset:offset + limit]

    async def get_life_facts_for_user(self, user_id: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get life facts for a user"""
        all_facts = self._list_user_data(user_id, "life_facts.json")
        
        if category:
            all_facts = [f for f in all_facts if f.get("category") == category]
        
        return all_facts

    async def get_info_sources_for_user(self, user_id: str, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get info sources for a user"""
        all_sources = self._list_user_data(user_id, "info_sources.json")
        
        if platform:
            all_sources = [s for s in all_sources if s.get("platform") == platform]
        
        return all_sources

    async def search_user_content(self, user_id: str, query: str, content_types: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Search across user's content"""
        query = query.lower()
        results = {}
        
        # Default to searching all content types
        if not content_types:
            content_types = ["life_events", "life_facts", "documents"]
        
        if "life_events" in content_types:
            life_events = self._list_user_data(user_id, "life_events.json")
            results["life_events"] = [
                e for e in life_events 
                if query in e.get("summary", "").lower()
            ]
        
        if "life_facts" in content_types:
            life_facts = self._list_user_data(user_id, "life_facts.json")
            results["life_facts"] = [
                f for f in life_facts 
                if query in f.get("summary", "").lower()
            ]
        
        if "documents" in content_types:
            documents = self._list_user_data(user_id, "documents.json")
            results["documents"] = [
                d for d in documents 
                if query in d.get("description", "").lower() or 
                   query in d.get("original_filename", "").lower()
            ]
        
        return results

    async def get_user_activity_summary(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get user activity summary"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get all user data
        life_events = self._list_user_data(user_id, "life_events.json")
        life_facts = self._list_user_data(user_id, "life_facts.json")
        documents = self._list_user_data(user_id, "documents.json")
        
        # Count recent items
        recent_life_events = 0
        recent_life_facts = 0
        recent_documents = 0
        
        for entry in life_events:
            try:
                created_at = datetime.fromisoformat(entry.get("created_at", "1900-01-01"))
                if created_at > cutoff_date:
                    recent_life_events += 1
            except:
                pass
        
        for fact in life_facts:
            try:
                created_at = datetime.fromisoformat(fact.get("created_at", "1900-01-01"))
                if created_at > cutoff_date:
                    recent_life_facts += 1
            except:
                pass
        
        for doc in documents:
            try:
                created_at = datetime.fromisoformat(doc.get("created_at", "1900-01-01"))
                if created_at > cutoff_date:
                    recent_documents += 1
            except:
                pass
        
        return {
            "user_id": user_id,
            "days": days,
            "activity_counts": {
                "life_events": recent_life_events,
                "life_facts": recent_life_facts,
                "documents": recent_documents,
                "total": recent_life_events + recent_life_facts + recent_documents
            },
            "recent_items": {
                "life_events": life_events[:3],
                "life_facts": life_facts[:3],
                "documents": documents[:3]
            },
            "total_counts": {
                "life_events": len(life_events),
                "life_facts": len(life_facts),
                "documents": len(documents)
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
        all_events = self._list_user_data(user_id, "life_events.json")
        matching_events = []
        
        for entry in all_events:
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
                visibility = entry.get("visibility")
                if isinstance(visibility, dict):
                    visibility_type = visibility.get("type")
                else:
                    # Handle simple string visibility format
                    visibility_type = visibility
                
                if visibility_type not in visibility_levels:
                    continue
                    
            matching_events.append(entry)
        
        # Sort by start_date descending (most recent first)
        matching_events.sort(
            key=lambda x: datetime.fromisoformat(x.get("start_date")), 
            reverse=True
        )
        
        return matching_events