# 🚂 Railway Deployment Guide - Step by Step

**Date:** 2025-10-03  
**Project:** JJF Survey Analytics Platform

## 📋 Pre-Deployment Checklist

### ✅ Files Ready for Deployment
- [x] `app.py` - Main application
- [x] `requirements.txt` - All dependencies listed
- [x] `Procfile` - Railway process configuration
- [x] `railway.toml` - Railway deployment settings
- [x] `runtime.txt` - Python version (3.9.18)
- [x] `.gitignore` - Excludes databases and sensitive files
- [x] `templates/` - All HTML templates
- [x] `healthcheck/` - Health check system

### ✅ Code Changes Verified Locally
- [x] Empty row validation working
- [x] Summary view displaying correctly
- [x] Latest updates filtered properly
- [x] Organization counts accurate
- [x] All routes accessible
- [x] No authentication required (for testing)

## 🚀 Deployment Steps

### Step 1: Commit and Push to Git

```bash
# Check current status
git status

# Add all changes
git add .

# Commit with descriptive message
git commit -m "Add empty row validation and summary view with org counts"

# Push to main branch
git push origin main
```

### Step 2: Railway Project Setup

#### Option A: Using Railway Dashboard (Recommended)

1. **Go to Railway Dashboard**
   - Visit: https://railway.app
   - Login to your account

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository: `jjf-survey-analytics`
   - Railway will auto-detect Python and start building

#### Option B: Using Railway CLI

```bash
# Install Railway CLI (if not already installed)
npm install -g @railway/cli

# Login to Railway
railway login

# Link to existing project or create new
railway link

# Deploy
railway up
```

### Step 3: Configure Environment Variables

In Railway Dashboard → Your Project → Variables, add:

```bash
# Required Variables
REQUIRE_AUTH=false
SECRET_KEY=<generate-random-key>

# Optional Variables (with defaults)
PORT=8080
LOG_LEVEL=INFO
RAILWAY_ENVIRONMENT=production
PYTHONUNBUFFERED=1
```

**Generate SECRET_KEY:**
```python
import secrets
print(secrets.token_hex(32))
```

### Step 4: Add PostgreSQL Database (Optional)

1. In Railway Dashboard, click "New"
2. Select "Database" → "PostgreSQL"
3. Railway automatically:
   - Provisions PostgreSQL instance
   - Sets `DATABASE_URL` environment variable
   - Links to your application

**Note:** The app works with SQLite by default, PostgreSQL is optional for production.

### Step 5: Monitor Deployment

1. **Watch Build Logs**
   - Railway Dashboard → Deployments → View Logs
   - Look for successful build messages

2. **Check Health Endpoint**
   - Once deployed, visit: `https://your-app.railway.app/health/status`
   - Should return JSON with health status

3. **Verify Application**
   - Visit: `https://your-app.railway.app`
   - Should load dashboard without login (auth disabled)

### Step 6: Initialize Data (First Deployment Only)

After successful deployment, populate the database:

```bash
# Option A: Via Railway CLI
railway run python improved_extractor.py
railway run python survey_normalizer.py --auto

# Option B: Via Railway Shell
railway shell
python improved_extractor.py
python survey_normalizer.py --auto
exit
```

## 🔍 Verification Steps

### 1. Check Deployment Status

```bash
# Via Railway CLI
railway status

# Via Railway Dashboard
# Go to Deployments tab, check latest deployment
```

### 2. Test Health Endpoint

```bash
# Check health status
curl https://your-app.railway.app/health/status

# Expected response:
{
  "status": "healthy",
  "timestamp": "2025-10-03T13:00:00Z",
  "components": {
    "database": "healthy",
    "survey_database": "healthy"
  }
}
```

### 3. Test Main Dashboard

```bash
# Open in browser
open https://your-app.railway.app

# Or use curl
curl -I https://your-app.railway.app
# Should return: HTTP/1.1 200 OK
```

### 4. Verify Features

Visit these URLs to verify all features work:

- **Dashboard:** `https://your-app.railway.app/`
- **Spreadsheets:** `https://your-app.railway.app/spreadsheets`
- **Survey Analytics:** `https://your-app.railway.app/surveys`
- **Auto-Sync:** `https://your-app.railway.app/sync`
- **Health Dashboard:** `https://your-app.railway.app/health/dashboard`

### 5. Check Logs

```bash
# Via Railway CLI
railway logs

# Follow logs in real-time
railway logs --follow

# Via Railway Dashboard
# Go to Deployments → View Logs
```

## 🐛 Troubleshooting

### Build Failures

**Issue:** Build fails during deployment

