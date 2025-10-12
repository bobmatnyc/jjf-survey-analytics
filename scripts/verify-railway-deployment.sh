#!/bin/bash

# Railway Deployment Verification Script
# This script verifies that the health check system is working correctly on Railway

set -e

echo "🔍 Railway Deployment Verification"
echo "=================================="

# Get Railway URL
RAILWAY_URL=$(railway domain 2>/dev/null || echo "")

if [ -z "$RAILWAY_URL" ]; then
    echo "❌ Could not get Railway URL. Make sure you're in a Railway project directory."
    echo "   Run: railway login && railway link"
    exit 1
fi

echo "🌐 Testing Railway deployment: $RAILWAY_URL"
echo ""

# Test basic connectivity
echo "1. Testing basic connectivity..."
if curl -f "$RAILWAY_URL" > /dev/null 2>&1; then
    echo "   ✅ Basic connectivity: OK"
else
    echo "   ❌ Basic connectivity: FAILED"
    echo "   Check Railway logs: railway logs"
    exit 1
fi

# Test health endpoints
echo ""
echo "2. Testing health endpoints..."

# Test /health/test endpoint
echo "   Testing /health/test..."
if curl -f "$RAILWAY_URL/health/test" > /dev/null 2>&1; then
    echo "   ✅ Health test endpoint: OK"
    
    # Get detailed info
    TEST_RESPONSE=$(curl -s "$RAILWAY_URL/health/test")
    RAILWAY_ENV=$(echo "$TEST_RESPONSE" | jq -r '.deployment.railway_environment // "unknown"')
    DEPLOYMENT_ID=$(echo "$TEST_RESPONSE" | jq -r '.deployment.railway_deployment_id // "unknown"')
    
    echo "      Environment: $RAILWAY_ENV"
    echo "      Deployment ID: ${DEPLOYMENT_ID:0:8}..."
else
    echo "   ❌ Health test endpoint: FAILED"
fi

# Test /health/status endpoint (used by Railway)
echo "   Testing /health/status..."
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$RAILWAY_URL/health/status")
if [ "$STATUS_CODE" = "200" ]; then
    echo "   ✅ Health status endpoint: OK (HTTP $STATUS_CODE)"
else
    echo "   ⚠️  Health status endpoint: HTTP $STATUS_CODE"
    if [ "$STATUS_CODE" = "503" ]; then
        echo "      This indicates health check failures - check logs"
    fi
fi

# Test main /health endpoint (comprehensive)
echo "   Testing /health..."
HEALTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$RAILWAY_URL/health")
if [ "$HEALTH_CODE" = "200" ]; then
    echo "   ✅ Main health endpoint: OK (HTTP $HEALTH_CODE)"
    
    # Get health summary
    HEALTH_RESPONSE=$(curl -s "$RAILWAY_URL/health")
    OVERALL_STATUS=$(echo "$HEALTH_RESPONSE" | jq -r '.overall_status // "unknown"')
    TOTAL_CHECKS=$(echo "$HEALTH_RESPONSE" | jq -r '.summary.total // 0')
    PASSED_CHECKS=$(echo "$HEALTH_RESPONSE" | jq -r '.summary.passed // 0')
    FAILED_CHECKS=$(echo "$HEALTH_RESPONSE" | jq -r '.summary.failed // 0')
    
    echo "      Overall Status: $OVERALL_STATUS"
    echo "      Health Checks: $PASSED_CHECKS/$TOTAL_CHECKS passed, $FAILED_CHECKS failed"
else
    echo "   ⚠️  Main health endpoint: HTTP $HEALTH_CODE"
    if [ "$HEALTH_CODE" = "503" ]; then
        echo "      This indicates system health issues"
    fi
fi

# Test health dashboard
echo "   Testing /health/dashboard..."
if curl -f "$RAILWAY_URL/health/dashboard" > /dev/null 2>&1; then
    echo "   ✅ Health dashboard: OK"
    echo "      View at: $RAILWAY_URL/health/dashboard"
else
    echo "   ❌ Health dashboard: FAILED"
fi

