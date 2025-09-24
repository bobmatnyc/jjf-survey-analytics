#!/bin/bash

echo "🔧 Fixing Railway Port Issue"
echo "============================"

# Commit the port fixes
git add .
git commit -m "Fix Railway port binding - use dynamic PORT from Railway" || echo "No changes to commit"

echo "📋 Changes made:"
echo "✅ Updated minimal_app.py - better port detection"
echo "✅ Updated Procfile - use Railway's PORT variable directly"
echo "✅ Added debugging for port environment variables"

echo ""
echo "🚀 Next steps:"
echo "1. Push to git (if Railway is connected to GitHub):"
echo "   git push origin main"
echo ""
echo "2. Or use Railway CLI:"
echo "   railway login"
echo "   railway link"
echo "   railway up"
echo ""
echo "3. Or redeploy from Railway dashboard:"
echo "   Go to Railway dashboard → Your project → Deployments → Deploy"

echo ""
echo "🎯 Expected result:"
echo "The app should now bind to whatever port Railway assigns"
echo "instead of hardcoded 5001"

# Try to push to git
if git remote -v | grep -q origin; then
    echo ""
    echo "🔄 Attempting to push to git..."
    if git push origin main 2>/dev/null || git push origin master 2>/dev/null; then
        echo "✅ Pushed to git - Railway should auto-deploy"
        echo ""
        echo "⏳ Wait 1-2 minutes, then test:"
        echo "curl https://jjf-survey-analytics-production.up.railway.app/health"
    else
        echo "⚠️ Git push failed - deploy manually via Railway dashboard"
    fi
else
    echo "⚠️ No git remote found - deploy manually via Railway dashboard"
fi
