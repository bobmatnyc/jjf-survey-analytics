#!/bin/bash

# Railway Deployment Debug Script
# This script helps debug Railway deployment issues

set -e

echo "🔍 Railway Deployment Debug"
echo "=========================="

# Check Railway CLI
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
    echo "✅ Railway CLI installed"
fi

# Check login status
if ! railway whoami &> /dev/null; then
    echo "❌ Not logged in to Railway"
    echo "Please run: railway login"
    exit 1
fi

echo "✅ Railway CLI ready"

# Get project info
echo ""
echo "📋 Project Information:"
PROJECT_INFO=$(railway status 2>/dev/null || echo "No project linked")
echo "$PROJECT_INFO"

# Check environment variables
echo ""
echo "⚙️ Environment Variables:"
railway variables 2>/dev/null || echo "Could not fetch variables"

# Check recent logs
echo ""
echo "📜 Recent Logs (last 20 lines):"
echo "================================"
railway logs --tail 20 2>/dev/null || echo "Could not fetch logs"

# Check deployment status
echo ""
echo "🚀 Deployment Status:"
echo "===================="
railway status 2>/dev/null || echo "Could not fetch status"

# Test endpoints if URL is available
RAILWAY_URL=$(railway domain 2>/dev/null || echo "")

if [ -n "$RAILWAY_URL" ]; then
    echo ""
    echo "🌐 Testing Endpoints:"
    echo "===================="
    echo "URL: $RAILWAY_URL"
    
    # Test health endpoint
    echo ""
    echo "Testing /health/test..."
    if curl -f -m 10 "$RAILWAY_URL/health/test" > /dev/null 2>&1; then
        echo "✅ /health/test: OK"
        
        # Get detailed info
        TEST_RESPONSE=$(curl -s -m 10 "$RAILWAY_URL/health/test" 2>/dev/null || echo "{}")
        echo "Response preview:"
        echo "$TEST_RESPONSE" | jq -r '.message // "No message"' 2>/dev/null || echo "Could not parse response"
    else
        echo "❌ /health/test: FAILED"
    fi
    
    # Test health status
    echo ""
    echo "Testing /health/status..."
    STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 10 "$RAILWAY_URL/health/status" 2>/dev/null || echo "000")
    if [ "$STATUS_CODE" = "200" ]; then
        echo "✅ /health/status: OK (HTTP $STATUS_CODE)"
    else
        echo "❌ /health/status: FAILED (HTTP $STATUS_CODE)"
    fi
    
    # Test main endpoint
    echo ""
    echo "Testing main endpoint..."
    MAIN_CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 10 "$RAILWAY_URL/" 2>/dev/null || echo "000")
    echo "Main endpoint: HTTP $MAIN_CODE"
    
else
    echo ""
    echo "⚠️ No Railway URL available"
fi

# Check local files
echo ""
echo "📁 Local Files Check:"
echo "===================="

REQUIRED_FILES=(
    "railway_app.py"
    "requirements.txt"
    "railway.toml"
    "nixpacks.toml"
    "Procfile"
    "templates/login.html"
    "templates/error.html"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file: Found"
    else
        echo "❌ $file: Missing"
    fi
done

# Check Python syntax
echo ""
echo "🐍 Python Syntax Check:"
echo "======================="
if python -m py_compile railway_app.py 2>/dev/null; then
    echo "✅ railway_app.py: Syntax OK"
else
    echo "❌ railway_app.py: Syntax Error"
    python -m py_compile railway_app.py
fi

# Check requirements
echo ""
echo "📦 Requirements Check:"
echo "===================="
if [ -f "requirements.txt" ]; then
    echo "Requirements.txt contents:"
    cat requirements.txt | head -10
    
    # Check if Flask is included
    if grep -q "Flask" requirements.txt; then
        echo "✅ Flask found in requirements.txt"
    else
        echo "❌ Flask missing from requirements.txt"
    fi
else
    echo "❌ requirements.txt not found"
fi

# Deployment recommendations
echo ""
echo "💡 Deployment Recommendations:"
echo "=============================="

if [ "$STATUS_CODE" != "200" ] && [ "$MAIN_CODE" != "200" ]; then
    echo "🔧 Application not responding. Try these steps:"
    echo ""
    echo "1. Check logs for errors:"
    echo "   railway logs --tail 50"
    echo ""
    echo "2. Redeploy with the simplified app:"
    echo "   railway up"
    echo ""
    echo "3. Check environment variables:"
    echo "   railway variables"
    echo ""
    echo "4. Set required variables if missing:"
    echo "   railway variables set REQUIRE_AUTH=false"
    echo "   railway variables set PORT=5001"
    echo ""
    echo "5. Monitor deployment:"
    echo "   railway logs --follow"
fi

# Quick fix deployment
echo ""
echo "🚀 Quick Fix Deployment:"
echo "======================="
echo "To deploy the simplified Railway app:"
echo ""
echo "railway variables set REQUIRE_AUTH=false"
echo "railway variables set PORT=5001"
echo "railway up"
echo ""
echo "Then monitor with:"
echo "railway logs --follow"

echo ""
echo "🔍 Debug complete!"
echo ""
echo "If the application is still not working:"
echo "1. Check the logs: railway logs --tail 50"
echo "2. Try the quick fix deployment above"
echo "3. Test the health endpoint: curl $RAILWAY_URL/health/test"
