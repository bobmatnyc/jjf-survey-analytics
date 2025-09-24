# Railway Deployment Guide - JJF Survey Analytics

This guide covers deploying the JJF Survey Analytics application with integrated health checks to Railway.

## 🚂 Railway Deployment Setup

### Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Repository**: Code should be in a GitHub repository
3. **Google Credentials**: Service account JSON file for Google Sheets API

### Environment Variables

Set these environment variables in Railway dashboard:

#### Required Variables
```bash
# Google Sheets API
GOOGLE_CREDENTIALS_FILE=credentials.json

# Railway automatically sets these:
# PORT=<dynamic-port>
# RAILWAY_ENVIRONMENT=production
# RAILWAY_SERVICE_NAME=<service-name>
# RAILWAY_DEPLOYMENT_ID=<deployment-id>
```

#### Optional Variables
```bash
# Database (if using external database)
DATABASE_URL=sqlite:///surveyor_data_improved.db

# Logging
LOG_LEVEL=INFO

# Health Check Configuration
HEALTH_CHECK_CACHE_DURATION=30

# Alert Configuration (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_FROM_EMAIL=alerts@yourcompany.com
ALERT_TO_EMAILS=admin@yourcompany.com
ALERT_WEBHOOK_URL=https://hooks.slack.com/services/your/webhook/url
```

### Google Credentials Setup

1. **Upload Credentials File**:
   - Add `credentials.json` to your repository root
   - **Security Note**: Ensure this file is in `.gitignore` for production
   - Alternative: Use Railway's file upload feature

2. **Environment Variable Method** (Recommended):
   ```bash
   # Set the entire JSON as an environment variable
   GOOGLE_CREDENTIALS_JSON='{"type":"service_account","project_id":"..."}'
   ```

### Railway Configuration

Create `railway.toml` in your project root:

```toml
[build]
builder = "nixpacks"

[deploy]
healthcheckPath = "/health/status"
healthcheckTimeout = 30
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3

[environments.production]
variables = { LOG_LEVEL = "INFO" }

[environments.staging]
variables = { LOG_LEVEL = "DEBUG" }
```

## 📊 Health Check Integration

### Railway Health Checks

Railway will automatically use the `/health/status` endpoint for:
- **Deployment Health**: Verify successful deployment
- **Service Monitoring**: Continuous health monitoring
- **Auto-restart**: Restart service on health check failures

### Available Health Endpoints

| Endpoint | Purpose | Railway Usage |
|----------|---------|---------------|
| `/health/status` | Quick status for load balancers | ✅ Railway health checks |
| `/health` | Complete health check | Manual monitoring |
| `/health/dashboard` | Web interface | Development/debugging |
| `/health/test` | Deployment verification | ✅ Post-deployment testing |
| `/health/metrics` | Prometheus metrics | External monitoring |

### Health Check Logging

The application logs health check results to Railway's log system:

```bash
# View logs in Railway dashboard or CLI
railway logs

# Filter health check logs
railway logs --filter "Health Check"
```

## 🔧 Deployment Process

### 1. Initial Deployment

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init

# Deploy
railway up
```

### 2. Environment Setup

```bash
# Set environment variables
railway variables set GOOGLE_CREDENTIALS_FILE=credentials.json
railway variables set LOG_LEVEL=INFO

# Upload credentials file (if not in repo)
railway files upload credentials.json
```

### 3. Verify Deployment

```bash
# Get deployment URL
railway domain

# Test health endpoints
curl https://your-app.railway.app/health/test
curl https://your-app.railway.app/health/status
```

## 📈 Monitoring & Logging

### Railway Logs

Monitor application health through Railway logs:

```bash
# Real-time logs
railway logs --follow

# Filter by log level
railway logs --filter "ERROR"
railway logs --filter "Health Check"