# Check Railway configuration
echo ""
echo "3. Checking Railway configuration..."

# Check if railway.toml exists
if [ -f "railway.toml" ]; then
    echo "   ✅ railway.toml: Found"
    
    # Check health check configuration
    if grep -q "healthcheckPath.*health" railway.toml; then
        echo "   ✅ Health check path configured"
    else
        echo "   ⚠️  Health check path not configured in railway.toml"
    fi
else
    echo "   ⚠️  railway.toml: Not found"
fi

# Check environment variables
echo ""
echo "4. Checking environment variables..."
ENV_VARS=$(railway variables 2>/dev/null || echo "")

if echo "$ENV_VARS" | grep -q "GOOGLE_CREDENTIALS_FILE"; then
    echo "   ✅ GOOGLE_CREDENTIALS_FILE: Set"
else
    echo "   ⚠️  GOOGLE_CREDENTIALS_FILE: Not set"
fi

if echo "$ENV_VARS" | grep -q "LOG_LEVEL"; then
    echo "   ✅ LOG_LEVEL: Set"
else
    echo "   ⚠️  LOG_LEVEL: Not set"
fi

# Check recent logs for health check activity
echo ""
echo "5. Checking recent health check activity..."
RECENT_LOGS=$(railway logs --tail 20 2>/dev/null || echo "")

if echo "$RECENT_LOGS" | grep -q "Health check"; then
    echo "   ✅ Health check activity found in logs"
    
    # Count health check entries
    HEALTH_LOG_COUNT=$(echo "$RECENT_LOGS" | grep -c "Health check" || echo "0")
    echo "      Recent health check log entries: $HEALTH_LOG_COUNT"
else
    echo "   ⚠️  No recent health check activity in logs"
fi

if echo "$RECENT_LOGS" | grep -q "ERROR"; then
    echo "   ⚠️  Errors found in recent logs - check: railway logs --filter ERROR"
else
    echo "   ✅ No errors in recent logs"
fi

# Performance test
echo ""
echo "6. Testing health check performance..."
START_TIME=$(date +%s%3N)
curl -s "$RAILWAY_URL/health/status" > /dev/null
END_TIME=$(date +%s%3N)
RESPONSE_TIME=$((END_TIME - START_TIME))

echo "   Health check response time: ${RESPONSE_TIME}ms"

if [ "$RESPONSE_TIME" -lt 5000 ]; then
    echo "   ✅ Response time: Good (< 5s)"
elif [ "$RESPONSE_TIME" -lt 10000 ]; then
    echo "   ⚠️  Response time: Acceptable (< 10s)"
else
    echo "   ❌ Response time: Too slow (> 10s)"
fi

# Summary
echo ""
echo "📊 Verification Summary"
echo "======================"

# Overall assessment
ISSUES=0

if [ "$STATUS_CODE" != "200" ]; then
    ISSUES=$((ISSUES + 1))
fi

if [ "$HEALTH_CODE" != "200" ]; then
    ISSUES=$((ISSUES + 1))
fi

if [ "$RESPONSE_TIME" -gt 10000 ]; then
    ISSUES=$((ISSUES + 1))
fi

if [ "$ISSUES" -eq 0 ]; then
    echo "✅ All checks passed! Your Railway deployment is healthy."
    echo ""
    echo "🔗 Application URLs:"
    echo "   Main App: $RAILWAY_URL"
    echo "   Health Dashboard: $RAILWAY_URL/health/dashboard"
    echo "   Health Status: $RAILWAY_URL/health/status"
    echo ""
    echo "📊 Monitoring:"
    echo "   railway logs --follow"
    echo "   railway logs --filter \"Health Check\""
elif [ "$ISSUES" -eq 1 ]; then
    echo "⚠️  1 issue found - check the warnings above"
else
    echo "❌ $ISSUES issues found - review the failures above"
    echo ""
    echo "🔍 Debugging steps:"
    echo "   railway logs --tail 50"
    echo "   railway logs --filter ERROR"
    echo "   railway status"
fi

echo ""
echo "🚂 Railway Health Check Configuration Complete!"
