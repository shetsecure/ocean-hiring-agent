#!/usr/bin/env python3
"""
Team Compatibility Dashboard - Startup Script
Run this file to start the dashboard server.
"""

import os
import sys
from app import app

if __name__ == '__main__':
    print("🚀 Starting Team Compatibility Dashboard...")
    print(f"📊 Dashboard URL: http://localhost:5005")
    print(f"🔗 API endpoints available at: http://localhost:5005/api/")
    print("💡 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5005)
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped. Thank you!")
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        sys.exit(1) 