#!/usr/bin/env python3
"""
Test script for AI Assistant functionality

This script tests:
- Weaviate connection
- Candidate synchronization
- Natural language querying
- Stats retrieval
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_api_health():
    """Test if API is running."""
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ API Health: OK")
            return True
        else:
            print(f"❌ API Health: Failed ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ API Health: Error - {e}")
        return False

def test_api_status():
    """Test API status and AI assistant availability."""
    try:
        response = requests.get(f"{BASE_URL}/status")
        if response.status_code == 200:
            data = response.json()
            print("✅ API Status: OK")
            print(f"   - AI Assistant Available: {data.get('ai_assistant_available', False)}")
            return data.get('ai_assistant_available', False)
        else:
            print(f"❌ API Status: Failed ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ API Status: Error - {e}")
        return False

def test_sync_candidates():
    """Test candidate synchronization."""
    try:
        print("🔄 Testing candidate sync...")
        response = requests.post(f"{BASE_URL}/candidates/sync", json={})
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Sync: {data['message']}")
            return True
        else:
            print(f"❌ Sync: Failed ({response.status_code}) - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Sync: Error - {e}")
        return False

def test_candidate_stats():
    """Test candidate statistics retrieval."""
    try:
        print("📊 Testing candidate stats...")
        response = requests.get(f"{BASE_URL}/candidates/stats")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Stats: {data['total_candidates']} candidates in database")
            print(f"   Collection: {data['collection_name']}")
            return True
        else:
            print(f"❌ Stats: Failed ({response.status_code}) - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Stats: Error - {e}")
        return False

def test_candidate_queries():
    """Test natural language queries."""
    test_queries = [
        "Who's the most outgoing?",
        "Who would be perfect for sales?",
        "Who can handle high pressure?",
        "Who is the most organized and reliable?",
        "Who is most creative and innovative?"
    ]
    
    results = []
    for query in test_queries:
        try:
            print(f"🔍 Testing query: '{query}'")
            
            payload = {
                "query": query,
                "limit": 3
            }
            
            response = requests.post(f"{BASE_URL}/candidates/query", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Found {data['results_count']} results")
                
                if data['results_count'] > 0:
                    top_candidate = data['candidates'][0]
                    print(f"   🏆 Top match: {top_candidate['name']} (Score: {top_candidate.get('compatibility_score', 'N/A')})")
                    print(f"   📝 Summary: {top_candidate['summary'][:100]}...")
                
                results.append({"query": query, "success": True, "results": data['results_count']})
            else:
                print(f"   ❌ Query failed ({response.status_code}) - {response.text}")
                results.append({"query": query, "success": False, "error": response.text})
                
        except Exception as e:
            print(f"   ❌ Query error: {e}")
            results.append({"query": query, "success": False, "error": str(e)})
        
        time.sleep(1)  # Rate limiting
    
    return results

def main():
    """Run all tests."""
    print("🚀 Starting AI Assistant Tests...\n")
    
    # Test 1: API Health
    if not test_api_health():
        print("❌ API is not running. Please start the API first.")
        return
    
    print()
    
    # Test 2: API Status and AI Assistant availability
    ai_available = test_api_status()
    if not ai_available:
        print("❌ AI Assistant is not available. Check Weaviate configuration.")
        return
    
    print()
    
    # Test 3: Sync candidates
    if not test_sync_candidates():
        print("❌ Candidate sync failed. Cannot proceed with queries.")
        return
    
    print()
    
    # Test 4: Get stats
    test_candidate_stats()
    
    print()
    
    # Test 5: Natural language queries
    print("🤖 Testing Natural Language Queries...\n")
    query_results = test_candidate_queries()
    
    print(f"\n📊 Query Test Summary:")
    successful_queries = sum(1 for r in query_results if r["success"])
    total_queries = len(query_results)
    print(f"   ✅ Successful: {successful_queries}/{total_queries}")
    
    if successful_queries == total_queries:
        print("\n🎉 All tests passed! AI Assistant is working correctly.")
    else:
        print(f"\n⚠️ {total_queries - successful_queries} tests failed. Check logs for details.")

if __name__ == "__main__":
    main() 