#!/bin/bash

echo "🚂 Simple Railway Deployment"
echo "============================"

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo "❌ Please log in to Railway first:"
    echo "railway login"
    exit 1
fi

echo "✅ Railway CLI ready"

# Show current project
echo "📋 Current project:"
railway status 2>/dev/null || echo "No project status available"

# Set environment variables using the new syntax
echo "⚙️ Setting environment variables..."

# Try different Railway CLI syntaxes
if railway variables --set "PYTHONUNBUFFERED=1" 2>/dev/null; then
    echo "✅ Set PYTHONUNBUFFERED"
else
    echo "⚠️ Could not set PYTHONUNBUFFERED"
fi

# Force push the code
echo "🚀 Force deploying..."
git add .
git commit -m "Deploy minimal Flask app with gunicorn" || echo "No changes to commit"

# Try to deploy
if railway up --detach 2>/dev/null; then
    echo "✅ Deployment initiated"
else
    echo "⚠️ Using alternative deployment method..."
    # Alternative: push to git if Railway is connected to GitHub
    git push origin main 2>/dev/null || git push origin master 2>/dev/null || echo "Git push failed"
fi

echo ""
echo "⏳ Waiting for deployment (30 seconds)..."
sleep 30

# Test the deployment
echo "🧪 Testing deployment..."
URL="https://jjf-survey-analytics-production.up.railway.app"

echo "Testing $URL/health..."
if curl -f -m 10 "$URL/health" > /dev/null 2>&1; then
    echo "✅ Health endpoint working!"
    
    # Get the response
    RESPONSE=$(curl -s -m 10 "$URL/health" 2>/dev/null)
    echo "Response: $RESPONSE" | head -c 200
    echo ""
    
    echo ""
    echo "🎉 Deployment successful!"
    echo "🌐 App URL: $URL"
    echo "🏥 Health: $URL/health"
    echo "🧪 Test: $URL/test"
    
else
    echo "❌ Health endpoint not responding"
    echo ""
    echo "🔍 Troubleshooting steps:"
    echo "1. Check logs: railway logs --tail 20"
    echo "2. Check status: railway status"
    echo "3. Wait longer (deployments can take 2-3 minutes)"
    echo "4. Try: curl -v $URL/health"
fi

echo ""
echo "📋 Next steps:"
echo "- Monitor: railway logs --follow"
echo "- Status: railway status"
echo "- Test: curl $URL/health"
