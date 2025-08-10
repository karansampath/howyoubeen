"""
Onboarding API routes

Handles the multi-step user onboarding process:
1. Start onboarding session
2. Submit basic info (name, bio)
3. Add data sources and upload documents  
4. Configure visibility categories
5. Process user data
6. Get status and results
"""

import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from ...ai_engine.onboarding_service import onboarding_service
from ...integrations.mock_services import mock_services
from ...storage.storage_factory import get_storage_service

router = APIRouter()
logger = logging.getLogger(__name__)


# Request/Response Models
class StartOnboardingResponse(BaseModel):
    session_id: str
    message: str


class BasicInfoRequest(BaseModel):
    session_id: str
    full_name: str
    bio: str
    username: str
    email: str


class BasicInfoResponse(BaseModel):
    success: bool
    message: str
    next_step: str


class DataSourceRequest(BaseModel):
    session_id: str
    platform: str
    credentials: Dict[str, str] = {}  # For demo, we don't need real credentials


class DataSourceResponse(BaseModel):
    success: bool
    message: str
    source_id: Optional[str] = None


class VisibilityConfigRequest(BaseModel):
    session_id: str
    categories: List[Dict[str, Any]]


class VisibilityConfigResponse(BaseModel):
    success: bool
    message: str


class ProcessRequest(BaseModel):
    session_id: str


class ProcessResponse(BaseModel):
    success: bool
    user_id: Optional[str] = None
    profile_url: Optional[str] = None
    ai_summary: Optional[str] = None
    next_steps: List[str] = []
    error: Optional[str] = None


@router.post("/start", response_model=StartOnboardingResponse)
async def start_onboarding():
    """Start a new onboarding session"""
    try:
        session_id = await onboarding_service.start_onboarding()
        return StartOnboardingResponse(
            session_id=session_id,
            message="Onboarding session started successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start onboarding: {str(e)}")


