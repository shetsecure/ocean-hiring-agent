#!/bin/bash

# Team Compatibility Dashboard - Startup Script
# This script installs dependencies and starts the dashboard

echo "🚀 Team Compatibility Dashboard Setup"
echo "======================================"

# Check if pip is available
if ! command -v pip &> /dev/null; then
    echo "❌ pip not found. Please install Python and pip first."
    exit 1
fi

# Install Flask if not installed
echo "📦 Checking dependencies..."
if ! python -c "import flask" 2>/dev/null; then
    echo "🔧 Installing Flask..."
    pip install flask
    echo "✅ Flask installed successfully!"
else
    echo "✅ Flask already installed"
fi

# Check if data file exists
if [ ! -f "../data_for_dashboard.json" ]; then
    echo "⚠️  Warning: data_for_dashboard.json not found in parent directory"
    echo "   Please ensure the data file is generated before starting the dashboard"
fi

echo ""
echo "🎯 Starting Team Compatibility Dashboard..."
echo "📊 Dashboard will be available at: http://localhost:5000"
echo "🔗 API endpoints: http://localhost:5000/api/"
echo "💡 Press Ctrl+C to stop the server"
echo "--------------------------------------"

# Start the Flask application
python app.py 