**Solutions:**
```bash
# Check requirements.txt syntax
cat requirements.txt

# Verify Python version
cat runtime.txt

# Check Procfile
cat Procfile

# Review build logs in Railway Dashboard
```

### Application Won't Start

**Issue:** Deployment succeeds but app doesn't start

**Check:**
1. Environment variables are set correctly
2. PORT variable is not hardcoded
3. Procfile uses correct command
4. Check application logs for errors

**Fix:**
```bash
# View logs
railway logs

# Check environment variables
railway variables

# Restart deployment
railway up --detach
```

### Health Check Failures

**Issue:** Railway shows "Unhealthy" status

**Check:**
```bash
# Test health endpoint manually
curl https://your-app.railway.app/health/status

# Check if path is correct in railway.toml
cat railway.toml | grep healthcheckPath

# Verify health endpoint in app
curl https://your-app.railway.app/health
```

**Fix:**
Update `railway.toml` if needed:
```toml
[deploy]
healthcheckPath = "/health/status"
healthcheckTimeout = 60
```

### Database Connection Issues

**Issue:** Can't connect to database

**Check:**
```bash
# Verify DATABASE_URL is set
railway variables | grep DATABASE_URL

# Check database service is running
# In Railway Dashboard → Database → Status
```

**Fix:**
- Ensure PostgreSQL service is running
- Verify DATABASE_URL format
- Check app.py database connection logic

### Empty Dashboard

**Issue:** Dashboard loads but shows no data

**Solution:**
```bash
# Initialize data
railway run python improved_extractor.py
railway run python survey_normalizer.py --auto

# Verify data was created
railway run python -c "import sqlite3; conn = sqlite3.connect('surveyor_data_improved.db'); print(conn.execute('SELECT COUNT(*) FROM raw_data').fetchone())"
```

## 📊 Expected Results

### Successful Deployment

**Build Output:**
```
✓ Building...
✓ Installing dependencies from requirements.txt
✓ Collecting Flask>=2.3.0
✓ Successfully installed Flask-2.3.0 gunicorn-21.2.0 ...
✓ Build completed successfully
```

**Deployment Output:**
```
✓ Deploying...
✓ Health check passed
✓ Deployment successful
✓ Available at: https://your-app.railway.app
```

### Dashboard Features Working

- ✅ Recent Activity Summary showing spreadsheet groups
- ✅ Organization counts displayed
- ✅ Latest Individual Responses filtered (no empty rows)
- ✅ Spreadsheet cards with direct links
- ✅ All navigation links working

## 🔐 Security Notes

### For Testing (Current Setup)
- `REQUIRE_AUTH=false` - No password required
- Good for initial testing and verification
- **Not recommended for production with sensitive data**

### For Production (Recommended)
```bash
# Set these environment variables in Railway:
REQUIRE_AUTH=true
APP_PASSWORD=<strong-unique-password>
SECRET_KEY=<random-secret-key>
```

## 📝 Post-Deployment Tasks

### 1. Test All Features
- [ ] Dashboard loads
- [ ] Summary view shows correct counts
- [ ] Organization lists display
- [ ] Individual responses show user context
- [ ] Spreadsheet links work
- [ ] Auto-sync dashboard accessible
- [ ] Health checks pass

### 2. Monitor Performance
- [ ] Check response times
- [ ] Monitor memory usage
- [ ] Review error logs
- [ ] Verify auto-sync runs

### 3. Document Deployment
- [ ] Note Railway app URL
- [ ] Save environment variable values (securely)
- [ ] Document any custom configurations
- [ ] Update team on deployment status

## 🎯 Quick Commands Reference

```bash
# Deploy to Railway
git push origin main

# View logs
railway logs --follow

# Check status
railway status

# Run commands on Railway
railway run <command>

# Open Railway shell
railway shell

# Open app in browser
railway open

# View environment variables
railway variables

# Restart deployment
railway up --detach
```

## 📞 Support Resources

- **Railway Docs:** https://docs.railway.app
- **Railway Discord:** https://discord.gg/railway
- **Project Docs:** See README.md, ARCHITECTURE.md
- **Health Check:** `/health/dashboard` on your deployed app

---

## ✅ Deployment Checklist

Before deploying:
- [ ] All code committed to git
- [ ] Changes pushed to main branch
- [ ] Environment variables documented
- [ ] .gitignore excludes sensitive files
- [ ] requirements.txt is complete
- [ ] Procfile is correct
- [ ] railway.toml is configured

After deploying:
- [ ] Build succeeded
- [ ] Health check passes
- [ ] Dashboard loads
- [ ] All features work
- [ ] Data initialized (if first deployment)
- [ ] Logs reviewed for errors
- [ ] Performance acceptable

---

**Ready to deploy!** Follow the steps above and verify each checkpoint.

