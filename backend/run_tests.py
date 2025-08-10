#!/usr/bin/env python3
"""
Test runner for KeepInTouch backend

This script can run tests directly without pytest dependency
"""

import asyncio
import sys
import os

from tests.integration.test_onboarding_simple import run_simple_tests


async def main():
    """Run all tests"""
    print("🚀 Starting KeepInTouch Backend Tests")
    print("=" * 50)
    
    try:
        # Run integration tests
        print("\n📋 Integration Tests")
        print("-" * 20)
        success = await run_simple_tests()
        
        if success:
            print("\n✅ All tests passed successfully!")
            return 0
        else:
            print("\n❌ Some tests failed!")
            return 1
            
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())