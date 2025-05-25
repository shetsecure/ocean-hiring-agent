#!/usr/bin/env python3
"""
Simple Mistral API Test Script

Tests the Mistral API connection and basic functionality to diagnose issues.
"""

import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from mistralai import Mistral
from pathlib import Path

def test_mistral_connection():
    """Test basic Mistral API connection and functionality."""
    
    print("🔑 Testing Mistral API Connection...")
    print("=" * 50)
    
    # Load environment variables - look in parent directory first
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(env_path)
    # Fallback to default search
    load_dotenv()
    
    # Get API key
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print("❌ ERROR: MISTRAL_API_KEY not found in environment variables")
        return False
    
    print(f"✅ API Key found: {api_key[:8]}...{api_key[-4:]}")
    
    try:
        # Initialize client
        client = Mistral(api_key=api_key)
        print("✅ Mistral client initialized successfully")
        
        # Test simple prompt
        print("\n🤖 Testing simple prompt...")
        
        messages = [{"role": "user", "content": "Say 'Hello, API is working!' in exactly 5 words."}]
        
        start_time = time.time()
        response = client.chat.complete(
            model="mistral-small-latest",
            messages=messages,
            temperature=0.1,
            max_tokens=50
        )
        end_time = time.time()
        
        response_time = end_time - start_time
        content = response.choices[0].message.content
        
        print(f"✅ Response received in {response_time:.2f}s")
        print(f"📝 Response: {content}")
        
        # Test rate limiting behavior
        print("\n🚦 Testing rate limiting...")
        
        for i in range(3):
            print(f"Request {i+1}/3...")
            start_time = time.time()
            
            try:
                test_response = client.chat.complete(
                    model="mistral-small-latest",
                    messages=[{"role": "user", "content": f"Count to {i+1}"}],
                    temperature=0.1,
                    max_tokens=20
                )
                
                elapsed = time.time() - start_time
                print(f"✅ Request {i+1} succeeded in {elapsed:.2f}s")
                print(f"   Response: {test_response.choices[0].message.content}")
                
            except Exception as e:
                elapsed = time.time() - start_time
                print(f"❌ Request {i+1} failed after {elapsed:.2f}s: {e}")
                
                # Check if it's a rate limit error
                if "rate limit" in str(e).lower() or "429" in str(e):
                    print("🚨 Rate limit detected!")
                    return False
            
            # Small delay between requests
            time.sleep(0.5)
        
        print("\n✅ All tests passed! Mistral API is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_rag_prompt():
    """Test a RAG-style prompt similar to what the AI assistant uses."""
    
    print("\n🧠 Testing RAG-style Analysis Prompt...")
    print("=" * 50)
    
    # Load environment variables - look in parent directory first
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(env_path)
    # Fallback to default search
    load_dotenv()
    
    api_key = os.getenv("MISTRAL_API_KEY")
    
    if not api_key:
        print("❌ API key not available")
        return False
    
    try:
        client = Mistral(api_key=api_key)
        
        # Sample candidate data (similar to what RAG uses)
        prompt = """You are an expert HR analyst. Rank these candidates for "Who is the most outgoing?"

Candidates:
1. Mohammed - Extraversion: 0.85, Openness: 0.95, Agreeableness: 0.90
2. Alice Smith - Extraversion: 0.50, Openness: 0.65, Agreeableness: 0.75  
3. David Lee - Extraversion: 0.10, Openness: 0.20, Agreeableness: 0.20

Rank by extraversion scores and explain why.

RESPONSE FORMAT (JSON):
{
  "analysis": "Brief explanation",
  "ranked_candidates": [
    {"name": "Name", "rank": 1, "reasoning": "Why they rank here"}
  ]
}"""

        messages = [{"role": "user", "content": prompt}]
        
        print("🚀 Sending RAG analysis prompt...")
        start_time = time.time()
        
        response = client.chat.complete(
            model="mistral-small-latest",
            messages=messages,
            temperature=0.1,
            max_tokens=500
        )
        
        elapsed = time.time() - start_time
        content = response.choices[0].message.content
        
        print(f"✅ RAG prompt completed in {elapsed:.2f}s")
        print("\n📊 RAG Response:")
        print("-" * 30)
        print(content)
        
        # Try to parse as JSON
        try:
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                print("\n✅ JSON parsing successful!")
                print(f"Analysis: {parsed.get('analysis', 'N/A')}")
                for candidate in parsed.get('ranked_candidates', []):
                    print(f"  {candidate.get('rank', '?')}. {candidate.get('name', 'Unknown')} - {candidate.get('reasoning', 'No reasoning')}")
            else:
                print("⚠️ No JSON found in response")
        except Exception as parse_error:
            print(f"⚠️ JSON parsing failed: {parse_error}")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG test failed: {e}")
        return False

if __name__ == "__main__":
    print(f"🧪 Mistral API Test Suite")
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Test basic connection
    basic_success = test_mistral_connection()
    
    if basic_success:
        # Test RAG-style prompt
        rag_success = test_rag_prompt()
        
        if rag_success:
            print("\n🎉 ALL TESTS PASSED! Mistral API is ready for RAG.")
        else:
            print("\n⚠️ Basic connection works but RAG testing failed.")
    else:
        print("\n❌ Basic connection failed. Check API key and rate limits.")
    
    print(f"\n⏰ Test completed: {datetime.now().isoformat()}") 