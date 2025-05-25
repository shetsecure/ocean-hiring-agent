#!/usr/bin/env python3
"""
Mini-script to test Weaviate connection only

This script checks:
- Environment variables
- Weaviate connection
- Basic operations
"""

import os
import weaviate
from dotenv import load_dotenv
from pathlib import Path

def test_weaviate_connection():
    """Test basic Weaviate connection."""
    print("🔧 Testing Weaviate Connection...\n")
    
    # Load environment variables - look in parent directory first
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(env_path)
    # Fallback to default search
    load_dotenv()
    
    # Check environment variables
    weaviate_url = os.getenv("WEAVIATE_URL")
    weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    print("📋 Environment Variables:")
    print(f"   WEAVIATE_URL: {weaviate_url}")
    print(f"   WEAVIATE_API_KEY: {'✅ Set' if weaviate_api_key else '❌ Missing'}")
    print(f"   OPENAI_API_KEY: {'✅ Set' if openai_api_key else '❌ Missing'}")
    print()
    
    if not weaviate_url or not weaviate_api_key:
        print("❌ Missing required Weaviate credentials!")
        return False
    
    # Fix URL format if needed
    if not weaviate_url.startswith(('http://', 'https://')):
        weaviate_url = f"https://{weaviate_url}"
        print(f"🔧 Fixed URL format: {weaviate_url}")
    
    try:
        print("🔌 Attempting to connect to Weaviate...")
        
        # Connect to Weaviate Cloud
        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=weaviate_url,
            auth_credentials=weaviate.auth.AuthApiKey(weaviate_api_key),
            headers={
                "X-OpenAI-Api-Key": openai_api_key or ""
            }
        )
        
        # Test connection
        if client.is_ready():
            print("✅ Successfully connected to Weaviate!")
            
            # Test basic operations
            print("\n🧪 Testing basic operations...")
            
            # Get cluster info
            try:
                meta = client.get_meta()
                print(f"   ✅ Cluster version: {meta.get('version', 'Unknown')}")
            except Exception as e:
                print(f"   ⚠️ Meta info error: {e}")
            
            # List collections
            try:
                collections = client.collections.list_all()
                print(f"   ✅ Found {len(collections)} collections")
                for col in collections:
                    print(f"      - {col}")
            except Exception as e:
                print(f"   ⚠️ Collections list error: {e}")
            
            # Close connection
            client.close()
            print("\n🎉 Weaviate connection test successful!")
            return True
            
        else:
            print("❌ Weaviate client is not ready")
            return False
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n🔍 Troubleshooting tips:")
        print("   1. Check if your Weaviate cluster is running")
        print("   2. Verify your API key is correct")
        print("   3. Check if your cluster URL is accessible")
        print("   4. Ensure your OpenAI API key is valid (for embeddings)")
        return False

if __name__ == "__main__":
    success = test_weaviate_connection()
    if success:
        print("\n✅ Ready to run AI Assistant tests!")
    else:
        print("\n❌ Fix connection issues before proceeding") 