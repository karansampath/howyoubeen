"""
Integration test for onboarding flow using local storage

Tests the complete onboarding process with LocalStorageService backend
"""

import asyncio
import json
import os
import tempfile
import pytest
from typing import Dict, Any

from keepintouch.ai_engine.onboarding_service import OnboardingService
from keepintouch.storage.local_storage_service import LocalStorageService


class TestOnboardingLocalStorage:
    """Integration test for onboarding with local storage"""
    
    @pytest.fixture
    async def storage_service(self):
        """Create a clean local storage service for testing"""
        # Create a temporary backup file for persistence during test
        temp_backup = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        temp_backup.close()
        
        storage = LocalStorageService(backup_file=temp_backup.name)
        
        yield storage
        
        # Cleanup
        storage.cleanup()
        if os.path.exists(temp_backup.name):
            os.unlink(temp_backup.name)
    
    @pytest.fixture
    async def onboarding_service(self, storage_service):
        """Create onboarding service with test storage"""
        return OnboardingService(storage=storage_service)
    
    async def test_complete_onboarding_flow(self, onboarding_service):
        """Test the complete onboarding flow from start to finish"""
        
        # Step 1: Start onboarding
        session_id = await onboarding_service.start_onboarding()
        assert session_id is not None
        assert len(session_id) > 0
        
        # Verify session was created
        session = await onboarding_service.storage.get_onboarding_session(session_id)
        assert session is not None
        assert session["step"] == "start"
        
        # Step 2: Submit basic info
        basic_info_success = await onboarding_service.submit_basic_info(
            session_id=session_id,
            name="John Doe",
            bio="Software developer who loves coding and coffee",
            username="johndoe123",
            email="john.doe@example.com"
        )
        assert basic_info_success is True
        
        # Verify basic info step completed
        session = await onboarding_service.storage.get_onboarding_session(session_id)
        assert session["step"] == "basic_info_complete"
        assert "basic_info" in session["data"]
        assert session["data"]["basic_info"]["username"] == "johndoe123"
        
        # Step 3: Add data sources (optional step)
        # Test LinkedIn connection
        linkedin_source = await onboarding_service.add_data_source(
            session_id=session_id,
            platform="linkedin",
            credentials={"access_token": "fake_token_linkedin"}
        )
        assert linkedin_source is not None
        assert linkedin_source.platform == "linkedin"
        
        # Test Goodreads connection
        goodreads_source = await onboarding_service.add_data_source(
            session_id=session_id,
            platform="goodreads",
            credentials={"user_id": "123456", "api_key": "fake_api_key"}
        )
        assert goodreads_source is not None
        assert goodreads_source.platform == "goodreads"
        
        # Verify data sources were added
        session = await onboarding_service.storage.get_onboarding_session(session_id)
        data_sources = session["data"].get("data_sources", [])
        assert len(data_sources) == 2
        
        # Step 4: Upload documents
        sample_pdf_content = b"%PDF-1.4 fake pdf content for testing"
        document = await onboarding_service.upload_document(
            session_id=session_id,
            file_content=sample_pdf_content,
            filename="resume.pdf",
            description="My updated resume"
        )
        assert document is not None
        assert "resume.pdf" in document.description
        
        # Upload another document
        sample_text_content = b"This is a sample text document with personal notes"
        text_document = await onboarding_service.upload_document(
            session_id=session_id,
            file_content=sample_text_content,
            filename="notes.txt",
            description="Personal notes"
        )
        assert text_document is not None
        
        # Verify documents were uploaded
        session = await onboarding_service.storage.get_onboarding_session(session_id)
        uploaded_docs = session["data"].get("uploaded_documents", [])
        assert len(uploaded_docs) == 2
        
        # Step 5: Configure visibility
        visibility_categories = [
            {"type": "public", "name": "Public Information"},
            {"type": "friends", "name": "Friends Only"},
            {"type": "private", "name": "Private Data"}
        ]
        
        visibility_success = await onboarding_service.configure_visibility(
            session_id=session_id,
            visibility_categories=visibility_categories
        )
        assert visibility_success is True
        
        # Verify visibility configuration
        session = await onboarding_service.storage.get_onboarding_session(session_id)
        assert session["step"] == "visibility_configured"
        assert "visibility_categories" in session["data"]
        
        # Step 6: Process user data and complete onboarding
        result = await onboarding_service.process_user_data(session_id)
        
        # Verify processing was successful
        assert result["success"] is True
        assert "user_id" in result
        assert "profile_url" in result
        assert "ai_summary" in result
        assert "next_steps" in result
        
        user_id = result["user_id"]
        
        # Verify user was created
        user = await onboarding_service.storage.get_user(user_id)
        assert user is not None
        assert user["username"] == "johndoe123"
        assert user["email"] == "john.doe@example.com"
        assert user["onboarding_completed"] is True
        
        # Verify final session state
        final_session = await onboarding_service.storage.get_onboarding_session(session_id)
        assert final_session["step"] == "completed"
        
        # Step 7: Test query methods to verify data was stored correctly
        
        # Test user queries
        user_by_username = await onboarding_service.storage.get_user_by_username("johndoe123")
        assert user_by_username is not None
        assert user_by_username["id"] == user_id
        
        user_by_email = await onboarding_service.storage.get_user_by_email("john.doe@example.com")
        assert user_by_email is not None
        assert user_by_email["id"] == user_id
        
        # Test document queries
        user_documents = await onboarding_service.storage.get_documents_for_user(user_id)
        assert len(user_documents) == 2
        
        # Test visibility categories
        visibility_cats = await onboarding_service.storage.get_visibility_categories(user_id)
        assert len(visibility_cats) == 3
        
        # Test info sources
        info_sources = await onboarding_service.storage.get_info_sources_for_user(user_id)
        assert len(info_sources) == 2
        
        # Test diary entries and life facts were created
        diary_entries = await onboarding_service.storage.get_diary_entries_for_user(user_id)
        life_facts = await onboarding_service.storage.get_life_facts_for_user(user_id)
        
        # Should have generated some content (exact count depends on mock generators)
        assert isinstance(diary_entries, list)
        assert isinstance(life_facts, list)
        
        # Test search functionality
        search_results = await onboarding_service.storage.search_user_content(
            user_id=user_id,
            query="resume"
        )
        assert "documents" in search_results
        
        # Test activity summary
        activity = await onboarding_service.storage.get_user_activity_summary(user_id, days=30)
        assert activity["user_id"] == user_id
        assert "activity_counts" in activity
        assert "total_counts" in activity
        
        print(f"✅ Complete onboarding flow test passed!")
        print(f"   User ID: {user_id}")
        print(f"   Documents: {len(user_documents)}")
        print(f"   Data sources: {len(info_sources)}")
        print(f"   Visibility categories: {len(visibility_cats)}")
        
        return result
    
    async def test_onboarding_status_tracking(self, onboarding_service):
        """Test that onboarding status is properly tracked throughout the process"""
        
        # Start onboarding
        session_id = await onboarding_service.start_onboarding()
        
        # Check initial status
        status = await onboarding_service.get_onboarding_status(session_id)
        assert status["step"] == "start"
        assert status["data_summary"]["has_basic_info"] is False
        assert status["data_summary"]["data_sources_count"] == 0
        assert status["data_summary"]["documents_count"] == 0
        
        # Submit basic info
        await onboarding_service.submit_basic_info(
            session_id=session_id,
            name="Test User",
            bio="Test bio",
            username="testuser",
            email="test@example.com"
        )
        
        # Check status after basic info
        status = await onboarding_service.get_onboarding_status(session_id)
        assert status["step"] == "basic_info_complete"
        assert status["data_summary"]["has_basic_info"] is True
        
        # Add a data source
        await onboarding_service.add_data_source(
            session_id=session_id,
            platform="linkedin",
            credentials={"access_token": "test_token"}
        )
        
        # Check status after data source
        status = await onboarding_service.get_onboarding_status(session_id)
        assert status["data_summary"]["data_sources_count"] == 1
        
        # Upload a document
        await onboarding_service.upload_document(
            session_id=session_id,
            file_content=b"test content",
            filename="test.txt"
        )
        
        # Check status after document upload
        status = await onboarding_service.get_onboarding_status(session_id)
        assert status["data_summary"]["documents_count"] == 1
    
    async def test_username_email_uniqueness(self, onboarding_service):
        """Test that username and email uniqueness is enforced"""
        
        # Create first user
        session_id1 = await onboarding_service.start_onboarding()
        success1 = await onboarding_service.submit_basic_info(
            session_id=session_id1,
            name="User One",
            bio="First user",
            username="uniqueuser",
            email="unique@example.com"
        )
        assert success1 is True
        
        # Try to create second user with same username
        session_id2 = await onboarding_service.start_onboarding()
        success2 = await onboarding_service.submit_basic_info(
            session_id=session_id2,
            name="User Two",
            bio="Second user",
            username="uniqueuser",  # Same username
            email="different@example.com"
        )
        assert success2 is False  # Should fail due to duplicate username
        
        # Try to create third user with same email
        session_id3 = await onboarding_service.start_onboarding()
        success3 = await onboarding_service.submit_basic_info(
            session_id=session_id3,
            name="User Three",
            bio="Third user", 
            username="differentuser",
            email="unique@example.com"  # Same email
        )
        assert success3 is False  # Should fail due to duplicate email
    
    async def test_storage_persistence(self, storage_service):
        """Test that data persists when using backup file"""
        
        # Create some test data
        onboarding_service = OnboardingService(storage=storage_service)
        
        session_id = await onboarding_service.start_onboarding()
        await onboarding_service.submit_basic_info(
            session_id=session_id,
            name="Persistent User",
            bio="Testing persistence",
            username="persistentuser",
            email="persistent@example.com"
        )
        
        # Get backup file path
        backup_file = storage_service.backup_file
        assert backup_file is not None
        
        # Verify backup file exists and contains data
        assert os.path.exists(backup_file)
        
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)
        
        # Should have session and user data
        assert len(backup_data.get("sessions", {})) >= 1
        assert session_id in backup_data["sessions"]
        
        # Create new storage service from same backup file
        new_storage = LocalStorageService(backup_file=backup_file)
        
        # Should be able to retrieve the session
        restored_session = await new_storage.get_onboarding_session(session_id)
        assert restored_session is not None
        assert restored_session["data"]["basic_info"]["username"] == "persistentuser"


