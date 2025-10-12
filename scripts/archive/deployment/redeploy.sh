#!/bin/bash

echo "🔄 Redeploying with Port Fix"
echo "============================"

# Test current status
echo "🧪 Testing current deployment..."
if curl -f -m 5 "https://jjf-survey-analytics-production.up.railway.app/health" > /dev/null 2>&1; then
    echo "✅ App is already working!"
    exit 0
else
    echo "❌ App not responding, redeploying..."
fi

# Commit changes
git add .
git commit -m "Fix port binding for Railway" || echo "No changes to commit"

# Push to trigger redeploy (if Railway is connected to GitHub)
if git push origin main 2>/dev/null || git push origin master 2>/dev/null; then
    echo "✅ Pushed to git - Railway should auto-deploy"
else
    echo "⚠️ Git push failed, trying Railway CLI..."
    
    # Try Railway CLI
    if railway login --help > /dev/null 2>&1; then
        echo "Please run: railway login && railway up"
    fi
fi

echo ""
echo "⏳ Waiting 30 seconds for deployment..."
sleep 30

# Test again
echo "🧪 Testing deployment..."
if curl -f -m 10 "https://jjf-survey-analytics-production.up.railway.app/health" > /dev/null 2>&1; then
    echo "✅ Deployment successful!"
    
    # Get response
    RESPONSE=$(curl -s -m 5 "https://jjf-survey-analytics-production.up.railway.app/health" 2>/dev/null)
    echo "Health check response:"
    echo "$RESPONSE" | head -c 300
    echo ""
    
    echo ""
    echo "🎉 App is now working!"
    echo "🌐 URL: https://jjf-survey-analytics-production.up.railway.app"
    
else
    echo "❌ Still not responding"
    echo ""
    echo "🔍 Manual steps to try:"
    echo "1. railway login"
    echo "2. railway link (select jjf-survey-analytics-production)"
    echo "3. railway logs"
    echo "4. railway up"
fi
