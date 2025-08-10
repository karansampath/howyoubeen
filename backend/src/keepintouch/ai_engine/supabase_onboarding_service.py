"""
Supabase-integrated onboarding service for managing the user onboarding flow

This service uses Supabase repositories instead of in-memory storage
for production-ready data persistence.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4
import logging

from ..data_models.models import User, Document, InfoSource, VisibilityCategory
from ..data_models.enums import ContentType, VisibilityCategoryType
from ..storage.repositories import UserRepository, OnboardingRepository, DocumentRepository, VisibilityRepository
from ..integrations.mock_services import mock_services
from .document_processor import document_processor, profile_generator

logger = logging.getLogger(__name__)


class SupabaseOnboardingService:
    """Service to handle user onboarding process with Supabase"""
    
    def __init__(self):
        self.user_repo = UserRepository(use_service_key=True)
        self.onboarding_repo = OnboardingRepository(use_service_key=True)
        self.document_repo = DocumentRepository(use_service_key=True)
        self.visibility_repo = VisibilityRepository(use_service_key=True)
    
    async def start_onboarding(self) -> str:
        """Start a new onboarding process"""
        try:
            session = await self.onboarding_repo.create_session()
            logger.info(f"Started onboarding session: {session['id']}")
            return session['id']
        except Exception as e:
            logger.error(f"Error starting onboarding: {e}")
            raise
    
    async def submit_basic_info(self, session_id: str, name: str, bio: str, username: str, email: str) -> bool:
        """Submit basic user information (step a & b)"""
        try:
            # Check if username is already taken
            if await self.user_repo.username_exists(username):
                logger.warning(f"Username '{username}' already exists")
                return False
            
            # Check if email is already taken
            if await self.user_repo.email_exists(email):
                logger.warning(f"Email '{email}' already exists")
                return False
            
            # Update session with basic info
            basic_info = {
                "full_name": name,
                "bio": bio,
                "username": username,
                "email": email
            }
            
            success = await self.onboarding_repo.update_session_data(session_id, {"basic_info": basic_info})
            if success:
                await self.onboarding_repo.set_session_step(session_id, "basic_info_complete")
                logger.info(f"Basic info submitted for session {session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error submitting basic info: {e}")
            return False
    
    async def add_data_source(self, session_id: str, platform: str, credentials: Dict[str, str]) -> Optional[InfoSource]:
        """Add a data source connection (step c)"""
        try:
            session_data = await self.onboarding_repo.get_session_data(session_id)
            if not session_data:
                return None
            
            service = mock_services.get_service(platform)
            if not service:
                logger.warning(f"Unknown platform: {platform}")
                return None
            
            # Mock connection to service
            user_id = session_data.get("user_id") or str(uuid4())
            info_source = await service.connect(user_id, credentials)
            
            # Store the connection in session data
            data = session_data.get("data", {})
            current_sources = data.get("data_sources", [])
            current_sources.append({
                "platform": info_source.platform,
                "url": info_source.url,
                "description": info_source.info_description,
                "source_id": info_source.source_id
            })
            
            success = await self.onboarding_repo.update_session_data(session_id, {"data_sources": current_sources})
            
            if success:
                logger.info(f"Added data source {platform} to session {session_id}")
                return info_source
            
            return None
            
        except Exception as e:
            logger.error(f"Error adding data source: {e}")
            return None
    
    async def upload_document(self, session_id: str, file_content: bytes, filename: str, description: str = "") -> Optional[Document]:
        """Upload and process a document (step c)"""
        try:
            session_data = await self.onboarding_repo.get_session_data(session_id)
            if not session_data:
                return None
            
            # For now, store file locally (would use Supabase Storage in production)
            import tempfile
            import os
            
            temp_dir = tempfile.gettempdir()
            file_id = str(uuid4())
            file_ext = os.path.splitext(filename)[1] if '.' in filename else ''
            file_path = os.path.join(temp_dir, f"keepintouch_{file_id}{file_ext}")
            
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            # Determine content type
            content_type = self._get_content_type(file_ext.lstrip('.'))
            
            # Create document record in session (will be saved to DB during processing)
            document_data = {
                "document_id": str(uuid4()),
                "file_path": file_path,
                "content_type": content_type.value,
                "description": description or f"Uploaded file: {filename}",
                "filename": filename,
                "file_size": len(file_content)
            }
            
            # Store in session
            data = session_data.get("data", {})
            current_docs = data.get("uploaded_documents", [])
            current_docs.append(document_data)
            
            success = await self.onboarding_repo.update_session_data(session_id, {"uploaded_documents": current_docs})
            
            if success:
                logger.info(f"Uploaded document {filename} to session {session_id}")
                # Return a Document-like object
                return Document(
                    document_id=document_data["document_id"],
                    file_path=document_data["file_path"],
                    content_type=ContentType(document_data["content_type"]),
                    description=document_data["description"]
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error uploading document: {e}")
            return None
    
    async def configure_visibility(self, session_id: str, visibility_categories: List[Dict[str, Any]]) -> bool:
        """Configure visibility categories (step d)"""
        try:
            # Validate category types
            valid_types = [t.value for t in VisibilityCategoryType]
            for cat_data in visibility_categories:
                if cat_data.get("type") not in valid_types:
                    logger.warning(f"Invalid visibility type: {cat_data.get('type')}")
                    return False
            
            success = await self.onboarding_repo.update_session_data(session_id, {
                "visibility_categories": visibility_categories
            })
            
            if success:
                await self.onboarding_repo.set_session_step(session_id, "visibility_configured")
                logger.info(f"Configured visibility for session {session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error configuring visibility: {e}")
            return False
    
    async def process_user_data(self, session_id: str) -> Dict[str, Any]:
        """Process all user data and generate profile (step e)"""
        try:
            await self.onboarding_repo.set_session_step(session_id, "processing")
            
            # Get session data
            session_data = await self.onboarding_repo.get_session_data(session_id)
            if not session_data:
                return {"success": False, "error": "Session not found"}
            
            data = session_data.get("data", {})
            basic_info = data.get("basic_info", {})
            
            # Create the user in Supabase
            user_data = {
                "username": basic_info.get("username", f"user_{session_id[:8]}"),
                "email": basic_info.get("email", ""),
                "full_name": basic_info.get("full_name", ""),
                "bio": basic_info.get("bio", ""),
                "onboarding_completed": False
            }
            
            user = await self.user_repo.create_user(user_data)
            user_id = user["id"]
            
            # Update session with user_id
            await self.onboarding_repo.set_session_user_id(session_id, user_id)
            
            # Create visibility categories
            visibility_cats = data.get("visibility_categories", [])
            if not visibility_cats:
                # Create default categories
                visibility_categories = await self.visibility_repo.create_default_categories(user_id)
            else:
                visibility_categories = await self.visibility_repo.create_categories_for_user(user_id, visibility_cats)
            
            # Get default visibility category for content
            default_visibility = visibility_categories[0] if visibility_categories else None
            
            # Create info sources
            data_sources = data.get("data_sources", [])
            for source_data in data_sources:
                info_source_data = {
                    "user_id": user_id,
                    "platform": source_data["platform"],
                    "url": source_data.get("url", ""),
                    "info_description": source_data.get("description", f"Data from {source_data['platform']}")
                }
                
                # Create info source in Supabase
                await self.user_repo.client.table("info_sources").insert(info_source_data).execute()
            
            # Create documents
            uploaded_docs = data.get("uploaded_documents", [])
            documents_data = []
            
            for doc_info in uploaded_docs:
                document_data = {
                    "user_id": user_id,
                    "file_path": doc_info["file_path"],
                    "content_type": doc_info["content_type"],
                    "description": doc_info["description"],
                    "file_size": doc_info.get("file_size", 0)
                }
                
                doc = await self.document_repo.create_document(document_data)
                documents_data.append(doc)
            
            # Process documents with AI (mock)
            extracted_data = []
            for doc in documents_data:
                document_obj = Document(
                    document_id=doc["id"],
                    file_path=doc["file_path"],
                    content_type=ContentType(doc["content_type"]),
                    description=doc["description"]
                )
                
                processing_result = await document_processor.process_document(document_obj)
                extracted_data.append(processing_result)
            
            # Process data from external sources (mock)
            for source_data in data_sources:
                platform = source_data["platform"]
                service = mock_services.get_service(platform)
                if service:
                    if platform == "goodreads":
                        # Mock source data for processing
                        mock_source = InfoSource(
                            platform=platform,
                            url=source_data.get("url", ""),
                            info_description=source_data.get("description", "")
                        )
                        reading_data = await service.get_reading_data(mock_source)
                        extracted_data.extend(reading_data)
                    elif platform == "linkedin":
                        mock_source = InfoSource(
                            platform=platform,
                            url=source_data.get("url", ""),
                            info_description=source_data.get("description", "")
                        )
                        profile_data = await service.get_profile_data(mock_source)
                        extracted_data.append({"type": "professional_info", "extracted_data": profile_data})
            
            # Generate diary entries and life facts with AI
            diary_entries = await profile_generator.generate_diary_entries(extracted_data, visibility_categories)
            life_facts = await profile_generator.generate_life_facts(extracted_data, visibility_categories)
            
            # Save diary entries to Supabase
            for entry in diary_entries:
                entry_data = {
                    "user_id": user_id,
                    "visibility_category_id": default_visibility["id"] if default_visibility else None,
                    "start_date": entry.start_date.isoformat(),
                    "end_date": entry.end_date.isoformat() if entry.end_date else None,
                    "summary": entry.summary
                }
                await self.user_repo.client.table("diary_entries").insert(entry_data).execute()
            
            # Save life facts to Supabase
            for fact in life_facts:
                fact_data = {
                    "user_id": user_id,
                    "visibility_category_id": default_visibility["id"] if default_visibility else None,
                    "summary": fact.summary,
                    "category": fact.category,
                    "date": fact.date.isoformat()
                }
                await self.user_repo.client.table("life_facts").insert(fact_data).execute()
            
            # Generate AI summary
            summary_data = {
                "full_name": user["full_name"],
                "bio": user["bio"],
                "sources": data_sources,
                "documents": uploaded_docs
            }
            ai_summary = await profile_generator.generate_user_summary(summary_data)
            
            # Mark user onboarding as complete
            await self.user_repo.mark_onboarding_complete(user_id)
            
            # Update session as completed
            await self.onboarding_repo.set_session_step(session_id, "completed")
            
            logger.info(f"Successfully processed onboarding for user {user_id}")
            
            return {
                "success": True,
                "user_id": user_id,
                "profile_url": f"/profile/{user['username']}",
                "ai_summary": ai_summary,
                "next_steps": [
                    "Share your profile URL with friends",
                    "Test your AI by chatting with it",
                    "Upload more content to enrich your profile"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error processing user data: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_onboarding_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current onboarding status"""
        try:
            return await self.onboarding_repo.get_session_summary(session_id)
        except Exception as e:
            logger.error(f"Error getting onboarding status: {e}")
            return None
    
    def _get_content_type(self, file_extension: str) -> ContentType:
        """Determine content type from file extension"""
        image_exts = ["jpg", "jpeg", "png", "gif", "webp"]
        video_exts = ["mp4", "avi", "mov", "mkv"]
        doc_exts = ["pdf", "doc", "docx", "txt"]
        
        if file_extension.lower() in image_exts:
            return ContentType.IMAGE
        elif file_extension.lower() in video_exts:
            return ContentType.VIDEO
        elif file_extension.lower() in doc_exts:
            return ContentType.DOCUMENT
        else:
            return ContentType.TEXT


# Global service instance
supabase_onboarding_service = SupabaseOnboardingService()