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

from ..data_models.models import User, Document, InfoSource, VisibilityCategory, FriendshipTier, LifeEvent
from ..data_models.enums import ContentType, VisibilityCategoryType
from ..storage.storage_service import StorageService
from ..storage.storage_factory import get_storage_service
from ..integrations.mock_services import mock_services
from .document_processor import document_processor, profile_generator
from .external_data_processor import ExternalDataProcessor, ProcessedExternalData


class OnboardingService:
    """Service to handle user onboarding process"""
    
    def __init__(self, storage: Optional[StorageService] = None):
        """
        Initialize onboarding service
        
        Args:
            storage: Optional storage service. If not provided, will use factory to auto-detect
        """
        self.storage = storage or get_storage_service()
    
    async def start_onboarding(self) -> str:
        """Start a new onboarding process"""
        # Generate temporary user ID for the session
        temp_user_id = str(uuid4())
        session_id = await self.storage.create_onboarding_session(user_id=temp_user_id)
        return session_id
    
    async def submit_basic_info(self, session_id: str, name: str, bio: str, username: str, email: str) -> bool:
        """Submit basic user information (step a & b)"""
        session = await self.storage.get_onboarding_session(session_id)
        if not session:
            return False
        
        # Validate username and email are unique
        existing_user = await self.storage.get_user_by_username(username)
        if existing_user:
            return False
        
        existing_email = await self.storage.get_user_by_email(email)
        if existing_email:
            return False
        
        basic_info = {
            "full_name": name,
            "bio": bio,
            "username": username,
            "email": email
        }
        
        await self.storage.update_onboarding_session(session_id, {"basic_info": basic_info})
        await self.storage.set_onboarding_step(session_id, "basic_info_complete")
        return True
    
    async def add_data_source(self, session_id: str, platform: str, credentials: Dict[str, str]) -> Optional[InfoSource]:
        """Add a data source connection (step c)"""
        session = await self.storage.get_onboarding_session(session_id)
        if not session:
            return None
        
        service = mock_services.get_service(platform)
        if not service:
            return None
        
        try:
            user_id = session.get("user_id")
            if not user_id:
                return None
                
            info_source = await service.connect(user_id, credentials)
            
            # Store the connection
            current_sources = session.get("data", {}).get("data_sources", [])
            current_sources.append({
                "platform": info_source.platform,
                "url": info_source.url,
                "description": info_source.info_description,
                "source_id": info_source.source_id,
                "user_id": user_id
            })
            
            await self.storage.update_onboarding_session(session_id, {"data_sources": current_sources})
            return info_source
            
        except Exception as e:
            print(f"Error connecting to {platform}: {e}")
            return None
    
    async def upload_document(self, session_id: str, file_content: bytes, filename: str, description: str = "") -> Optional[Document]:
        """Upload and process a document (step c)"""
        session = await self.storage.get_onboarding_session(session_id)
        if not session:
            return None
        
        user_id = session.get("user_id")
        if not user_id:
            return None
        
        try:
            # Save the uploaded file
            file_result = await self.storage.save_file(user_id, file_content, filename, description)
            
            # Determine content type
            ext = filename.split('.')[-1].lower() if '.' in filename else ''
            content_type = self._get_content_type(ext)
            
            # Create document record using the new storage interface
            document_data = {
                "user_id": user_id,
                "filename": filename,
                "file_path": file_result["file_path"],
                "file_size": file_result["file_size"],
                "content_type": content_type.value,
                "description": description or f"Uploaded file: {filename}"
            }
            
            document_record = await self.storage.create_document(document_data)
            
            # Create Document model for compatibility
            document = Document(
                document_id=document_record["id"],
                file_path=file_result["file_path"],
                content_type=content_type,
                description=description or f"Uploaded file: {filename}"
            )
            
            # Store in session
            current_docs = session.get("data", {}).get("uploaded_documents", [])
            current_docs.append({
                "document_id": document.document_id,
                "filename": filename,
                "description": description,
                "content_type": content_type.value
            })
            
            await self.storage.update_onboarding_session(session_id, {"uploaded_documents": current_docs})
            return document
            
        except Exception as e:
            print(f"Error uploading document: {e}")
            return None
    
    async def configure_visibility(self, session_id: str, visibility_categories: List[Dict[str, Any]]) -> bool:
        """Configure visibility categories (step d)"""
        session = await self.storage.get_onboarding_session(session_id)
        if not session:
            return False
        
        user_id = session.get("user_id")
        if not user_id:
            return False
        
        try:
            # Convert to VisibilityCategory objects for session storage
            categories = []
            for cat_data in visibility_categories:
                category = VisibilityCategory(
                    type=VisibilityCategoryType(cat_data["type"]),
                    name=cat_data.get("name"),
                    also_visible=[]  # Simplified for now
                )
                categories.append(category)
            
            # Store categories in the storage backend
            category_data = []
            for cat in categories:
                category_data.append({
                    "name": cat.name or str(cat.type),
                    "type": str(cat.type),
                    "description": f"Visibility level: {str(cat.type)}"
                })
            
            await self.storage.create_visibility_categories(user_id, category_data)
            
            await self.storage.update_onboarding_session(session_id, {
                "visibility_categories": [cat.dict() for cat in categories]
            })
            await self.storage.set_onboarding_step(session_id, "visibility_configured")
            return True
            
        except Exception as e:
            print(f"Error configuring visibility: {e}")
            return False
    
    async def process_user_data(self, session_id: str) -> Dict[str, Any]:
        """Process all user data and generate profile (step e)"""
        session = await self.storage.get_onboarding_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}
        
        try:
            await self.storage.set_onboarding_step(session_id, "processing")
            
            # Get session data
            session_data = session.get("data", {})
            basic_info = session_data.get("basic_info", {})
            user_id = session.get("user_id")
            
            if not user_id:
                return {"success": False, "error": "No user ID in session"}
            
            # Create the user
            user_data = {
                "username": basic_info.get("username", f"user_{user_id[:8]}"),
                "email": basic_info.get("email", ""),
                "full_name": basic_info.get("full_name", ""),
                "bio": basic_info.get("bio", ""),
                "onboarding_completed": False
            }
            
            user = await self.storage.create_user(user_data)
            
            # Set the user ID in the session for future reference
            await self.storage.set_onboarding_user_id(session_id, user["id"])
            actual_user_id = user["id"]
            
            # Process documents
            extracted_data = []
            uploaded_docs = session_data.get("uploaded_documents", [])
            
            for doc_info in uploaded_docs:
                # Documents are already created in storage, just process them
                processing_result = await self._process_document_for_extraction(doc_info)
                if processing_result:
                    extracted_data.append(processing_result)
            
            # Process data from external sources
            data_sources = session_data.get("data_sources", [])
            for source_info in data_sources:
                # Create info source record in storage
                source_data = {
                    "user_id": actual_user_id,
                    "platform": source_info["platform"],
                    "url": source_info.get("url", ""),
                    "description": source_info.get("description", f"Data from {source_info['platform']}"),
                    "source_id": source_info.get("source_id", str(uuid4()))
                }
                await self.storage.create_info_source(source_data)
                
                # Process the source data
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
            
            # Generate diary entries and life facts from documents
            life_events = await profile_generator.generate_life_events(extracted_data, visibility_categories)
            life_facts = await profile_generator.generate_life_facts(extracted_data, visibility_categories)
            
            # Add external data entries and facts
            external_events = session_data.get("external_life_events", [])
            external_facts = session_data.get("external_life_facts", [])
            
            for external_event in external_events:
                event_data = external_event["event_data"]
                event = LifeEvent(**event_data)
                life_events.append(event)
            
            for external_fact in external_facts:
                fact_data = external_fact["fact_data"]
                fact = LifeFact(**fact_data)
                life_facts.append(fact)
            
            # Store diary entries and life facts in storage
            for entry in life_events:
                visibility_str = 'public'
                if entry.visibility:
                    visibility_str = entry.visibility.type.value if hasattr(entry.visibility.type, 'value') else str(entry.visibility.type)
                
                entry_data = {
                    "user_id": actual_user_id,
                    "summary": entry.summary,
                    "content": getattr(entry, 'content', ''),
                    "visibility": visibility_str,
                    "date": entry.start_date.isoformat() if hasattr(entry, 'start_date') and entry.start_date else datetime.now().isoformat()
                }
                await self.storage.create_life_event(entry_data)
            
            for fact in life_facts:
                visibility_str = 'public'
                if fact.visibility:
                    visibility_str = fact.visibility.type.value if hasattr(fact.visibility.type, 'value') else str(fact.visibility.type)
                    
                fact_data = {
                    "user_id": actual_user_id,
                    "summary": fact.summary,
                    "description": getattr(fact, 'description', ''),
                    "category": getattr(fact, 'category', 'general'),
                    "visibility": visibility_str
                }
                await self.storage.create_life_fact(fact_data)
            
            # Generate AI summary
            summary_data = {
                "full_name": user["full_name"],
                "bio": user["bio"], 
                "sources": data_sources,
                "documents": uploaded_docs
            }
            ai_summary = await profile_generator.generate_user_summary(summary_data)
            
            # Mark user onboarding as completed
            await self.storage.update_user(actual_user_id, {
                "onboarding_completed": True
            })
            
            await self.storage.set_onboarding_step(session_id, "completed")
            
            return {
                "success": True,
                "user_id": actual_user_id,
                "profile_url": f"/profile/{user['username']}",
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
        session = await self.storage.get_onboarding_session(session_id)
        if not session:
            return None
        
        session_data = session.get("data", {})
        
        return {
            "session_id": session_id,
            "step": session.get("step", "start"),
            "created_at": session.get("created_at"),
            "updated_at": session.get("updated_at"),
            "data_summary": {
                "has_basic_info": "basic_info" in session_data,
                "data_sources_count": len(session_data.get("data_sources", [])),
                "documents_count": len(session_data.get("uploaded_documents", [])),
                "external_sources_count": len(session_data.get("external_data_sources", [])),
                "has_visibility_config": "visibility_categories" in session_data
            }
        }
    
    # External Data Source Methods
    
    async def connect_github(
        self, 
        session_id: str, 
        username: str, 
        github_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Connect and process GitHub data source
        
        Args:
            session_id: Onboarding session ID
            username: GitHub username
            github_token: Optional GitHub personal access token
            
        Returns:
            Dictionary with connection status and processing results
        """
        session = await self.storage.get_onboarding_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}
        
        try:
            # Get visibility configuration
            session_data = session.get("data", {})
            visibility_cats = session_data.get("visibility_categories", [])
            visibility_categories = [VisibilityCategory(**cat) for cat in visibility_cats] if visibility_cats else []
            
            # Process GitHub data using external data processor
            processor = ExternalDataProcessor()
            processed_data = await processor.process_github_data(
                username=username,
                visibility_config=visibility_categories,
                github_token=github_token
            )
            
            # Store processed data in session
            current_external_data = session_data.get("external_data_sources", [])
            current_external_data.append({
                "platform": "github",
                "username": username,
                "connected_at": datetime.now().isoformat(),
                "events_count": len(processed_data.life_events),
                "facts_count": len(processed_data.life_facts),
                "processing_summary": processed_data.processing_summary
            })
            
            await self.storage.update_onboarding_session(session_id, {
                "external_data_sources": current_external_data
            })
            
            # Store the actual life events and life facts for later use in process_user_data
            await self._store_processed_external_data(session_id, processed_data)
            
            return {
                "success": True,
                "platform": "github",
                "username": username,
                "summary": processed_data.processing_summary
            }
            
        except Exception as e:
            return {"success": False, "error": f"GitHub connection failed: {str(e)}"}
    
    async def connect_website(
        self, 
        session_id: str, 
        url: str,
        firecrawl_api_key: str
    ) -> Dict[str, Any]:
        """
        Connect and process website data source
        
        Args:
            session_id: Onboarding session ID
            url: Website URL to scrape
            firecrawl_api_key: Firecrawl API key
            
        Returns:
            Dictionary with connection status and processing results
        """
        session = await self.storage.get_onboarding_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}
        
        try:
            # Get visibility configuration
            session_data = session.get("data", {})
            visibility_cats = session_data.get("visibility_categories", [])
            visibility_categories = [VisibilityCategory(**cat) for cat in visibility_cats] if visibility_cats else []
            
            # Process website data using external data processor
            processor = ExternalDataProcessor()
            processed_data = await processor.process_website_data(
                url=url,
                visibility_config=visibility_categories,
                firecrawl_api_key=firecrawl_api_key
            )
            
            # Store processed data in session
            current_external_data = session_data.get("external_data_sources", [])
            current_external_data.append({
                "platform": "website",
                "url": url,
                "connected_at": datetime.now().isoformat(),
                "events_count": len(processed_data.life_events),
                "facts_count": len(processed_data.life_facts),
                "processing_summary": processed_data.processing_summary
            })
            
            await self.storage.update_onboarding_session(session_id, {
                "external_data_sources": current_external_data
            })
            
            # Store the actual life events and life facts for later use in process_user_data
            await self._store_processed_external_data(session_id, processed_data)
            
            return {
                "success": True,
                "platform": "website",
                "url": url,
                "summary": processed_data.processing_summary
            }
            
        except Exception as e:
            return {"success": False, "error": f"Website connection failed: {str(e)}"}
    
    async def get_external_data_sources(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get list of connected external data sources for a session
        
        Args:
            session_id: Onboarding session ID
            
        Returns:
            List of connected external data sources
        """
        session = await self.storage.get_onboarding_session(session_id)
        if not session:
            return []
        
        session_data = session.get("data", {})
        return session_data.get("external_data_sources", [])
    
    async def _store_processed_external_data(
        self, 
        session_id: str, 
        processed_data: ProcessedExternalData
    ) -> None:
        """
        Store processed external data in session for later use
        
        Args:
            session_id: Onboarding session ID
            processed_data: Processed external data to store
        """
        print(f"[DEBUG] Storing processed external data for session: {session_id}")
        print(f"[DEBUG] Platform: {processed_data.platform}, Events: {len(processed_data.life_events)}, Facts: {len(processed_data.life_facts)}")
        
        session = await self.storage.get_onboarding_session(session_id)
        if not session:
            print(f"[DEBUG] ERROR: Session not found: {session_id}")
            return
        
        session_data = session.get("data", {})
        
        # Store life events
        stored_events = session_data.get("external_life_events", [])
        print(f"[DEBUG] Processing {len(processed_data.life_events)} life events for JSON storage...")
        
        for i, event in enumerate(processed_data.life_events):
            print(f"[DEBUG] Processing life event {i+1}: {event.summary[:50]}...")
            
            # Convert to dict with JSON serialization for datetime objects
            try:
                event_dict = event.dict()
                print(f"[DEBUG] Event dict keys: {list(event_dict.keys())}")
                
                # Manually handle datetime serialization
                if "start_date" in event_dict and event_dict["start_date"]:
                    print(f"[DEBUG] Converting start_date: {event_dict['start_date']} (type: {type(event_dict['start_date'])})")
                    event_dict["start_date"] = event_dict["start_date"].isoformat() if hasattr(event_dict["start_date"], "isoformat") else event_dict["start_date"]
                if "end_date" in event_dict and event_dict["end_date"]:
                    event_dict["end_date"] = event_dict["end_date"].isoformat() if hasattr(event_dict["end_date"], "isoformat") else event_dict["end_date"]
                if "created_at" in event_dict and event_dict["created_at"]:
                    event_dict["created_at"] = event_dict["created_at"].isoformat() if hasattr(event_dict["created_at"], "isoformat") else event_dict["created_at"]
                if "updated_at" in event_dict and event_dict["updated_at"]:
                    event_dict["updated_at"] = event_dict["updated_at"].isoformat() if hasattr(event_dict["updated_at"], "isoformat") else event_dict["updated_at"]
                
                # Handle nested visibility category datetime fields
                if "visibility" in event_dict and event_dict["visibility"]:
                    visibility = event_dict["visibility"]
                    print(f"[DEBUG] Processing visibility: {type(visibility)}")
                    if isinstance(visibility, dict):
                        for key, value in visibility.items():
                            if hasattr(value, "isoformat"):
                                print(f"[DEBUG] Converting visibility.{key}: {value}")
                                visibility[key] = value.isoformat()
                
                stored_events.append({
                    "platform": processed_data.platform,
                    "event_data": event_dict,
                    "created_at": datetime.now().isoformat()
                })
                print(f"[DEBUG] Successfully processed life event {i+1}")
                
            except Exception as e:
                print(f"[DEBUG] ERROR processing life event {i+1}: {e}")
                raise
        
        # Store life facts
        stored_facts = session_data.get("external_life_facts", [])
        for fact in processed_data.life_facts:
            # Convert to dict with JSON serialization for datetime objects
            fact_dict = fact.dict()
            # Manually handle datetime serialization
            if "date" in fact_dict and fact_dict["date"]:
                fact_dict["date"] = fact_dict["date"].isoformat() if hasattr(fact_dict["date"], "isoformat") else fact_dict["date"]
            if "created_at" in fact_dict and fact_dict["created_at"]:
                fact_dict["created_at"] = fact_dict["created_at"].isoformat() if hasattr(fact_dict["created_at"], "isoformat") else fact_dict["created_at"]
            if "updated_at" in fact_dict and fact_dict["updated_at"]:
                fact_dict["updated_at"] = fact_dict["updated_at"].isoformat() if hasattr(fact_dict["updated_at"], "isoformat") else fact_dict["updated_at"]
            
            # Handle nested visibility category datetime fields
            if "visibility" in fact_dict and fact_dict["visibility"]:
                visibility = fact_dict["visibility"]
                if isinstance(visibility, dict):
                    for key, value in visibility.items():
                        if hasattr(value, "isoformat"):
                            visibility[key] = value.isoformat()
            
            stored_facts.append({
                "platform": processed_data.platform,
                "fact_data": fact_dict,
                "created_at": datetime.now().isoformat()
            })
        
        await self.storage.update_onboarding_session(session_id, {
            "external_life_events": stored_events,
            "external_life_facts": stored_facts
        })
    
    # Helper Methods
    
    async def _process_document_for_extraction(self, doc_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a document for data extraction"""
        try:
            # Mock document processing for now
            # In a real implementation, this would extract text/data from the document
            return {
                "type": "document",
                "filename": doc_info.get("filename"),
                "description": doc_info.get("description", ""),
                "content_type": doc_info.get("content_type"),
                "extracted_data": f"Content from {doc_info.get('filename', 'unknown file')}"
            }
        except Exception as e:
            print(f"Error processing document for extraction: {e}")
            return None
    
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


# Global service instance - will use storage factory to auto-detect backend
onboarding_service = OnboardingService()