# Export logs
railway logs --json > deployment_logs.json
```

### Key Log Messages

Look for these log messages during deployment:

```
✅ Health check system initialized
✅ Auto-sync service started
🌐 Starting Flask server on 0.0.0.0:PORT
📊 Database found: surveyor_data_improved.db
```

### Error Troubleshooting

Common deployment issues and solutions:

#### 1. Health Check Failures
```
❌ API Health Check FAILED - Google Credentials: Credentials file not found
```
**Solution**: Verify `GOOGLE_CREDENTIALS_FILE` environment variable and file upload

#### 2. Database Issues
```
❌ Database not found: surveyor_data_improved.db
```
**Solution**: Run data extraction or upload existing database files

#### 3. Port Binding Issues
```
OSError: [Errno 98] Address already in use
```
**Solution**: Ensure app uses `PORT` environment variable (already configured)

### Health Dashboard Access

Access the health dashboard at:
```
https://your-app.railway.app/health/dashboard
```

## 🔄 Continuous Deployment

### GitHub Integration

1. **Connect Repository**: Link your GitHub repo in Railway dashboard
2. **Auto-deploy**: Enable automatic deployments on push
3. **Branch Protection**: Set up staging/production branches

### Deployment Hooks

Add deployment verification:

```bash
# In your CI/CD pipeline
curl -f https://your-app.railway.app/health/status || exit 1
```

### Health Check Monitoring

Set up external monitoring:

```bash
# Prometheus scraping
curl https://your-app.railway.app/health/metrics

# Uptime monitoring
curl -f https://your-app.railway.app/health/status
```

## 🛡️ Security Considerations

### Credentials Management

1. **Never commit credentials** to repository
2. **Use Railway environment variables** for sensitive data
3. **Rotate credentials regularly**
4. **Monitor access logs** for unauthorized access

### Health Endpoint Security

Consider restricting health endpoints in production:

```python
# Add authentication for sensitive endpoints
@app.before_request
def require_auth():
    if request.path.startswith('/health/') and request.path != '/health/status':
        # Add authentication logic
        pass
```

## 📋 Deployment Checklist

### Pre-deployment
- [ ] Google Credentials file uploaded or environment variable set
- [ ] Environment variables configured in Railway
- [ ] Database files available (if needed)
- [ ] Railway health check path configured (`/health/status`)

### Post-deployment
- [ ] Health check endpoints responding
- [ ] Application logs showing successful startup
- [ ] Database connectivity verified
- [ ] Google Sheets API authentication working
- [ ] Auto-sync service running (if applicable)

### Monitoring Setup
- [ ] Railway health checks enabled
- [ ] External monitoring configured (optional)
- [ ] Alert notifications set up (optional)
- [ ] Log aggregation configured (optional)

## 🚨 Troubleshooting

### Common Railway Issues

1. **Build Failures**
   - Check `requirements.txt` for missing dependencies
   - Verify Python version compatibility
   - Review build logs in Railway dashboard

2. **Runtime Errors**
   - Check environment variables are set correctly
   - Verify file permissions and paths
   - Review application logs

3. **Health Check Failures**
   - Test endpoints locally first
   - Check Railway health check timeout settings
   - Verify network connectivity

### Debug Commands

```bash
# Check deployment status
railway status

# View environment variables
railway variables

# Test health endpoints
curl https://your-app.railway.app/health/test
curl https://your-app.railway.app/health/status

# Check logs for errors
railway logs --filter "ERROR" --tail 100
```

## 📞 Support

### Railway Resources
- [Railway Documentation](https://docs.railway.app)
- [Railway Discord](https://discord.gg/railway)
- [Railway Status Page](https://status.railway.app)

### Health Check Resources
- Health Dashboard: `/health/dashboard`
- Test Endpoint: `/health/test`
- Complete Documentation: `HEALTHCHECK_ENDPOINTS.md`

The health check system is now fully integrated and Railway-ready with comprehensive logging and monitoring capabilities!
