#!/bin/bash

# Quick fix for Railway deployment issues
# This script deploys a simplified version that should work

set -e

echo "🚂 Railway Deployment Quick Fix"
echo "==============================="

# Check Railway CLI
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Please install it first:"
    echo "npm install -g @railway/cli"
    exit 1
fi

# Check login
if ! railway whoami &> /dev/null; then
    echo "❌ Please log in to Railway first:"
    echo "railway login"
    exit 1
fi

echo "✅ Railway CLI ready"

# Set minimal environment variables for quick deployment
echo ""
echo "⚙️ Setting minimal environment variables..."

railway variables set REQUIRE_AUTH=false
railway variables set PORT=5001
railway variables set LOG_LEVEL=INFO
railway variables set PYTHONUNBUFFERED=1

echo "✅ Environment variables set"

# Deploy the simplified app
echo ""
echo "🚀 Deploying simplified Railway app..."
echo "This uses railway_app.py which has better error handling"

railway up

echo ""
echo "⏳ Waiting for deployment to complete..."
sleep 15

# Get the URL and test
RAILWAY_URL=$(railway domain 2>/dev/null || echo "")

if [ -n "$RAILWAY_URL" ]; then
    echo ""
    echo "🌐 Testing deployment: $RAILWAY_URL"
    
    # Test health endpoint
    echo "Testing health endpoint..."
    if curl -f -m 15 "$RAILWAY_URL/health/test" > /dev/null 2>&1; then
        echo "✅ Health endpoint working!"
        
        # Get response
        RESPONSE=$(curl -s -m 10 "$RAILWAY_URL/health/test" 2>/dev/null || echo "{}")
        echo ""
        echo "📊 Deployment Info:"
        echo "$RESPONSE" | jq -r '.message // "JJF Survey Analytics is running"' 2>/dev/null || echo "Application is running"
        
        # Test main endpoint
        echo ""
        echo "Testing main application..."
        MAIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -m 10 "$RAILWAY_URL/" 2>/dev/null || echo "000")
        
        if [ "$MAIN_STATUS" = "200" ]; then
            echo "✅ Main application working! (HTTP $MAIN_STATUS)"
        elif [ "$MAIN_STATUS" = "302" ]; then
            echo "✅ Main application working! (HTTP $MAIN_STATUS - redirect to login)"
        else
            echo "⚠️ Main application status: HTTP $MAIN_STATUS"
        fi
        
    else
        echo "❌ Health endpoint not responding"
        echo ""
        echo "🔍 Checking logs for errors..."
        railway logs --tail 10
    fi
    
    echo ""
    echo "🎉 Deployment Complete!"
    echo "======================"
    echo "🌐 Application URL: $RAILWAY_URL"
    echo "🏥 Health Check: $RAILWAY_URL/health/test"
    echo "📊 System Status: $RAILWAY_URL/health/status"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Visit $RAILWAY_URL to access the application"
    echo "2. Authentication is disabled for this quick fix"
    echo "3. Monitor logs: railway logs --follow"
    echo "4. To enable auth later: railway variables set REQUIRE_AUTH=true"
    
else
    echo "❌ Could not get Railway URL"
    echo "Check deployment status: railway status"
fi

echo ""
echo "🔧 If there are still issues:"
echo "1. Check logs: railway logs --tail 20"
echo "2. Check status: railway status"
echo "3. Debug with: ./debug-railway.sh"
