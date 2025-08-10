"""
Onboarding service for managing the user onboarding flow

This service orchestrates the complete onboarding process including:
- Basic info collection (name, bio)
- Data source connections 
- Document uploads and processing
- Visibility configuration
- Profile generation
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..data_models.models import User, Document, InfoSource, VisibilityCategory, FriendshipTier
from ..data_models.enums import ContentType, VisibilityCategoryType
from ..storage.memory_store import store
from ..integrations.mock_services import mock_services
from .document_processor import document_processor, profile_generator


class OnboardingService:
    """Service to handle user onboarding process"""
    
    async def start_onboarding(self) -> str:
        """Start a new onboarding process"""
        user_id = str(uuid4())
        session_id = await store.create_onboarding_session(user_id)
        return session_id
    
    async def submit_basic_info(self, session_id: str, name: str, bio: str, username: str, email: str) -> bool:
        """Submit basic user information (step a & b)"""
        session = await store.get_onboarding_session(session_id)
        if not session:
            return False
        
        # Validate username is unique
        existing_user = await store.get_user_by_username(username)
        if existing_user:
            return False
        
        basic_info = {
            "full_name": name,
            "bio": bio,
            "username": username,
            "email": email
        }
        
        await store.update_onboarding_session(session_id, {"basic_info": basic_info})
        await store.set_onboarding_step(session_id, "basic_info_complete")
        return True
    
    async def add_data_source(self, session_id: str, platform: str, credentials: Dict[str, str]) -> Optional[InfoSource]:
        """Add a data source connection (step c)"""
        session = await store.get_onboarding_session(session_id)
        if not session:
            return None
        
        service = mock_services.get_service(platform)
        if not service:
            return None
        
        try:
            user_id = session["user_id"]
            info_source = await service.connect(user_id, credentials)
            
            # Store the connection
            current_sources = session["data"].get("data_sources", [])
            current_sources.append({
                "platform": info_source.platform,
                "url": info_source.url,
                "description": info_source.info_description,
                "source_id": info_source.source_id
            })
            
            await store.update_onboarding_session(session_id, {"data_sources": current_sources})
            return info_source
            
        except Exception as e:
            print(f"Error connecting to {platform}: {e}")
            return None
    
    async def upload_document(self, session_id: str, file_content: bytes, filename: str, description: str = "") -> Optional[Document]:
        """Upload and process a document (step c)"""
        session = await store.get_onboarding_session(session_id)
        if not session:
            return None
        
        try:
            # Save the uploaded file
            file_path = await store.save_uploaded_file(file_content, filename)
            
            # Determine content type
            ext = filename.split('.')[-1].lower() if '.' in filename else ''
            content_type = self._get_content_type(ext)
            
            # Create document record
            document = Document(
                file_path=file_path,
                content_type=content_type,
                description=description or f"Uploaded file: {filename}"
            )
            
            await store.create_document({
                "document_id": document.document_id,
                "file_path": document.file_path,
                "content_type": document.content_type,
                "description": document.description
            })
            
            # Store in session
            current_docs = session["data"].get("uploaded_documents", [])
            current_docs.append({
                "document_id": document.document_id,
                "filename": filename,
                "description": description,
                "content_type": content_type.value
            })
            
            await store.update_onboarding_session(session_id, {"uploaded_documents": current_docs})
            return document
            
        except Exception as e:
            print(f"Error uploading document: {e}")
            return None
    
    async def configure_visibility(self, session_id: str, visibility_categories: List[Dict[str, Any]]) -> bool:
        """Configure visibility categories (step d)"""
        session = await store.get_onboarding_session(session_id)
        if not session:
            return False
        
        try:
            # Convert to VisibilityCategory objects
            categories = []
            for cat_data in visibility_categories:
                category = VisibilityCategory(
                    type=VisibilityCategoryType(cat_data["type"]),
                    name=cat_data.get("name"),
                    also_visible=[]  # Simplified for now
                )
                categories.append(category)
            
            await store.update_onboarding_session(session_id, {
                "visibility_categories": [cat.dict() for cat in categories]
            })
            await store.set_onboarding_step(session_id, "visibility_configured")
            return True
            
        except Exception as e:
            print(f"Error configuring visibility: {e}")
            return False
    
    async def process_user_data(self, session_id: str) -> Dict[str, Any]:
        """Process all user data and generate profile (step e)"""
        session = await store.get_onboarding_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}
        
        try:
            await store.set_onboarding_step(session_id, "processing")
            
            # Get session data
            session_data = session["data"]
            basic_info = session_data.get("basic_info", {})
            
            # Create the user
            user_data = {
                "user_id": session["user_id"],
                "username": basic_info.get("username", f"user_{session['user_id'][:8]}"),
                "email": basic_info.get("email", ""),
                "full_name": basic_info.get("full_name", ""),
                "bio": basic_info.get("bio", ""),
                "onboarding_completed": False,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            user = await store.create_user(user_data)
            
            # Process documents
            extracted_data = []
            uploaded_docs = session_data.get("uploaded_documents", [])
            
            for doc_info in uploaded_docs:
                document = await store.documents.get(doc_info["document_id"])
                if document:
                    processing_result = await document_processor.process_document(document)
                    extracted_data.append(processing_result)
            
            # Process data from external sources
            data_sources = session_data.get("data_sources", [])
            for source_info in data_sources:
                platform = source_info["platform"]
                service = mock_services.get_service(platform)
                if service:
                    # Simulate fetching and processing data from the service
                    if platform == "goodreads":
                        reading_data = await service.get_reading_data(InfoSource(**source_info))
                        extracted_data.extend(reading_data)
                    elif platform == "linkedin":
                        profile_data = await service.get_profile_data(InfoSource(**source_info))
                        extracted_data.append({"type": "professional_info", "extracted_data": profile_data})
            
            # Get visibility configuration
            visibility_cats = session_data.get("visibility_categories", [])
            visibility_categories = [VisibilityCategory(**cat) for cat in visibility_cats]
            
            # Generate diary entries and life facts
            diary_entries = await profile_generator.generate_diary_entries(extracted_data, visibility_categories)
            life_facts = await profile_generator.generate_life_facts(extracted_data, visibility_categories)
            
            # Generate AI summary
            summary_data = {
                "full_name": user.full_name,
                "bio": user.bio,
                "sources": data_sources,
                "documents": uploaded_docs
            }
            ai_summary = await profile_generator.generate_user_summary(summary_data)
            
            # Update user with generated data
            await store.update_user(user.user_id, {
                "diary_entries": [entry.dict() for entry in diary_entries],
                "facts": [fact.dict() for fact in life_facts],
                "sources": [InfoSource(**source).dict() for source in data_sources],
                "onboarding_completed": True,
                "knowledge_last_updated": datetime.now()
            })
            
            await store.set_onboarding_step(session_id, "completed")
            
            return {
                "success": True,
                "user_id": user.user_id,
                "profile_url": f"/profile/{user.username}",
                "ai_summary": ai_summary,
                "next_steps": [
                    "Share your profile URL with friends",
                    "Test your AI by chatting with it",
                    "Upload more content to enrich your profile"
                ]
            }
            
        except Exception as e:
            print(f"Error processing user data: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_onboarding_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current onboarding status"""
        session = await store.get_onboarding_session(session_id)
        if not session:
            return None
        
        return {
            "session_id": session_id,
            "step": session["step"],
            "created_at": session["created_at"],
            "updated_at": session["updated_at"],
            "data_summary": {
                "has_basic_info": "basic_info" in session["data"],
                "data_sources_count": len(session["data"].get("data_sources", [])),
                "documents_count": len(session["data"].get("uploaded_documents", [])),
                "has_visibility_config": "visibility_categories" in session["data"]
            }
        }
    
    def _get_content_type(self, file_extension: str) -> ContentType:
        """Determine content type from file extension"""
        image_exts = ["jpg", "jpeg", "png", "gif", "webp"]
        video_exts = ["mp4", "avi", "mov", "mkv"]
        doc_exts = ["pdf", "doc", "docx", "txt"]
        
        if file_extension in image_exts:
            return ContentType.IMAGE
        elif file_extension in video_exts:
            return ContentType.VIDEO
        elif file_extension in doc_exts:
            return ContentType.DOCUMENT
        else:
            return ContentType.TEXT


# Global service instance
onboarding_service = OnboardingService()