# 🚀 Deployment Guide - JJF Survey Analytics

## 📋 Table of Contents
- [Local Development Deployment](#local-development-deployment)
- [Railway Production Deployment](#railway-production-deployment)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Troubleshooting](#troubleshooting)

## Local Development Deployment

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Git (for version control)
- Internet connection (for Google Sheets access)

### Step 1: Clone Repository
```bash
git clone <repository-url>
cd jjf-survey-analytics
```

### Step 2: Set Up Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
# Install all required packages
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Create a `.env` file in the project root:

```bash
# Application Configuration
PORT=5001
SECRET_KEY=your-secret-key-change-this-in-production

# Authentication
REQUIRE_AUTH=true
APP_PASSWORD=survey2025!

# Logging
LOG_LEVEL=INFO

# Auto-Sync Configuration
AUTO_SYNC_INTERVAL=300
```

### Step 5: Extract Initial Data
```bash
# Extract data from Google Sheets
python improved_extractor.py

# This will create: surveyor_data_improved.db
```

### Step 6: Normalize Survey Data
```bash
# Normalize the extracted data
python survey_normalizer.py --auto

# This will create: survey_normalized.db
```

### Step 7: Run Health Checks (Optional)
```bash
# Verify system health
python healthcheck.py

# Or run specific checks
python healthcheck.py --api-only
python healthcheck.py --deps-only
```

### Step 8: Start the Application
```bash
# Start the Flask web server
python app.py

# The application will be available at:
# http://localhost:5001
```

### Step 9: Access the Application
1. Open your browser to `http://localhost:5001`
2. Login with password: `survey2025!` (or your configured password)
3. Explore the dashboards:
   - Main Dashboard: `/`
   - Survey Analytics: `/surveys`
   - Auto-Sync: `/sync`
   - Health Checks: `/health/dashboard`

### Development Workflow

#### Using Make Commands
```bash
# Set up development environment
make setup

# Install dependencies
make install

# Run tests
make test

# Run with coverage
make test-cov

# Format code
make format

# Lint code
make lint

# Clean up
make clean
```

#### Manual Data Refresh
```bash
# Re-extract data from Google Sheets
python improved_extractor.py

# Re-normalize data
python survey_normalizer.py --full

# Or use auto mode for incremental updates
python survey_normalizer.py --auto
```

#### Enable Auto-Sync
```bash
# Start auto-sync service (checks every 5 minutes)
python auto_sync_service.py 300

# Or configure via web interface at /sync
```

## Railway Production Deployment

### Prerequisites
- Railway account (https://railway.app)
- GitHub repository with your code
- Railway CLI (optional, for command-line deployment)

### Step 1: Prepare Your Repository

Ensure these files are in your repository:
- `requirements.txt` - Python dependencies
- `Procfile` - Railway process configuration
- `railway.toml` - Railway deployment configuration
- `runtime.txt` - Python version specification

**Procfile:**
```
web: gunicorn railway_app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

**railway.toml:**
```toml
[build]
builder = "nixpacks"

[deploy]
healthcheckPath = "/health/status"
healthcheckTimeout = 30
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3
```

**runtime.txt:**
```
python-3.13
```

### Step 2: Create Railway Project

#### Option A: Via Railway Dashboard
1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Railway will auto-detect Python and start building

#### Option B: Via Railway CLI
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init

# Link to your project
railway link

# Deploy
railway up
```

### Step 3: Configure Environment Variables

In Railway Dashboard → Variables, add:

```bash
# Required Variables
APP_PASSWORD=your-secure-production-password
SECRET_KEY=your-long-random-secret-key-here
REQUIRE_AUTH=true

# Optional Variables
LOG_LEVEL=INFO
AUTO_SYNC_INTERVAL=300
RAILWAY_ENVIRONMENT=production
```

**Generate a secure SECRET_KEY:**
```python
import secrets
print(secrets.token_hex(32))
```

### Step 4: Add PostgreSQL Database

1. In Railway Dashboard, click "New"
2. Select "Database" → "PostgreSQL"
3. Railway will automatically:
   - Provision a PostgreSQL instance
   - Set the `DATABASE_URL` environment variable
   - Link it to your application

### Step 5: Deploy

Railway will automatically deploy when you push to your main branch:

```bash
git add .
git commit -m "Deploy to Railway"
git push origin main
```

Or manually trigger deployment:
```bash
railway up
```

### Step 6: Monitor Deployment

1. Watch build logs in Railway Dashboard
2. Check deployment status
3. Verify health check endpoint: `https://your-app.railway.app/health/status`

### Step 7: Initial Data Setup

After deployment, you need to populate the database:

#### Option A: Via Railway CLI
```bash
# Connect to your Railway environment
railway run python improved_extractor.py
railway run python survey_normalizer.py --auto
```

#### Option B: Via Railway Shell
```bash
# Open Railway shell
railway shell

# Run extraction and normalization
python improved_extractor.py
python survey_normalizer.py --auto
exit
```

### Step 8: Verify Deployment

1. Access your app: `https://your-app.railway.app`
2. Login with your configured password
3. Check health dashboard: `/health/dashboard`
4. Verify data in dashboards

## Environment Configuration

### Development Environment Variables

```bash
# .env file for local development
PORT=5001
SECRET_KEY=dev-secret-key-change-in-production
APP_PASSWORD=survey2025!
REQUIRE_AUTH=true
LOG_LEVEL=DEBUG
AUTO_SYNC_INTERVAL=300
```

### Production Environment Variables

```bash
# Railway environment variables
APP_PASSWORD=<strong-password>
SECRET_KEY=<generated-secret-key>
REQUIRE_AUTH=true
LOG_LEVEL=INFO
AUTO_SYNC_INTERVAL=300
RAILWAY_ENVIRONMENT=production
DATABASE_URL=<automatically-set-by-railway>
PORT=<automatically-set-by-railway>
```

### Environment Variable Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PORT` | No | 5001 (dev), dynamic (Railway) | Application port |
| `SECRET_KEY` | Yes | - | Flask session encryption key |
| `APP_PASSWORD` | Yes | survey2025! | Application password |
| `REQUIRE_AUTH` | No | true | Enable/disable authentication |
| `LOG_LEVEL` | No | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `AUTO_SYNC_INTERVAL` | No | 300 | Auto-sync check interval (seconds) |
| `DATABASE_URL` | No | - | PostgreSQL connection string (Railway only) |
| `RAILWAY_ENVIRONMENT` | No | - | Set to 'production' on Railway |

## Database Setup

### SQLite (Development)

SQLite databases are created automatically:
- `surveyor_data_improved.db` - Raw spreadsheet data
- `survey_normalized.db` - Normalized survey data

**Location:** Project root directory

**Backup:**
```bash
# Backup databases
cp surveyor_data_improved.db surveyor_data_improved.db.backup
cp survey_normalized.db survey_normalized.db.backup
```

### PostgreSQL (Production)

Railway automatically provisions and configures PostgreSQL.

**Connection:**
```python
# Automatically handled by app
DATABASE_URL = os.getenv('DATABASE_URL')
```

**Backup:**
```bash
# Via Railway CLI
railway run pg_dump > backup.sql

# Restore
railway run psql < backup.sql
```

#### PostgreSQL as Disposable Cache

**IMPORTANT:** PostgreSQL is automatically regenerated from Google Sheets on every Railway deployment.

**Automatic Regeneration Process:**
1. Railway detects `DATABASE_URL` environment variable
2. `railway_init.py` runs on startup
3. `improved_extractor.py` extracts from Google Sheets → PostgreSQL
4. `survey_normalizer.py` normalizes data → PostgreSQL
5. Application starts with fresh data

**This means:**
- You can safely delete the PostgreSQL database
- No manual data migration needed
- Google Sheets remain authoritative source
- Auto-sync keeps data fresh (5-minute intervals)

**Manual Regeneration (if needed):**
```bash
# Trigger via Railway CLI
railway run python improved_extractor.py
railway run python survey_normalizer.py --auto

# Or restart service (automatic regeneration)
railway restart
```

**Data Sync Behavior:**
- **On Deploy:** Full extraction from Google Sheets
- **Auto-Sync:** Monitors for changes, re-normalizes
- **Manual Sync:** Via `/sync` dashboard "Force Sync" button

## Troubleshooting

### Local Deployment Issues

#### Port Already in Use
```bash
# Find and kill process using port 5001
lsof -ti:5001 | xargs kill -9

# Or use a different port
export PORT=8080
python app.py
```

#### Database Not Found
```bash
# Extract data first
python improved_extractor.py

# Then normalize
python survey_normalizer.py --auto
```

#### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Or use virtual environment
deactivate
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Railway Deployment Issues

#### Build Failures
- Check `requirements.txt` for syntax errors
- Verify Python version in `runtime.txt`
- Review build logs in Railway Dashboard

#### Health Check Failures
- Verify `/health/status` endpoint is accessible
- Check application logs for errors
- Ensure database is connected

#### Database Connection Issues
- Verify `DATABASE_URL` is set
- Check PostgreSQL service is running
- Review connection logs

#### Application Not Starting
```bash
# Check logs
railway logs

# Verify environment variables
railway variables

# Test locally with production settings
export RAILWAY_ENVIRONMENT=production
python railway_app.py
```

### Common Issues

#### Authentication Loop
```bash
# Clear browser cookies
# Or disable auth temporarily
export REQUIRE_AUTH=false
```

#### Auto-Sync Not Working
- Check `/sync` dashboard
- Verify sync service is started
- Review sync logs in database
- Ensure source data has changed

#### Missing Data
```bash
# Re-run extraction and normalization
python improved_extractor.py
python survey_normalizer.py --full
```

## Monitoring

### Health Checks
- Access `/health/dashboard` for comprehensive health status
- Monitor `/health/status` endpoint for automated checks
- Review health check logs

### Application Logs
```bash
# Local development
# Logs appear in console

# Railway production
railway logs
railway logs --follow  # Live logs
```

### Performance Monitoring
- Monitor response times in Railway Dashboard
- Check database query performance
- Review auto-sync activity logs

---

**For additional help, see:**
- [README.md](README.md) - General documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) - Railway-specific details
- [HEALTHCHECK_README.md](HEALTHCHECK_README.md) - Health check system

**Last Updated:** 2025-10-03

