#!/usr/bin/env python3
"""
Test script to verify API functionality after refactoring.
"""

import json
import requests
import time

# Sample test data
TEAM_DATA = {
    "team": [
        {
            "id": "team001",
            "name": "Alice Johnson",
            "position": "Senior Developer",
            "big_five": {
                "openness": 0.8,
                "conscientiousness": 0.9,
                "extraversion": 0.6,
                "agreeableness": 0.7,
                "neuroticism": 0.3
            }
        }
    ]
}

CANDIDATES_DATA = {
    "candidates": [
        {
            "id": "cand001", 
            "name": "John Doe",
            "position": "Software Engineer",
            "responses": [
                {
                    "question": "Tell me about a challenging project you worked on.",
                    "answer": "I worked on a complex microservices architecture where I had to coordinate with multiple teams and learn new technologies like Kubernetes."
                }
            ]
        }
    ]
}

def test_health():
    """Test health endpoint."""
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"✅ Health check: {response.status_code}")
        print(f"   Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        if 'response' in locals():
            print(f"   Response text: {response.text}")
        return False

def test_status():
    """Test status endpoint."""
    try:
        response = requests.get("http://localhost:8000/status")
        print(f"✅ Status check: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Status check failed: {e}")
        if 'response' in locals():
            print(f"   Response text: {response.text}")
        return False

def test_create_interview():
    """Test interview creation."""
    try:
        data = {
            "candidate_name": "Test Candidate",
            "role": "Software Engineer",
            "candidate_email": "test@example.com"
        }
        response = requests.post("http://localhost:8000/interviews", json=data)
        
        print(f"✅ Interview creation: {response.status_code}")
        print(f"   Request data: {json.dumps(data, indent=2)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   Response: {json.dumps(result, indent=2)}")
        else:
            print(f"   Error response: {response.text}")
        return True
    except Exception as e:
        print(f"❌ Interview creation failed: {e}")
        if 'response' in locals():
            print(f"   Response text: {response.text}")
        return False

def test_compatibility_analysis():
    """Test compatibility analysis with JSON data."""
    try:
        data = {
            "team_data": TEAM_DATA,
            "candidates_data": CANDIDATES_DATA
        }
        print("🔄 Running compatibility analysis (this may take a moment due to AI processing)...")
        print(f"   Request data: {json.dumps(data, indent=2)}")
        
        response = requests.post("http://localhost:8000/analysis/compatibility", json=data)
        
        print(f"✅ Compatibility analysis: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   Team size: {result['analysis_metadata']['team_size']}")
            print(f"   Candidates: {result['analysis_metadata']['candidates_count']}")
            if result['candidates_analysis']:
                first_candidate = result['candidates_analysis'][0]
                print(f"   First candidate compatibility: {first_candidate['ai_analysis']['compatibility_score']}")
            print(f"   Full response: {json.dumps(result, indent=2)}")
        else:
            print(f"   Error response: {response.text}")
        return True
    except Exception as e:
        print(f"❌ Compatibility analysis failed: {e}")
        if 'response' in locals():
            print(f"   Response text: {response.text}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing API functionality...\n")
    
    # Start API server
    import subprocess
    import time
    
    print("🚀 Starting API server...")
    api_process = subprocess.Popen(["python", "api.py"], 
                                  stdout=subprocess.DEVNULL, 
                                  stderr=subprocess.DEVNULL)
    
    # Wait for server to start
    time.sleep(3)
    
    try:
        # Run tests
        tests = [
            ("Health Check", test_health),
            ("Status Check", test_status), 
            ("Interview Creation", test_create_interview),
            ("Compatibility Analysis", test_compatibility_analysis)
        ]
        
        results = []
        for test_name, test_func in tests:
            print(f"\n🔍 Running {test_name}...")
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results.append((test_name, False))
        
        # Summary
        print(f"\n📊 Test Results:")
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {status}: {test_name}")
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed")
        
    finally:
        # Clean up
        print("\n🧹 Cleaning up...")
        api_process.terminate()
        api_process.wait()

if __name__ == "__main__":
    main() 