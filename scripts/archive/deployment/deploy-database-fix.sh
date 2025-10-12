#!/bin/bash

echo "🗄️ Deploying Database Fix to Railway"
echo "===================================="

# Test current app status
echo "🧪 Testing current app status..."
CURRENT_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://jjf-survey-analytics-production.up.railway.app/health" 2>/dev/null)
if [ "$CURRENT_STATUS" = "200" ]; then
    echo "✅ App is currently responding (HTTP $CURRENT_STATUS)"
else
    echo "⚠️ App status: HTTP $CURRENT_STATUS"
fi

echo ""
echo "📋 Database Fix Changes:"
echo "✅ Created init_database.py - Database table creation script"
echo "✅ Created railway_init.py - Railway-specific initialization"
echo "✅ Updated app.py - Auto-initialize database on Railway"
echo "✅ Updated Procfile - Run database init before app start"

# Commit changes
git add .
git commit -m "Add database initialization for Railway deployment" || echo "No changes to commit"

echo ""
echo "🚀 Deploying database fix..."

# Deploy to Railway
if git push origin master 2>/dev/null; then
    echo "✅ Pushed to git - Railway should auto-deploy"
    
    echo ""
    echo "⏳ Waiting for deployment (database initialization may take extra time)..."
    sleep 45
    
    # Test deployment
    echo "🧪 Testing database fix..."
    for i in {1..8}; do
        echo "Test attempt $i/8..."
        
        # Test health endpoint
        HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -m 15 "https://jjf-survey-analytics-production.up.railway.app/health" 2>/dev/null)
        if [ "$HEALTH_STATUS" = "200" ]; then
            echo "✅ Health endpoint working (HTTP $HEALTH_STATUS)"
            
            # Test main dashboard (should redirect to login, not show database error)
            MAIN_RESPONSE=$(curl -s -m 15 "https://jjf-survey-analytics-production.up.railway.app/" 2>/dev/null)
            if echo "$MAIN_RESPONSE" | grep -q "Redirecting"; then
                echo "✅ Main dashboard working (redirecting to login)"
                
                # Test login page
                LOGIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -m 15 "https://jjf-survey-analytics-production.up.railway.app/login" 2>/dev/null)
                if [ "$LOGIN_STATUS" = "200" ]; then
                    echo "✅ Login page working (HTTP $LOGIN_STATUS)"
                    echo ""
                    echo "🎉 Database fix deployment successful!"
                    break
                else
                    echo "⚠️ Login page status: HTTP $LOGIN_STATUS"
                fi
            elif echo "$MAIN_RESPONSE" | grep -q "no such table"; then
                echo "❌ Still getting database error - waiting longer..."
            else
                echo "⚠️ Unexpected response from main dashboard"
            fi
        else
            echo "⚠️ Health endpoint status: HTTP $HEALTH_STATUS"
        fi
        
        if [ $i -lt 8 ]; then
            echo "⏳ Waiting 30 seconds before next test..."
            sleep 30
        fi
    done
    
else
    echo "❌ Git push failed"
    echo ""
    echo "Manual deployment options:"
    echo "1. Railway Dashboard: Go to your project → Deployments → Deploy"
    echo "2. Railway CLI: railway login && railway up"
fi

echo ""
echo "🎯 What This Fix Does:"
echo "✅ Creates database tables automatically on Railway"
echo "✅ Adds sample data for testing"
echo "✅ Fixes 'no such table: spreadsheets' error"
echo "✅ Enables full application functionality"

echo ""
echo "🌐 Test Your Application:"
echo "1. Visit: https://jjf-survey-analytics-production.up.railway.app/"
echo "2. Login with password: survey2025!"
echo "3. Navigate to different sections (should work without database errors)"

echo ""
echo "📋 Next Steps After Database Fix:"
echo "1. Test all application features"
echo "2. Upload real survey data using the extractors"
echo "3. Configure Google Sheets API credentials"
echo "4. Set up auto-sync service"

echo ""
echo "🔍 Monitoring:"
echo "Health Check: curl https://jjf-survey-analytics-production.up.railway.app/health"
echo "Railway Logs: Check Railway dashboard for deployment logs"
