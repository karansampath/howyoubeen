"""
Simple integration test for onboarding flow using local storage

A minimal test to verify the basic onboarding functionality works correctly.
"""

import asyncio
import os
import tempfile

from keepintouch.ai_engine.onboarding_service import OnboardingService
from keepintouch.storage.local_storage_service import LocalStorageService


async def test_basic_onboarding():
    """Test basic onboarding flow without external dependencies"""
    
    # Create temporary storage
    temp_backup = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
    temp_backup.close()
    
    try:
        # Create services
        storage = LocalStorageService(backup_file=temp_backup.name)
        onboarding_service = OnboardingService(storage=storage)
        
        print("🧪 Testing basic onboarding flow...")
        
        # Step 1: Start onboarding
        session_id = await onboarding_service.start_onboarding()
        print(f"✅ Started onboarding session: {session_id[:8]}...")
        
        # Step 2: Submit basic info
        basic_info_success = await onboarding_service.submit_basic_info(
            session_id=session_id,
            name="Test User",
            bio="Testing the onboarding system",
            username="testuser123",
            email="test@example.com"
        )
        print(f"✅ Basic info submitted: {basic_info_success}")
        
        # Step 3: Upload a simple document
        sample_content = b"This is a test document for the onboarding system"
        document = await onboarding_service.upload_document(
            session_id=session_id,
            file_content=sample_content,
            filename="test.txt",
            description="Test document"
        )
        print(f"✅ Document uploaded: {document is not None}")
        
        # Step 4: Configure basic visibility
        visibility_categories = [
            {"type": "public", "name": "Public Information"},
            {"type": "good_friends", "name": "Friends Only"}
        ]
        
        visibility_success = await onboarding_service.configure_visibility(
            session_id=session_id,
            visibility_categories=visibility_categories
        )
        print(f"✅ Visibility configured: {visibility_success}")
        
        # Step 5: Process user data (complete onboarding)
        result = await onboarding_service.process_user_data(session_id)
        print(f"✅ Onboarding processing: {result['success']}")
        
        if result["success"]:
            user_id = result["user_id"]
            print(f"✅ User created with ID: {user_id}")
            
            # Verify user exists
            user = await storage.get_user(user_id)
            print(f"✅ User retrieved: {user is not None}")
            print(f"   Username: {user['username']}")
            print(f"   Email: {user['email']}")
            print(f"   Onboarding complete: {user['onboarding_completed']}")
            
            # Check storage health
            health = await storage.health_check()
            print(f"✅ Storage health: {health['status']}")
            
            return True
        else:
            print(f"❌ Onboarding failed: {result.get('error', 'Unknown error')}")
            return False
    
    finally:
        # Cleanup
        if 'storage' in locals():
            storage.cleanup()
        if os.path.exists(temp_backup.name):
            os.unlink(temp_backup.name)


async def test_username_uniqueness():
    """Test that username uniqueness is enforced"""
    
    temp_backup = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
    temp_backup.close()
    
    try:
        storage = LocalStorageService(backup_file=temp_backup.name)
        onboarding_service = OnboardingService(storage=storage)
        
        print("🧪 Testing username uniqueness...")
        
        # Create first user completely
        session_id1 = await onboarding_service.start_onboarding()
        success1 = await onboarding_service.submit_basic_info(
            session_id=session_id1,
            name="User One",
            bio="First user",
            username="uniqueuser",
            email="user1@example.com"
        )
        
        # Complete the first user creation
        if success1:
            visibility_categories = [{"type": "public", "name": "Public Information"}]
            await onboarding_service.configure_visibility(session_id1, visibility_categories)
            result1 = await onboarding_service.process_user_data(session_id1)
            success1 = result1["success"]
        
        print(f"✅ First user created: {success1}")
        
        # Try to create second user with same username
        session_id2 = await onboarding_service.start_onboarding()
        success2 = await onboarding_service.submit_basic_info(
            session_id=session_id2,
            name="User Two",
            bio="Second user",
            username="uniqueuser",  # Same username
            email="user2@example.com"
        )
        print(f"✅ Duplicate username rejected: {not success2}")
        
        return success1 and not success2
        
    finally:
        if 'storage' in locals():
            storage.cleanup()
        if os.path.exists(temp_backup.name):
            os.unlink(temp_backup.name)


async def test_storage_queries():
    """Test storage query methods"""
    
    temp_backup = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
    temp_backup.close()
    
    try:
        storage = LocalStorageService(backup_file=temp_backup.name)
        onboarding_service = OnboardingService(storage=storage)
        
        print("🧪 Testing storage queries...")
        
        # Create a user first
        session_id = await onboarding_service.start_onboarding()
        await onboarding_service.submit_basic_info(
            session_id=session_id,
            name="Query Test User",
            bio="Testing query functionality",
            username="queryuser",
            email="query@example.com"
        )
        
        # Process to create the user
        result = await onboarding_service.process_user_data(session_id)
        if not result["success"]:
            print(f"❌ Failed to create user: {result.get('error')}")
            return False
        
        user_id = result["user_id"]
        
        # Test query methods
        user_by_username = await storage.get_user_by_username("queryuser")
        print(f"✅ Query by username: {user_by_username is not None}")
        
        user_by_email = await storage.get_user_by_email("query@example.com")
        print(f"✅ Query by email: {user_by_email is not None}")
        
        # Test activity summary
        activity = await storage.get_user_activity_summary(user_id, days=30)
        print(f"✅ Activity summary: {activity['user_id'] == user_id}")
        
        # Test search (should handle empty results gracefully)
        search_results = await storage.search_user_content(user_id, "test")
        print(f"✅ Search functionality: {isinstance(search_results, dict)}")
        
        return True
        
    finally:
        if 'storage' in locals():
            storage.cleanup()
        if os.path.exists(temp_backup.name):
            os.unlink(temp_backup.name)


async def run_simple_tests():
    """Run all simple tests"""
    
    print("🚀 Starting Simple Onboarding Tests")
    print("=" * 50)
    
    try:
        # Test 1: Basic onboarding flow
        test1_result = await test_basic_onboarding()
        print(f"Test 1 - Basic Onboarding: {'✅ PASSED' if test1_result else '❌ FAILED'}")
        
        # Test 2: Username uniqueness
        test2_result = await test_username_uniqueness()
        print(f"Test 2 - Username Uniqueness: {'✅ PASSED' if test2_result else '❌ FAILED'}")
        
        # Test 3: Storage queries
        test3_result = await test_storage_queries()
        print(f"Test 3 - Storage Queries: {'✅ PASSED' if test3_result else '❌ FAILED'}")
        
        all_passed = test1_result and test2_result and test3_result
        
        print("\n" + "=" * 50)
        if all_passed:
            print("🎉 All simple tests PASSED!")
        else:
            print("❌ Some tests FAILED!")
        
        return all_passed
        
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    exit_code = 0 if asyncio.run(run_simple_tests()) else 1
    exit(exit_code)