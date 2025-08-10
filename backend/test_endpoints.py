#!/usr/bin/env python3
"""Simple endpoint testing script"""

import httpx
import asyncio
import json
from pathlib import Path
import sys

# Add the src directory to Python path
sys.path.append(str(Path(__file__).parent / "src"))

BASE_URL = "http://localhost:8002"

async def test_health_endpoint():
    """Test the health endpoint"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health")
            print(f"✓ Health endpoint: {response.status_code}")
            print(f"  Response: {response.json()}")
            return True
        except Exception as e:
            print(f"✗ Health endpoint failed: {e}")
            return False

async def test_onboarding_start():
    """Test onboarding start endpoint"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{BASE_URL}/api/onboarding/start")
            print(f"✓ Onboarding start: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  Session ID: {data.get('session_id')}")
                return data.get('session_id')
            else:
                print(f"  Error: {response.text}")
                return None
        except Exception as e:
            print(f"✗ Onboarding start failed: {e}")
            return None

async def test_user_endpoint():
    """Test user profile endpoint (should fail since no user exists)"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/api/users/johndoe")
            print(f"✓ User endpoint: {response.status_code}")
            if response.status_code == 404:
                print("  Expected 404 - no user exists yet")
            elif response.status_code == 200:
                print(f"  User data: {response.json()}")
            else:
                print(f"  Unexpected response: {response.text}")
            return True
        except Exception as e:
            print(f"✗ User endpoint failed: {e}")
            return False

async def test_chat_endpoint():
    """Test chat endpoint (should fail since no user exists)"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/chat/johndoe",
                json={"message": "Hello!"}
            )
            print(f"✓ Chat endpoint: {response.status_code}")
            if response.status_code == 404:
                print("  Expected 404 - no user exists yet")
            elif response.status_code == 200:
                print(f"  Chat response: {response.json()}")
            else:
                print(f"  Response: {response.text}")
            return True
        except Exception as e:
            print(f"✗ Chat endpoint failed: {e}")
            return False

async def test_friends_endpoint():
    """Test friends endpoint (should fail since no user exists)"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/api/users/test123/friends")
            print(f"✓ Friends endpoint: {response.status_code}")
            if response.status_code == 404:
                print("  Expected 404 - no user exists yet")
            else:
                print(f"  Response: {response.text}")
            return True
        except Exception as e:
            print(f"✗ Friends endpoint failed: {e}")
            return False

async def test_timeline_endpoint():
    """Test timeline endpoint (should fail since no user exists)"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/api/users/johndoe/timeline")
            print(f"✓ Timeline endpoint: {response.status_code}")
            if response.status_code == 404:
                print("  Expected 404 - no user exists yet")
            else:
                print(f"  Response: {response.text}")
            return True
        except Exception as e:
            print(f"✗ Timeline endpoint failed: {e}")
            return False

async def main():
    """Run all endpoint tests"""
    print("🔍 Testing API endpoints...")
    print(f"Base URL: {BASE_URL}")
    print("=" * 50)
    
    tests = [
        test_health_endpoint(),
        test_onboarding_start(),
        test_user_endpoint(),
        test_chat_endpoint(),
        test_friends_endpoint(),
        test_timeline_endpoint(),
    ]
    
    results = await asyncio.gather(*tests, return_exceptions=True)
    
    print("=" * 50)
    passed = sum(1 for r in results if r is True or isinstance(r, str))
    total = len(results)
    print(f"Tests completed: {passed}/{total} endpoints responded as expected")

if __name__ == "__main__":
    asyncio.run(main())
