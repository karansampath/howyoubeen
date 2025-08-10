"""
Supabase-integrated onboarding API routes

Updated routes that use Supabase for data persistence instead of in-memory storage.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import logging

from ...ai_engine.supabase_onboarding_service import supabase_onboarding_service
from ...integrations.mock_services import mock_services
from ...storage.repositories import UserRepository
from ...storage.supabase_storage import upload_user_file, get_user_file_url

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize repositories
user_repo = UserRepository(use_service_key=True)


# Request/Response Models (same as before)
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
    credentials: Dict[str, str] = {}


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
    """Start a new onboarding session using Supabase"""
    try:
        session_id = await supabase_onboarding_service.start_onboarding()
        logger.info(f"Started Supabase onboarding session: {session_id}")
        
        return StartOnboardingResponse(
            session_id=session_id,
            message="Onboarding session started successfully with Supabase"
        )
    except Exception as e:
        logger.error(f"Failed to start Supabase onboarding: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start onboarding: {str(e)}")


@router.post("/basic-info", response_model=BasicInfoResponse)
async def submit_basic_info(request: BasicInfoRequest):
    """Submit basic user information (step a & b)"""
    try:
        success = await supabase_onboarding_service.submit_basic_info(
            session_id=request.session_id,
            name=request.full_name,
            bio=request.bio,
            username=request.username,
            email=request.email
        )
        
        if not success:
            raise HTTPException(
                status_code=400, 
                detail="Failed to save basic info. Username or email may already exist."
            )
        
        logger.info(f"Submitted basic info for session {request.session_id}")
        
        return BasicInfoResponse(
            success=True,
            message="Basic information saved successfully to Supabase",
            next_step="data_sources"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving basic info: {e}")
        raise HTTPException(status_code=500, detail=f"Error saving basic info: {str(e)}")


@router.post("/data-source", response_model=DataSourceResponse)
async def add_data_source(request: DataSourceRequest):
    """Add a data source connection (part of step c)"""
    try:
        info_source = await supabase_onboarding_service.add_data_source(
            session_id=request.session_id,
            platform=request.platform,
            credentials=request.credentials
        )
        
        if not info_source:
            raise HTTPException(status_code=400, detail=f"Failed to connect to {request.platform}")
        
        logger.info(f"Connected {request.platform} for session {request.session_id}")
        
        return DataSourceResponse(
            success=True,
            message=f"Successfully connected to {request.platform} via Supabase",
            source_id=info_source.source_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error connecting data source: {e}")
        raise HTTPException(status_code=500, detail=f"Error connecting data source: {str(e)}")


@router.post("/upload-document")
async def upload_document(
    session_id: str = Form(...),
    description: str = Form(""),
    file: UploadFile = File(...)
):
    """Upload a document (part of step c) - Enhanced with Supabase Storage"""
    try:
        # Read file content
        file_content = await file.read()
        
        # Get session data to determine user (for storage organization)
        session_data = await supabase_onboarding_service.onboarding_repo.get_session_data(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Onboarding session not found")
        
        # For now, use session_id as user_id for storage path
        # In production, this would be the actual user_id once user is created
        storage_user_id = session_data.get("user_id") or session_id
        
        # Upload to Supabase Storage (optional - can still use local storage during onboarding)
        # storage_result = await upload_user_file(storage_user_id, file_content, file.filename or "document")
        
        # Use the service to handle the upload
        document = await supabase_onboarding_service.upload_document(
            session_id=session_id,
            file_content=file_content,
            filename=file.filename or "unknown",
            description=description
        )
        
        if not document:
            raise HTTPException(status_code=400, detail="Failed to upload document")
        
        logger.info(f"Uploaded document {file.filename} to session {session_id}")
        
        return {
            "success": True,
            "message": f"Document '{file.filename}' uploaded successfully to Supabase",
            "document_id": document.document_id,
            "file_size": len(file_content)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")


@router.post("/visibility-config", response_model=VisibilityConfigResponse)
async def configure_visibility(request: VisibilityConfigRequest):
    """Configure visibility categories (step d)"""
    try:
        success = await supabase_onboarding_service.configure_visibility(
            session_id=request.session_id,
            visibility_categories=request.categories
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to configure visibility settings")
        
        logger.info(f"Configured visibility for session {request.session_id}")
        
        return VisibilityConfigResponse(
            success=True,
            message="Visibility categories configured successfully in Supabase"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error configuring visibility: {e}")
        raise HTTPException(status_code=500, detail=f"Error configuring visibility: {str(e)}")


@router.post("/process", response_model=ProcessResponse)
async def process_user_data(request: ProcessRequest):
    """Process all user data and generate profile (step e) - Full Supabase integration"""
    try:
        logger.info(f"Processing user data for session {request.session_id}")
        
        result = await supabase_onboarding_service.process_user_data(request.session_id)
        
        if not result.get("success"):
            return ProcessResponse(
                success=False,
                error=result.get("error", "Unknown error during processing")
            )
        
        logger.info(f"Successfully processed user data: {result.get('user_id')}")
        
        return ProcessResponse(
            success=True,
            user_id=result.get("user_id"),
            profile_url=result.get("profile_url"),
            ai_summary=result.get("ai_summary"),
            next_steps=result.get("next_steps", [])
        )
    except Exception as e:
        logger.error(f"Error processing user data: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing user data: {str(e)}")


@router.get("/status/{session_id}")
async def get_onboarding_status(session_id: str):
    """Get current onboarding status"""
    try:
        status = await supabase_onboarding_service.get_onboarding_status(session_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Onboarding session not found")
        
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting status: {e}")
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
            },
            "storage_backend": "supabase"
        }
    except Exception as e:
        logger.error(f"Error getting platforms: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting platforms: {str(e)}")


@router.get("/user/{user_id}")
async def get_user_profile(user_id: str):
    """Get user profile from Supabase"""
    try:
        user = await user_repo.get_user_with_related_data(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "user_id": user["id"],
            "username": user["username"],
            "full_name": user["full_name"],
            "bio": user["bio"],
            "onboarding_completed": user["onboarding_completed"],
            "visibility_categories_count": len(user.get("visibility_categories", [])),
            "diary_entries_count": len(user.get("diary_entries", [])),
            "facts_count": len(user.get("life_facts", [])),
            "sources_count": len(user.get("info_sources", [])),
            "friends_count": len(user.get("friends", [])),
            "storage_backend": "supabase"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting user profile: {str(e)}")


@router.get("/user/{user_id}/files")
async def get_user_files(user_id: str):
    """Get user's uploaded files"""
    try:
        # Verify user exists
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get documents from database
        from ...storage.repositories import DocumentRepository
        doc_repo = DocumentRepository()
        documents = await doc_repo.get_documents_for_user(user_id)
        
        # Add signed URLs for file access
        for doc in documents:
            if doc.get("file_path"):
                signed_url = await get_user_file_url(doc["file_path"], expires_in=3600)
                doc["signed_url"] = signed_url
        
        return {
            "user_id": user_id,
            "documents": documents,
            "total_count": len(documents)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user files: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting user files: {str(e)}")


@router.delete("/session/{session_id}")
async def cleanup_session(session_id: str):
    """Clean up onboarding session"""
    try:
        session_data = await supabase_onboarding_service.onboarding_repo.get_session_data(session_id)
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Delete session from Supabase
        success = await supabase_onboarding_service.onboarding_repo.delete(session_id)
        
        if success:
            logger.info(f"Cleaned up Supabase session: {session_id}")
            return {"message": "Session cleaned up successfully from Supabase"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete session")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning up session: {e}")
        raise HTTPException(status_code=500, detail=f"Error cleaning up session: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check for Supabase onboarding service"""
    try:
        # Test Supabase connection
        from ...storage.supabase_client import get_supabase_client
        
        client = get_supabase_client(use_service_key=True)
        connection_ok = client.test_connection()
        
        return {
            "status": "healthy" if connection_ok else "degraded",
            "service": "supabase-onboarding-api",
            "supabase_connection": connection_ok,
            "timestamp": "now()"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "supabase-onboarding-api",
            "error": str(e),
            "timestamp": "now()"
        }