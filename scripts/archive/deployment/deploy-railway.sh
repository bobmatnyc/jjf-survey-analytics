#!/bin/bash

# Railway Deployment Script for JJF Survey Analytics
# This script helps configure and deploy the application to Railway

set -e

echo "🚂 Railway Deployment Configuration for JJF Survey Analytics"
echo "============================================================"

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

# Check if user is logged in
if ! railway whoami &> /dev/null; then
    echo "🔐 Please log in to Railway:"
    railway login
fi

echo "✅ Railway CLI ready"

# Check for required files
echo "📋 Checking required files..."

if [ ! -f "app.py" ]; then
    echo "❌ app.py not found in current directory"
    exit 1
fi

if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found"
    exit 1
fi

if [ ! -f "railway.toml" ]; then
    echo "❌ railway.toml not found - this should have been created"
    exit 1
fi

echo "✅ Required files present"

# Check for credentials
echo "🔑 Checking credentials..."

if [ ! -f "credentials.json" ]; then
    echo "⚠️  credentials.json not found"
    echo "   You'll need to set up Google Sheets API credentials"
    echo "   Either upload the file or set GOOGLE_CREDENTIALS_JSON environment variable"
fi

# Initialize Railway project if needed
if [ ! -f ".railway" ] && [ ! -d ".railway" ]; then
    echo "🚀 Initializing Railway project..."
    railway init
fi

# Set up environment variables
echo "⚙️  Setting up environment variables..."

# Required variables
railway variables set GOOGLE_CREDENTIALS_FILE=credentials.json
railway variables set LOG_LEVEL=INFO
railway variables set PYTHONUNBUFFERED=1

# Authentication variables
railway variables set REQUIRE_AUTH=true
railway variables set APP_PASSWORD=survey2025!
railway variables set PORT=5001

echo "✅ Basic environment variables set"
echo "🔐 Authentication configured with default password: survey2025!"
echo "   Change APP_PASSWORD in Railway dashboard for production"

# Optional: Upload credentials file if it exists
if [ -f "credentials.json" ]; then
    echo "📤 Uploading credentials.json..."
    # Note: Railway doesn't have a direct file upload via CLI
    # The file needs to be in the repository or set as an environment variable
    echo "   Make sure credentials.json is in your repository or"
    echo "   set GOOGLE_CREDENTIALS_JSON as an environment variable"
fi

# Deploy to Railway
echo "🚀 Deploying to Railway..."
railway up

# Get the deployment URL
echo "🌐 Getting deployment URL..."
RAILWAY_URL=$(railway domain 2>/dev/null || echo "URL not available yet")

echo ""
echo "🎉 Deployment initiated!"
echo "============================================================"
echo "📊 Monitor deployment:"
echo "   railway logs --follow"
echo ""
echo "🏥 Health check endpoints:"
echo "   ${RAILWAY_URL}/health"
echo "   ${RAILWAY_URL}/health/status"
echo "   ${RAILWAY_URL}/health/dashboard"
echo "   ${RAILWAY_URL}/health/test"
echo ""
echo "📋 Verify deployment:"
echo "   curl ${RAILWAY_URL}/health/test"
echo ""
echo "🔍 Debug if needed:"
echo "   railway logs --filter \"Health Check\""
echo "   railway logs --filter \"ERROR\""
echo ""

# Test health endpoint if deployment URL is available
if [[ $RAILWAY_URL != "URL not available yet" ]] && [[ $RAILWAY_URL != "" ]]; then
    echo "🧪 Testing health endpoint..."
    sleep 10  # Wait for deployment to be ready
    
    if curl -f "${RAILWAY_URL}/health/test" > /dev/null 2>&1; then
        echo "✅ Health endpoint responding"
    else
        echo "⚠️  Health endpoint not responding yet - check logs:"
        echo "   railway logs"
    fi
fi

echo ""
echo "🚂 Railway deployment configuration complete!"
echo "   Check Railway dashboard for deployment status"
echo "   Monitor logs: railway logs --follow"
