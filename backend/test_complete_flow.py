#!/usr/bin/env python3
"""Test complete user onboarding and API flow"""

import httpx
import asyncio
import json
from pathlib import Path
import sys

# Add the src directory to Python path
sys.path.append(str(Path(__file__).parent / "src"))

BASE_URL = "http://localhost:8002"

async def test_complete_flow():
    """Test complete user creation and API interaction flow"""
    async with httpx.AsyncClient() as client:
        print("🚀 Testing complete user flow...")
        print("=" * 50)
        
        # Step 1: Start onboarding
        print("1. Starting onboarding...")
        response = await client.post(f"{BASE_URL}/api/onboarding/start")
        if response.status_code != 200:
            print(f"❌ Failed to start onboarding: {response.status_code}")
            return
        
        session_data = response.json()
        session_id = session_data.get('session_id')
        print(f"✅ Session started: {session_id}")
        
        # Step 2: Submit basic info
        print("2. Submitting basic info...")
        basic_info = {
            "session_id": session_id,
            "full_name": "John Test Doe",
            "username": "johndoe", 
            "email": "john@example.com",
            "bio": "Software engineer who loves coding and outdoor activities."
        }
        
        response = await client.post(f"{BASE_URL}/api/onboarding/basic-info", json=basic_info)
        if response.status_code != 200:
            print(f"❌ Failed to submit basic info: {response.status_code} - {response.text}")
            return
        
        print("✅ Basic info submitted")
        
        # Step 3: Complete onboarding
        print("3. Completing onboarding...")
        complete_data = {
            "session_id": session_id,
            "username": "johndoe",
            "email": "john@example.com", 
            "bio": "Software engineer who loves coding and outdoor activities.",
            "data_sources": [],
            "visibility_preference": "good_friends"
        }
        
        response = await client.post(f"{BASE_URL}/api/onboarding/complete", json=complete_data)
        if response.status_code != 200:
            print(f"❌ Failed to complete onboarding: {response.status_code} - {response.text}")
            return
        
        completion_data = response.json()
        user_id = completion_data.get('user_id')
        print(f"✅ Onboarding completed. User ID: {user_id}")
        
        # Step 4: Test user profile endpoint
        print("4. Testing user profile...")
        response = await client.get(f"{BASE_URL}/api/users/johndoe")
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ User profile retrieved: {user_data.get('full_name')}")
        else:
            print(f"❌ Failed to get user profile: {response.status_code} - {response.text}")
        
        # Step 5: Test chat endpoint
        print("5. Testing chat...")
        chat_data = {"message": "Hello! How have you been?"}
        response = await client.post(f"{BASE_URL}/api/chat/johndoe", json=chat_data)
        if response.status_code == 200:
            chat_response = response.json()
            print(f"✅ Chat response: {chat_response.get('response')[:100]}...")
        else:
            print(f"❌ Failed to chat: {response.status_code} - {response.text}")
        
        # Step 6: Test friends endpoint
        print("6. Testing friends endpoint...")
        response = await client.get(f"{BASE_URL}/api/users/{user_id}/friends")
        if response.status_code == 200:
            friends_data = response.json()
            print(f"✅ Friends list retrieved: {len(friends_data)} friends")
        else:
            print(f"❌ Failed to get friends: {response.status_code} - {response.text}")
        
        # Step 7: Test timeline endpoint 
        print("7. Testing timeline...")
        response = await client.get(f"{BASE_URL}/api/users/johndoe/timeline")
        if response.status_code == 200:
            timeline_data = response.json()
            print(f"✅ Timeline retrieved: {len(timeline_data)} items")
        else:
            print(f"❌ Failed to get timeline: {response.status_code} - {response.text}")
        
        # Step 8: Test content upload
        print("8. Testing content upload...")
        content_data = {"content": "Just finished a great hiking trip in the mountains!"}
        response = await client.post(f"{BASE_URL}/api/users/{user_id}/content", json=content_data)
        if response.status_code == 200:
            upload_response = response.json()
            print(f"✅ Content uploaded: {upload_response.get('message')}")
        else:
            print(f"❌ Failed to upload content: {response.status_code} - {response.text}")
        
        print("=" * 50)
        print("🎉 Complete flow test finished!")

if __name__ == "__main__":
    asyncio.run(test_complete_flow())
