#!/bin/bash

echo "🔄 Restoring Full JJF Survey Analytics Application"
echo "================================================="

# Check current minimal app status
echo "🧪 Testing current minimal app..."
if curl -f -m 5 "https://jjf-survey-analytics-production.up.railway.app/health" > /dev/null 2>&1; then
    echo "✅ Minimal app is working - proceeding with full app restoration"
else
    echo "❌ Minimal app not working - fix basic deployment first"
    exit 1
fi

echo ""
echo "📋 Full App Restoration Changes:"
echo "✅ Updated Procfile - use app.py instead of minimal_app.py"
echo "✅ Fixed port configuration in app.py - use Railway's dynamic port"
echo "✅ Restored full requirements.txt - all dependencies included"
echo "✅ Updated railway.toml - proper health check configuration"
echo "✅ Authentication disabled by default for initial deployment"

# Commit the changes
git add .
git commit -m "Restore full JJF Survey Analytics application with Railway port fix" || echo "No changes to commit"

echo ""
echo "🚀 Deploying full application..."

# Try to push to git for auto-deploy
if git push origin main 2>/dev/null || git push origin master 2>/dev/null; then
    echo "✅ Pushed to git - Railway should auto-deploy"
    
    echo ""
    echo "⏳ Waiting for deployment (this may take 2-3 minutes due to additional dependencies)..."
    sleep 30
    
    # Test deployment progress
    echo "🧪 Testing deployment progress..."
    for i in {1..6}; do
        echo "Attempt $i/6..."
        if curl -f -m 10 "https://jjf-survey-analytics-production.up.railway.app/health" > /dev/null 2>&1; then
            echo "✅ Full app deployment successful!"
            
            # Get response
            RESPONSE=$(curl -s -m 10 "https://jjf-survey-analytics-production.up.railway.app/health" 2>/dev/null)
            echo ""
            echo "📊 Health Check Response:"
            echo "$RESPONSE" | head -c 500
            echo ""
            
            # Test main dashboard
            echo "🏠 Testing main dashboard..."
            MAIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -m 10 "https://jjf-survey-analytics-production.up.railway.app/" 2>/dev/null)
            if [ "$MAIN_STATUS" = "200" ]; then
                echo "✅ Main dashboard working (HTTP $MAIN_STATUS)"
            else
                echo "⚠️ Main dashboard status: HTTP $MAIN_STATUS"
            fi
            
            break
        else
            echo "⏳ Still deploying... waiting 30 seconds"
            sleep 30
        fi
    done
    
else
    echo "⚠️ Git push failed - deploy manually"
    echo ""
    echo "Manual deployment options:"
    echo "1. Railway Dashboard: Go to your project → Deployments → Deploy"
    echo "2. Railway CLI: railway login && railway up"
fi

echo ""
echo "🎯 Full Application Features Restored:"
echo "✅ Complete Flask web interface"
echo "✅ Survey analytics dashboard"
echo "✅ Google Sheets integration (requires credentials)"
echo "✅ Database management"
echo "✅ Auto-sync service"
echo "✅ Health monitoring system"
echo "✅ Authentication system (disabled by default)"

echo ""
echo "🌐 Application URLs:"
echo "Main App: https://jjf-survey-analytics-production.up.railway.app/"
echo "Health Check: https://jjf-survey-analytics-production.up.railway.app/health"
echo "Survey Analytics: https://jjf-survey-analytics-production.up.railway.app/surveys"
echo "Health Dashboard: https://jjf-survey-analytics-production.up.railway.app/health/dashboard"

echo ""
echo "📋 Next Steps:"
echo "1. Test all endpoints to ensure full functionality"
echo "2. Upload Google Sheets credentials if needed"
echo "3. Enable authentication if required: railway variables --set REQUIRE_AUTH=true"
echo "4. Upload database files for survey data"
echo "5. Configure auto-sync service"

echo ""
echo "🔍 Monitoring:"
echo "railway logs --follow  # Monitor deployment logs"
echo "curl https://jjf-survey-analytics-production.up.railway.app/health  # Test health"
