#!/usr/bin/env python3
"""
Health check script for the Flask application
"""

import requests
import sys
import os

def health_check():
    """Check if the Flask application is responding"""
    try:
        # Try to connect to the Flask app
        response = requests.get('http://localhost:5005/health', timeout=5)
        
        if response.status_code == 200:
            print("✅ Health check passed - Flask app is responding")
            return True
        else:
            print(f"❌ Health check failed - HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Health check failed - Cannot connect to Flask app")
        return False
    except requests.exceptions.Timeout:
        print("❌ Health check failed - Request timeout")
        return False
    except Exception as e:
        print(f"❌ Health check failed - {e}")
        return False

if __name__ == "__main__":
    if health_check():
        sys.exit(0)
    else:
        sys.exit(1) 