@router.post("/basic-info", response_model=BasicInfoResponse)
async def submit_basic_info(request: BasicInfoRequest):
    """Submit basic user information (step a & b)"""
    try:
        success = await onboarding_service.submit_basic_info(
            session_id=request.session_id,
            name=request.full_name,
            bio=request.bio,
            username=request.username,
            email=request.email
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to save basic info. Username may already exist.")
        
        return BasicInfoResponse(
            success=True,
            message="Basic information saved successfully",
            next_step="data_sources"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving basic info: {str(e)}")


@router.post("/data-source", response_model=DataSourceResponse)
async def add_data_source(request: DataSourceRequest):
    """Add a data source connection (part of step c)"""
    try:
        info_source = await onboarding_service.add_data_source(
            session_id=request.session_id,
            platform=request.platform,
            credentials=request.credentials
        )
        
        if not info_source:
            raise HTTPException(status_code=400, detail=f"Failed to connect to {request.platform}")
        
        return DataSourceResponse(
            success=True,
            message=f"Successfully connected to {request.platform}",
            source_id=info_source.source_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error connecting data source: {str(e)}")


@router.post("/upload-document")
async def upload_document(
    session_id: str = Form(...),
    description: str = Form(""),
    file: UploadFile = File(...)
):
    """Upload a document (part of step c)"""
    try:
        # Read file content
        file_content = await file.read()
        
        document = await onboarding_service.upload_document(
            session_id=session_id,
            file_content=file_content,
            filename=file.filename or "unknown",
            description=description
        )
        
        if not document:
            raise HTTPException(status_code=400, detail="Failed to upload document")
        
        return {
            "success": True,
            "message": f"Document '{file.filename}' uploaded successfully",
            "document_id": document.document_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")


@router.post("/visibility-config", response_model=VisibilityConfigResponse)
async def configure_visibility(request: VisibilityConfigRequest):
    """Configure visibility categories (step d)"""
    try:
        success = await onboarding_service.configure_visibility(
            session_id=request.session_id,
            visibility_categories=request.categories
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to configure visibility settings")
        
        return VisibilityConfigResponse(
            success=True,
            message="Visibility categories configured successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error configuring visibility: {str(e)}")


# External Data Source Routes

class GitHubConnectRequest(BaseModel):
    session_id: str
    username: str
    github_token: Optional[str] = None


class WebsiteConnectRequest(BaseModel):
    session_id: str
    url: str


class ExternalSourceResponse(BaseModel):
    success: bool
    platform: str
    message: str
    summary: Optional[Dict[str, Any]] = None


@router.post("/connect-github", response_model=ExternalSourceResponse)
async def connect_github(request: GitHubConnectRequest):
    """Connect GitHub data source during onboarding"""
    try:
        result = await onboarding_service.connect_github(
            session_id=request.session_id,
            username=request.username,
            github_token=request.github_token
        )
        
        if not result["success"]:
            logger.error(f"GitHub connection failed: {result}")
            raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
        
        return ExternalSourceResponse(
            success=True,
            platform="github",
            message=f"Successfully connected GitHub profile for {request.username}",
            summary=result["summary"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error connecting GitHub: {str(e)}")


@router.post("/connect-website", response_model=ExternalSourceResponse)
async def connect_website(request: WebsiteConnectRequest):
    """Connect website data source during onboarding"""
    try:
        # Get Firecrawl API key from environment or settings
        import os
        firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
        if not firecrawl_api_key:
            # For debugging, create a mock response
            logger.warning("Firecrawl API key not configured, using mock response")
            return ExternalSourceResponse(
                success=True,
                platform="website",
                message=f"Mock: Successfully scraped content from {request.url}",
                summary={
                    "pages_scraped": 1,
                    "content_length": 500,
                    "entries_generated": 1,
                    "facts_generated": 1
                }
            )
        
        result = await onboarding_service.connect_website(
            session_id=request.session_id,
            url=request.url,
            firecrawl_api_key=firecrawl_api_key
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return ExternalSourceResponse(
            success=True,
            platform="website",
            message=f"Successfully scraped content from {request.url}",
            summary=result["summary"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error connecting website: {str(e)}")


@router.get("/external-sources/{session_id}")
async def get_external_sources(session_id: str):
    """Get list of connected external data sources for a session"""
    try:
        sources = await onboarding_service.get_external_data_sources(session_id)
        return {
            "session_id": session_id,
            "external_sources": sources,
            "count": len(sources)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting external sources: {str(e)}")


@router.post("/process", response_model=ProcessResponse)
async def process_user_data(request: ProcessRequest):
    """Process all user data and generate profile (step e)"""
    try:
        result = await onboarding_service.process_user_data(request.session_id)
        
        if not result.get("success"):
            return ProcessResponse(
                success=False,
                error=result.get("error", "Unknown error during processing")
            )
        
        return ProcessResponse(
            success=True,
            user_id=result.get("user_id"),
            profile_url=result.get("profile_url"),
            ai_summary=result.get("ai_summary"),
            next_steps=result.get("next_steps", [])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing user data: {str(e)}")


@router.get("/status/{session_id}")
async def get_onboarding_status(session_id: str):
    """Get current onboarding status"""
    try:
        status = await onboarding_service.get_onboarding_status(session_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Onboarding session not found")
        
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}")


@router.get("/available-platforms")
async def get_available_platforms():
    """Get list of available data source platforms"""
    try:
        platforms = mock_services.get_available_platforms()
        return {
            "platforms": platforms,
            "descriptions": {
                "goodreads": "Connect your reading list and book reviews",
                "google_photos": "Import recent photos and memories",
                "linkedin": "Add professional profile information",
                "github": "Include your code repositories and projects",
                "instagram": "Share recent social media updates"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting platforms: {str(e)}")


@router.get("/user/{user_id}")
async def get_user_profile(user_id: str):
    """Get user profile (for testing)"""
    try:
        storage = get_storage_service()
        user = await storage.get_user(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get counts from storage
        diary_entries = await storage.get_diary_entries_for_user(user_id)
        life_facts = await storage.get_life_facts_for_user(user_id)
        info_sources = await storage.get_info_sources_for_user(user_id)
        
        return {
            "user_id": user["id"],
            "username": user["username"],
            "full_name": user["full_name"],
            "bio": user["bio"],
            "onboarding_completed": user["onboarding_completed"],
            "diary_entries_count": len(diary_entries),
            "facts_count": len(life_facts),
            "sources_count": len(info_sources)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user profile: {str(e)}")


@router.delete("/session/{session_id}")
async def cleanup_session(session_id: str):
    """Clean up onboarding session (for testing)"""
    try:
        storage = get_storage_service()
        session = await storage.get_onboarding_session(session_id)
        if session:
            # For now, just return success - actual deletion could be implemented
            # in the storage service if needed for production
            return {"message": "Session cleanup requested successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cleaning up session: {str(e)}")