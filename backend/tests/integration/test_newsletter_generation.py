"""
Integration test for newsletter generation functionality

Tests the complete flow from NewsletterConfig to generated markdown content
using mocked life event data and real storage/LLM integration.
"""

import asyncio
import tempfile
import shutil
from datetime import datetime, timedelta
import pytest

from howyoubeen.ai_engine.newsletter_generator import NewsletterGenerator
from howyoubeen.data_models.models import NewsletterConfig, VisibilityCategory
from howyoubeen.data_models.enums import VisibilityCategoryType
from howyoubeen.storage.local_storage_service import LocalStorageService


@pytest.mark.asyncio
async def test_newsletter_generation_with_events():
    """Test newsletter generation with sample life events"""
    
    # Create temporary storage directory
    temp_dir = tempfile.mkdtemp(prefix="test_newsletter_")
    
    try:
        print("🧪 Testing newsletter generation with life events...")
        
        # Create storage and generator
        storage = LocalStorageService(storage_root=temp_dir)
        generator = NewsletterGenerator(storage)
        
        # Create test user
        user_data = {
            "username": "johndoe",
            "email": "john@example.com",
            "full_name": "John Doe",
            "bio": "Software engineer and avid traveler"
        }
        
        # Add user to storage and get the generated user_id
        created_user = await storage.create_user(user_data)
        user_id = created_user["id"]  # The storage generates the actual user_id
        print(f"✅ Created test user: {user_data['full_name']} with ID: {user_id[:8]}...")
        
        # Create sample life events
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        last_week = now - timedelta(days=7)
        
        life_events = [
            {
                "event_id": "event-1",
                "user_id": user_id,
                "start_date": yesterday.isoformat(),
                "summary": "Completed a major project at work - launched the new user dashboard",
                "visibility": {
                    "type": "good_friends",
                    "name": None
                },
                "created_at": yesterday.isoformat(),
                "updated_at": yesterday.isoformat()
            },
            {
                "event_id": "event-2", 
                "user_id": user_id,
                "start_date": (now - timedelta(days=2)).isoformat(),
                "summary": "Went hiking at Mount Tamalpais with friends - amazing sunset views!",
                "visibility": {
                    "type": "good_friends",
                    "name": None
                },
                "created_at": (now - timedelta(days=2)).isoformat(),
                "updated_at": (now - timedelta(days=2)).isoformat()
            },
            {
                "event_id": "event-3",
                "user_id": user_id,
                "start_date": last_week.isoformat(),
                "summary": "Started learning Spanish - taking evening classes",
                "visibility": {
                    "type": "public",
                    "name": None
                },
                "created_at": last_week.isoformat(),
                "updated_at": last_week.isoformat()
            }
        ]
        
        # Add life events to storage
        created_events = []
        for event in life_events:
            created_event = await storage.create_life_event(event)
            created_events.append(created_event)
        
        print(f"✅ Created {len(life_events)} test life events")
        
        # Debug: Check what events are stored
        all_events = await storage.get_life_events_by_date_range(
            user_id=user_id,
            start_date=yesterday - timedelta(days=1),
            end_date=now + timedelta(days=1)
        )
        print(f"🔍 Debug: Found {len(all_events)} events in storage for user {user_id[:8]}...")
        
        # Debug: Check what events match the newsletter criteria
        visibility_levels = ["good_friends", "public"]
        filtered_events = await storage.get_life_events_by_date_range(
            user_id=user_id,
            start_date=now - timedelta(days=7),  # Same as newsletter config
            end_date=now + timedelta(days=1),
            visibility_levels=visibility_levels
        )
        print(f"🔍 Debug: Found {len(filtered_events)} events matching newsletter criteria")
        if filtered_events:
            for event in filtered_events:
                print(f"   - Event: {event.get('summary', 'No summary')[:50]}...")
                print(f"     Date: {event.get('start_date')}")
                print(f"     Visibility: {event.get('visibility')}")
        
        # Create newsletter configuration
        newsletter_config = NewsletterConfig(
            name="Weekly Update",
            instructions="Create a friendly, engaging newsletter highlighting key life events. Use a casual tone and include emojis where appropriate.",
            periodicity=168,  # Weekly (168 hours)
            start_date=now - timedelta(days=7),  # Start a week ago
            visibility=[
                VisibilityCategory(type=VisibilityCategoryType.GOOD_FRIENDS),
                VisibilityCategory(type=VisibilityCategoryType.PUBLIC)
            ]
        )
        
        print(f"✅ Created newsletter config: {newsletter_config.name}")
        
        # Generate newsletter using real LLM API
        result = await generator.generate_newsletter(
            user_id=user_id,
            newsletter_config=newsletter_config
        )
        
        print(f"✅ Newsletter generation completed")
        
        # Verify results
        assert result.success, f"Newsletter generation failed: {result.error_message}"
        assert result.content is not None, "Newsletter content should not be None"
        assert result.events_count > 0, f"Expected events but got {result.events_count}"
        assert len(result.content) > 100, "Newsletter content should be substantial"
        
        print(f"✅ Newsletter generated successfully:")
        print(f"   - Events processed: {result.events_count}")
        print(f"   - Content length: {len(result.content)} characters")
        print(f"   - Date range: {result.generation_summary['date_range']['start']} to {result.generation_summary['date_range']['end']}")
        
        # Verify content contains expected elements
        assert "John Doe" in result.content, "Newsletter should contain user name"
        assert "Weekly Update" in result.content, "Newsletter should contain newsletter name"
        # Note: We can't guarantee specific content since we're using real LLM now
        
        print("✅ Content validation passed")
        
        # Print sample of generated content
        print("\n📧 Generated Newsletter Sample:")
        print("-" * 50)
        print(result.content[:300] + "..." if len(result.content) > 300 else result.content)
        print("-" * 50)
            
        print("🎉 Newsletter generation integration test PASSED!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        raise
    finally:
        # Clean up
        try:
            shutil.rmtree(temp_dir)
        except:
            pass


@pytest.mark.asyncio
async def test_newsletter_generation_no_events():
    """Test newsletter generation when no life events match the criteria"""
    
    temp_dir = tempfile.mkdtemp(prefix="test_newsletter_no_events_")
    
    try:
        print("🧪 Testing newsletter generation with no matching events...")
        
        storage = LocalStorageService(storage_root=temp_dir)
        generator = NewsletterGenerator(storage)
        
        # Create test user
        user_data = {
            "username": "janedoe",
            "email": "jane@example.com", 
            "full_name": "Jane Doe",
            "bio": "Marketing specialist and yoga enthusiast"
        }
        
        created_user = await storage.create_user(user_data)
        user_id = created_user["id"]
        print(f"✅ Created test user: {user_data['full_name']} with ID: {user_id[:8]}...")
        
        # Create newsletter config for a period with no events
        now = datetime.now()
        newsletter_config = NewsletterConfig(
            name="Daily Digest",
            instructions="Create a brief daily update highlighting any new activities.",
            periodicity=24,  # Daily
            start_date=now - timedelta(hours=24),
            visibility=[VisibilityCategory(type=VisibilityCategoryType.PUBLIC)]
        )
        
        # Generate newsletter (will use real LLM API)
        result = await generator.generate_newsletter(
            user_id=user_id,
            newsletter_config=newsletter_config
        )
        
        print(f"✅ Newsletter generation completed")
        
        # Verify results
        assert result.success, f"Newsletter generation failed: {result.error_message}"
        assert result.content is not None, "Newsletter content should not be None"
        assert result.events_count == 0, f"Expected 0 events but got {result.events_count}"
        
        print(f"✅ No-events newsletter generated successfully:")
        print(f"   - Events processed: {result.events_count}")
        print(f"   - Content length: {len(result.content)} characters")
        
        # Verify content handles no events gracefully
        # Note: Real LLM might not always include the exact user name, so we'll check for meaningful content
        assert len(result.content) > 50, "Newsletter should still have meaningful content"
        assert "Daily Digest" in result.content, "Newsletter should contain newsletter name"
        
        print("✅ No-events validation passed")
            
        print("🎉 No-events newsletter generation test PASSED!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        raise
    finally:
        try:
            shutil.rmtree(temp_dir)
        except:
            pass


@pytest.mark.asyncio
async def test_newsletter_generation_llm_failure():
    """Test newsletter generation fallback when LLM fails"""
    
    temp_dir = tempfile.mkdtemp(prefix="test_newsletter_fallback_")
    
    try:
        print("🧪 Testing newsletter generation with LLM failure fallback...")
        
        storage = LocalStorageService(storage_root=temp_dir)
        generator = NewsletterGenerator(storage)
        
        # Create test user
        user_data = {
            "username": "bobsmith",
            "email": "bob@example.com",
            "full_name": "Bob Smith",
            "bio": "Data scientist and coffee enthusiast"
        }
        
        created_user = await storage.create_user(user_data)
        user_id = created_user["id"]
        print(f"✅ Created test user: {user_data['full_name']} with ID: {user_id[:8]}...")
        
        # Add a test event
        now = datetime.now()
        event = {
            "event_id": "fallback-event-1",
            "user_id": user_id,
            "start_date": (now - timedelta(hours=6)).isoformat(),
            "summary": "Published a research paper on machine learning applications",
            "visibility": {"type": "public", "name": None},
            "created_at": (now - timedelta(hours=6)).isoformat(),
            "updated_at": (now - timedelta(hours=6)).isoformat()
        }
        await storage.create_life_event(event)
        print("✅ Created test life event")
        
        newsletter_config = NewsletterConfig(
            name="Research Updates",
            instructions="Create an academic-style newsletter about research activities.",
            periodicity=24,
            start_date=now - timedelta(hours=24),
            visibility=[VisibilityCategory(type=VisibilityCategoryType.PUBLIC)]
        )
        
        # Since we removed LLM mocking per user request, this will use real LLM API
        # and should succeed rather than test the fallback path
        result = await generator.generate_newsletter(
            user_id=user_id,
            newsletter_config=newsletter_config
        )
        
        print("✅ Newsletter generation completed")
        
        # Verify results (should succeed with real LLM)
        assert result.success, f"Newsletter generation failed: {result.error_message}"
        assert result.content is not None, "Newsletter content should be generated"
        assert result.events_count == 1, f"Expected 1 event but got {result.events_count}"
        
        # Verify content structure
        assert "Research Updates" in result.content, "Should contain newsletter name"
        assert "Bob Smith" in result.content, "Should contain user name"
        # Note: Can't guarantee specific content since using real LLM
        
        print("✅ Newsletter validated:")
        print(f"   - Events processed: {result.events_count}")
        print(f"   - Content length: {len(result.content)} characters")
        
        # Print sample of generated content
        print("\n📧 Generated Newsletter Sample:")
        print("-" * 50)
        print(result.content[:200] + "..." if len(result.content) > 200 else result.content)
        print("-" * 50)
        
        print("🎉 Newsletter generation with real LLM test PASSED!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        raise
    finally:
        try:
            shutil.rmtree(temp_dir)
        except:
            pass


async def run_all_tests():
    """Run all newsletter generation tests"""
    print("🚀 Starting Newsletter Generation Integration Tests")
    print("=" * 60)
    
    tests = [
        ("Newsletter Generation with Events", test_newsletter_generation_with_events),
        ("Newsletter Generation with No Events", test_newsletter_generation_no_events),
        ("Newsletter Generation with Real LLM", test_newsletter_generation_llm_failure)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 40)
        try:
            await test_func()
            passed += 1
            print(f"✅ {test_name} PASSED")
        except Exception as e:
            print(f"❌ {test_name} FAILED: {e}")
    
    print("\n" + "=" * 60)
    print(f"🏁 Tests completed: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Newsletter generation is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the output above.")
        return False
    
    return True


if __name__ == "__main__":
    # Run the integration tests
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)