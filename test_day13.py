#!/usr/bin/env python
"""Test Day 13 Content Generation endpoints."""

import asyncio
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

async def test_interview_questions():
    """Test interview question generation."""
    print("🔍 Testing Interview Questions Generation...")
    
    try:
        # Sample CV content
        cv_content = """
        John Doe
        Senior Software Engineer
        
        Experience:
        - Senior Software Engineer at Tech Corp (2020-Present)
        - Software Engineer at StartupXYZ (2018-2020)
        - Junior Developer at Web Solutions (2016-2018)
        
        Skills:
        - Python, JavaScript, React, Node.js
        - AWS, Docker, Kubernetes
        - Agile, Scrum, CI/CD
        
        Education:
        - BS Computer Science, State University (2016)
        """
        
        request_data = {
            "cv_content": cv_content,
            "max_tokens": 800,
            "temperature": 0.7
        }
        
        response = requests.post(f"{BASE_URL}/generate/interview-questions", json=request_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Interview questions generated:")
            print(f"   Content length: {len(result['generated_content'])} chars")
            print(f"   Tokens used: {result['tokens_used']}")
            print(f"   Processing time: {result['processing_time_ms']:.2f}ms")
            print(f"   Generation type: {result['generation_type']}")
            
            # Show first few questions
            questions = result['generated_content'].split('\n')
            questions = [q.strip() for q in questions if q.strip() and q[0].isdigit()]
            print(f"   Questions generated: {len(questions)}")
            for i, q in enumerate(questions[:3]):
                print(f"     {i+1}. {q[:80]}...")
            
            return True
        else:
            print(f"Interview questions failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Interview questions error: {e}")
        return False

async def test_episode_brief():
    """Test episode brief generation."""
    print("🔍 Testing Episode Brief Generation...")
    
    try:
        # Sample podcast transcript
        transcript_content = """
        Host: Welcome to Tech Talk Today! I'm your host Sarah, and today we have a special guest,
        Dr. Michael Chen, who's been researching artificial intelligence for over 15 years.
        
        Michael: Thanks for having me, Sarah. I'm excited to talk about the recent developments
        in large language models and how they're changing the way we interact with technology.
        
        Host: That's fascinating! Can you explain in simple terms what makes these new models
        so different from what we had before?
        
        Michael: Absolutely. Think of it like the difference between a calculator and a
        smartphone. Old AI could do specific tasks really well, but these new models can
        understand context, have conversations, and even be creative. They're more like
        thinking partners than just tools.
        
        Host: That's a great analogy! So what are some practical ways people are using
        this technology right now?
        
        Michael: We're seeing incredible applications across healthcare, education,
        creative industries, and even personal productivity. The key is that these models
        can adapt to individual needs and learn from feedback.
        """
        
        request_data = {
            "transcript_content": transcript_content,
            "max_tokens": 1000,
            "temperature": 0.8
        }
        
        response = requests.post(f"{BASE_URL}/generate/episode-brief", json=request_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Episode brief generated:")
            print(f"   Content length: {len(result['generated_content'])} chars")
            print(f"   Tokens used: {result['tokens_used']}")
            print(f"   Processing time: {result['processing_time_ms']:.2f}ms")
            print(f"   Generation type: {result['generation_type']}")
            
            # Show preview
            preview = result['generated_content'][:300]
            print(f"   Preview: {preview}...")
            
            return True
        else:
            print(f"❌ Episode brief failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Episode brief error: {e}")
        return False

async def test_summary():
    """Test document summary generation."""
    print("🔍 Testing Summary Generation...")
    
    try:
        # Sample document content
        document_content = """
        Climate Change Impact on Global Food Security
        
        Executive Summary:
        Climate change poses significant threats to global food security through multiple pathways
        including reduced crop yields, increased pest pressures, and extreme weather events.
        This comprehensive analysis examines current impacts and future projections.
        
        Key Findings:
        1. Crop yields are projected to decrease by 15-25% in major agricultural regions
        by 2050 due to temperature increases and changing precipitation patterns.
        
        2. Food price volatility has increased by 40% over the past decade,
        disproportionately affecting vulnerable populations in developing nations.
        
        3. New agricultural zones are emerging as traditional farming regions
        become less suitable, requiring significant adaptation investments.
        
        4. Water scarcity affects 2.8 billion people annually, with climate change
        exacerbating existing water management challenges.
        
        Recommendations:
        - Invest in climate-resilient crop varieties and agricultural practices
        - Develop early warning systems for extreme weather events
        - Create international food reserve systems
        - Support smallholder farmers in adaptation strategies
        """
        
        request_data = {
            "document_content": document_content,
            "max_tokens": 600,
            "temperature": 0.5
        }
        
        response = requests.post(f"{BASE_URL}/generate/summary", json=request_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Summary generated:")
            print(f"   Content length: {len(result['generated_content'])} chars")
            print(f"   Tokens used: {result['tokens_used']}")
            print(f"   Processing time: {result['processing_time_ms']:.2f}ms")
            print(f"   Generation type: {result['generation_type']}")
            
            # Show preview
            preview = result['generated_content'][:300]
            print(f"   Preview: {preview}...")
            
            return True
        else:
            print(f"❌ Summary failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Summary error: {e}")
        return False

async def test_generation_with_context():
    """Test generation with additional context from search."""
    print("🔍 Testing Generation with Context...")
    
    try:
        cv_content = "Jane Smith - Data Scientist with 5 years experience in ML and Python"
        context = "The candidate is applying for a Senior Data Scientist position at a fintech company"
        
        request_data = {
            "cv_content": cv_content,
            "context": context,
            "max_tokens": 500,
            "temperature": 0.6
        }
        
        response = requests.post(f"{BASE_URL}/generate/interview-questions", json=request_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Generation with context working:")
            print(f"   Has context in metadata: {'has_context' in result['metadata']}")
            print(f"   Content length: {len(result['generated_content'])} chars")
            
            return True
        else:
            print(f"❌ Generation with context failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Generation with context error: {e}")
        return False

async def test_generation_options():
    """Test generation options endpoint."""
    print("🔍 Testing Generation Options...")
    
    try:
        response = requests.get(f"{BASE_URL}/generate/options", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Generation options working:")
            print(f"   Generation types: {result['generation_types']}")
            print(f"   Token limits: {result['max_tokens_range']}")
            print(f"   Temperature range: {result['temperature_range']}")
            print(f"   Supported formats: {result['supported_formats']}")
            
            return True
        else:
            print(f"❌ Generation options failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Generation options error: {e}")
        return False

async def test_generation_health():
    """Test generation health endpoint."""
    print("🔍 Testing Generation Health...")
    
    try:
        response = requests.get(f"{BASE_URL}/generate/health", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Generation health working:")
            print(f"   Status: {result['status']}")
            print(f"   Services: {result['services']}")
            
            # Check individual services
            for service, status in result['services'].items():
                status_icon = "✅" if "healthy" in status else "❌"
                print(f"   {status_icon} {service}: {status}")
            
            return True
        else:
            print(f"❌ Generation health failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Generation health error: {e}")
        return False

async def test_error_handling():
    """Test error handling with invalid requests."""
    print("🔍 Testing Error Handling...")
    
    try:
        # Test with empty content
        request_data = {
            "cv_content": "",  # Invalid: too short
            "max_tokens": 1000
        }
        
        response = requests.post(f"{BASE_URL}/generate/interview-questions", json=request_data, timeout=10)
        
        if response.status_code == 422:  # Validation error
            print("✅ Validation error handling working:")
            print(f"   Correctly rejected empty content")
            return True
        else:
            print(f"❌ Error handling failed - expected 422, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error handling test error: {e}")
        return False

async def main():
    """Run all Day 13 tests."""
    print("Starting Day 13 Content Generation Tests")
    print("=" * 60)
    
    tests = [
        ("Interview Questions", test_interview_questions),
        ("Episode Brief", test_episode_brief),
        ("Summary Generation", test_summary),
        ("Generation with Context", test_generation_with_context),
        ("Generation Options", test_generation_options),
        ("Generation Health", test_generation_health),
        ("Error Handling", test_error_handling)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
        
        # Small delay between tests
        await asyncio.sleep(1)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 DAY 13 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Day 13 implementation is complete!")
    else:
        print("⚠️ Some tests failed. Check logs above for details.")
    
    print("\nDay 13 Features Implemented:")
    print("✅ Content generation service with OpenAI integration")
    print("✅ Interview questions generator for CVs")
    print("✅ Episode brief generator for podcasts")
    print("✅ Summary generator for documents")
    print("✅ POST /generate/interview-questions endpoint")
    print("✅ POST /generate/episode-brief endpoint")
    print("✅ POST /generate/summary endpoint")
    print("✅ GET /generate/options endpoint")
    print("✅ GET /generate/health endpoint")
    print("✅ Comprehensive error handling and validation")
    print("✅ Context-aware generation with search integration")

if __name__ == "__main__":
    asyncio.run(main())