# Async test runner function
async def run_integration_tests():
    """Run integration tests manually (for development)"""
    
    # Create test instance
    test_instance = TestOnboardingLocalStorage()
    
    # Set up storage
    temp_backup = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
    temp_backup.close()
    
    try:
        storage = LocalStorageService(backup_file=temp_backup.name)
        service = OnboardingService(storage=storage)
        
        print("🧪 Running onboarding integration tests with local storage...")
        
        # Run the main test
        result = await test_instance.test_complete_onboarding_flow(service)
        print("✅ Complete onboarding flow test: PASSED")
        
        # Run status tracking test
        await test_instance.test_onboarding_status_tracking(service)
        print("✅ Status tracking test: PASSED")
        
        # Run uniqueness test
        await test_instance.test_username_email_uniqueness(service)
        print("✅ Username/email uniqueness test: PASSED")
        
        # Run persistence test
        await test_instance.test_storage_persistence(storage)
        print("✅ Storage persistence test: PASSED")
        
        print("\n🎉 All integration tests passed!")
        return True
        
    finally:
        # Cleanup
        if 'storage' in locals():
            storage.cleanup()
        if os.path.exists(temp_backup.name):
            os.unlink(temp_backup.name)


if __name__ == "__main__":
    # Run tests directly
    asyncio.run(run_integration_tests())