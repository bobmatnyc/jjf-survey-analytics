#!/bin/bash

echo "🚂 Deploying Minimal Flask App to Railway"
echo "========================================"

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo "❌ Please log in to Railway first:"
    echo "railway login"
    exit 1
fi

echo "✅ Railway CLI ready"

# Link to correct project if needed
echo "🔗 Linking to project..."
railway link

# Set minimal environment variables
echo "⚙️ Setting environment variables..."
railway variables set PORT=5001
railway variables set PYTHONUNBUFFERED=1

# Deploy
echo "🚀 Deploying minimal app..."
railway up

echo ""
echo "⏳ Waiting for deployment..."
sleep 20

# Test deployment
RAILWAY_URL=$(railway domain 2>/dev/null || echo "")

if [ -n "$RAILWAY_URL" ]; then
    echo ""
    echo "🧪 Testing deployment..."
    
    if curl -f -m 10 "$RAILWAY_URL/health" > /dev/null 2>&1; then
        echo "✅ Deployment successful!"
        echo ""
        echo "🌐 Your app is running at: $RAILWAY_URL"
        echo "🏥 Health check: $RAILWAY_URL/health"
        echo "🧪 Test endpoint: $RAILWAY_URL/test"
        
    else
        echo "❌ Health check failed"
        echo "🔍 Checking logs..."
        railway logs --tail 10
    fi
else
    echo "❌ Could not get Railway URL"
    echo "Check status: railway status"
fi

echo ""
echo "📋 To monitor: railway logs --follow"
