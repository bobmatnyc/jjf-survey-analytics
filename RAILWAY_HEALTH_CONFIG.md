# Railway Health Check Configuration

This guide shows how to configure Railway to use the `/health` endpoint for monitoring your JJF Survey Analytics application.

## 🚂 Railway Configuration Files

### 1. railway.toml
```toml
[build]
builder = "nixpacks"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 60
healthcheckInterval = 30
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3

[environments.production]
variables = { 
  LOG_LEVEL = "INFO",
  RAILWAY_ENVIRONMENT = "production"
}

[environments.staging]
variables = { 
  LOG_LEVEL = "DEBUG",
  RAILWAY_ENVIRONMENT = "staging"
}
```

### 2. nixpacks.toml
```toml
[phases.setup]
nixPkgs = ["python39", "pip"]

[phases.install]
cmds = ["pip install -r requirements.txt"]

[phases.build]
cmds = ["echo 'Build phase - preparing application'"]

[start]
cmd = "python app.py"

[variables]
PYTHONPATH = "/app"
PYTHONUNBUFFERED = "1"
```

### 3. Procfile
```
web: python app.py
```

## 🔧 Railway Dashboard Configuration

### Step 1: Project Settings

1. Go to your Railway project dashboard
2. Navigate to **Settings** → **Deploy**
3. Configure the following:

```
Health Check Path: /health
Health Check Timeout: 60 seconds
Health Check Interval: 30 seconds
Restart Policy: On Failure
Max Retries: 3
```

### Step 2: Environment Variables

Set these variables in **Settings** → **Variables**:

#### Required Variables
```bash
GOOGLE_CREDENTIALS_FILE=credentials.json
LOG_LEVEL=INFO
PYTHONUNBUFFERED=1
```

#### Optional Variables
```bash
# Database configuration
DATABASE_URL=sqlite:///surveyor_data_improved.db

# Health check configuration
HEALTH_CHECK_CACHE_DURATION=30

# Alert configuration (if using notifications)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_FROM_EMAIL=alerts@yourcompany.com
ALERT_TO_EMAILS=admin@yourcompany.com
```

### Step 3: Google Credentials

Choose one of these methods:

#### Method 1: Upload File (Recommended)
1. Add `credentials.json` to your repository
2. Set `GOOGLE_CREDENTIALS_FILE=credentials.json`
3. **Important**: Add to `.gitignore` for security

#### Method 2: Environment Variable
1. Copy the entire JSON content
2. Set `GOOGLE_CREDENTIALS_JSON` with the JSON string
3. Update app.py to handle this variable

## 🚀 Deployment Process

### Automated Deployment

Use the provided deployment script:

```bash
./deploy-railway.sh
```

### Manual Deployment

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project (if not done)
railway init

# Set environment variables
railway variables set GOOGLE_CREDENTIALS_FILE=credentials.json
railway variables set LOG_LEVEL=INFO

# Deploy
railway up

# Monitor deployment
railway logs --follow
```

## 📊 Health Check Monitoring

### Railway Health Check Behavior

Railway will:
1. **During Deployment**: Check `/health` endpoint every 30 seconds
2. **Post-Deployment**: Continue monitoring every 30 seconds
3. **On Failure**: Restart the service (up to 3 times)
4. **Timeout**: Fail health check after 60 seconds

### Health Check Response

The `/health` endpoint returns:

#### Healthy Response (200)
```json
{
  "overall_status": "pass",
  "timestamp": "2025-01-23T10:30:00.000Z",
  "duration_ms": 1234,
  "summary": {
    "total": 15,
    "passed": 15,
    "failed": 0,
    "warnings": 0
  },
  "railway_info": {
    "environment": "production",
    "service_name": "jjf-survey-analytics",
    "deployment_id": "abc123",
    "health_check_duration_ms": 1234
  }
}
```

#### Unhealthy Response (503)
```json
{
  "overall_status": "fail",
  "timestamp": "2025-01-23T10:30:00.000Z",
  "summary": {
    "total": 15,
    "passed": 12,
    "failed": 3,
    "warnings": 0
  },
  "railway_info": {
    "environment": "production",
    "service_name": "jjf-survey-analytics",
    "deployment_id": "abc123"
  }
}
```

## 📋 Verification Steps

### 1. Deployment Verification

```bash
# Check deployment status
railway status

# View recent logs
railway logs --tail 50

# Test health endpoint
curl https://your-app.railway.app/health/test
```

### 2. Health Check Verification

```bash
# Test main health endpoint
curl https://your-app.railway.app/health

# Test quick status
curl https://your-app.railway.app/health/status

# View health dashboard
open https://your-app.railway.app/health/dashboard
```

### 3. Log Monitoring

```bash
# Monitor health check logs
railway logs --filter "Health Check" --follow

# Monitor errors
railway logs --filter "ERROR" --follow

# Monitor Railway-specific logs
railway logs --filter "Railway" --follow
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Health Check Timeouts
```
Health check timeout after 60 seconds
```
**Solutions:**
- Increase `healthcheckTimeout` in `railway.toml`
- Optimize health check performance
- Check for slow database queries

#### 2. Credentials Not Found
```
❌ API Health Check FAILED - Google Credentials: Credentials file not found
```
**Solutions:**
- Verify `GOOGLE_CREDENTIALS_FILE` environment variable
- Check if `credentials.json` is in repository
- Use `GOOGLE_CREDENTIALS_JSON` environment variable instead

#### 3. Database Connection Issues
```
❌ SQLite Databases: No database files found
```
**Solutions:**
- Upload database files to repository
- Run data extraction after deployment
- Check file paths and permissions

### Debug Commands

```bash
# Check environment variables
railway variables

# View detailed logs
railway logs --json | jq '.message'

# Check service status
railway status

# Test specific endpoints
curl -v https://your-app.railway.app/health/test
curl -v https://your-app.railway.app/health/status
```

## 📈 Monitoring Best Practices

### 1. Log Analysis

Monitor these log patterns:

```bash
# Successful health checks
railway logs --filter "Health check completed"

# Failed health checks
railway logs --filter "HEALTH CHECK FAILURE"

# Performance monitoring
railway logs --filter "duration_ms"
```

### 2. External Monitoring

Set up additional monitoring:

```bash
# Uptime monitoring
curl -f https://your-app.railway.app/health/status

# Prometheus metrics
curl https://your-app.railway.app/health/metrics

# Performance monitoring
curl -w "@curl-format.txt" https://your-app.railway.app/health
```

### 3. Alert Configuration

Configure alerts for:
- Health check failures
- High response times
- Service restarts
- Database connectivity issues

## 🎯 Railway Health Check Benefits

✅ **Automatic Monitoring**: Railway continuously monitors your app
✅ **Auto-Recovery**: Automatic restarts on health check failures  
✅ **Deployment Verification**: Ensures successful deployments
✅ **Performance Insights**: Health check duration tracking
✅ **Comprehensive Logging**: Detailed logs for debugging
✅ **Zero-Downtime**: Health checks prevent serving unhealthy instances

Your Railway project is now configured to use the comprehensive `/health` endpoint for monitoring and automatic recovery!
