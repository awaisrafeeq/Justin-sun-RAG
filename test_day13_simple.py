#!/usr/bin/env python
"""Simple test for Day 13 Content Generation endpoints."""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_generation_health():
    """Test generation health endpoint."""
    print("Testing Generation Health...")
    
    try:
        response = requests.get(f"{BASE_URL}/generate/health", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Generation health working:")
            print(f"   Status: {result['status']}")
            print(f"   Services: {result['services']}")
            return True
        else:
            print(f"Generation health failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"Generation health error: {e}")
        return False

def test_generation_options():
    """Test generation options endpoint."""
    print("Testing Generation Options...")
    
    try:
        response = requests.get(f"{BASE_URL}/generate/options", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Generation options working:")
            print(f"   Generation types: {result['generation_types']}")
            print(f"   Token limits: {result['max_tokens_range']}")
            return True
        else:
            print(f"Generation options failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"Generation options error: {e}")
        return False

def test_interview_questions():
    """Test interview question generation."""
    print("Testing Interview Questions...")
    
    try:
        cv_content = """
        John Doe
        Senior Software Engineer
        
        Experience:
        - Senior Software Engineer at Tech Corp (2020-Present)
        - Software Engineer at StartupXYZ (2018-2020)
        
        Skills:
        - Python, JavaScript, React, Node.js
        - AWS, Docker, Kubernetes
        """
        
        request_data = {
            "cv_content": cv_content,
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        response = requests.post(f"{BASE_URL}/generate/interview-questions", json=request_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Interview questions generated:")
            print(f"   Content length: {len(result['generated_content'])} chars")
            print(f"   Tokens used: {result['tokens_used']}")
            print(f"   Processing time: {result['processing_time_ms']:.2f}ms")
            return True
        else:
            print(f"Interview questions failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"Interview questions error: {e}")
        return False

def main():
    """Run simple Day 13 tests."""
    print("Starting Day 13 Content Generation Tests")
    print("=" * 60)
    
    tests = [
        ("Generation Health", test_generation_health),
        ("Generation Options", test_generation_options),
        ("Interview Questions", test_interview_questions)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\nTesting {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"{test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("DAY 13 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed! Day 13 implementation is working!")
    else:
        print("Some tests failed. Check logs above for details.")

if __name__ == "__main__":
    main()
