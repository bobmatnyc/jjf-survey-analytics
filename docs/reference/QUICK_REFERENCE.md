# 🚀 Quick Reference Guide - JJF Survey Analytics

## 📋 Essential Commands

### Start Application
```bash
python app.py
# Access at: http://localhost:8080
# Password: survey2025!
```

### Extract & Normalize Data
```bash
# Extract from Google Sheets
python improved_extractor.py

# Normalize survey data
python survey_normalizer.py --auto
```

### Health Checks
```bash
# Full health check
python healthcheck.py

# Specific checks
python healthcheck.py --api-only
python healthcheck.py --deps-only
```

### Stop Application
```bash
# Press Ctrl+C in terminal
# Or kill process:
lsof -ti:8080 | xargs kill -9
```

## 🌐 Key URLs

### Local Development
- **Main App:** http://localhost:8080
- **Login:** http://localhost:8080/login
- **Analytics:** http://localhost:8080/surveys
- **Auto-Sync:** http://localhost:8080/sync
- **Health:** http://localhost:8080/health/dashboard
- **API Status:** http://localhost:8080/health/status

## 🔐 Authentication

### Local Development (Default)
- **Authentication:** DISABLED for easier testing
- **No password required** - Direct access to dashboard

### Enable Authentication (Production)
```bash
export REQUIRE_AUTH=true
export APP_PASSWORD=your-secure-password
```

### Change Password
```bash
export APP_PASSWORD=your-new-password
export REQUIRE_AUTH=true
```

## 📊 Database Files

### Locations
- **Raw Data:** `surveyor_data_improved.db`
- **Normalized:** `survey_normalized.db`

### Backup
```bash
cp surveyor_data_improved.db surveyor_data_improved.db.backup
cp survey_normalized.db survey_normalized.db.backup
```

## 🔧 Environment Variables

### Required
```bash
APP_PASSWORD=survey2025!
SECRET_KEY=your-secret-key
```

### Optional
```bash
PORT=8080
REQUIRE_AUTH=true
LOG_LEVEL=INFO
AUTO_SYNC_INTERVAL=300
```

## 📁 Key Files

### Main Application
- `app.py` - Local development server
- `railway_app.py` - Production server

### Data Processing
- `improved_extractor.py` - Extract from Google Sheets
- `survey_normalizer.py` - Normalize data
- `survey_analytics.py` - Analytics engine
- `auto_sync_service.py` - Auto-sync service

### Configuration
- `requirements.txt` - Python dependencies
- `Procfile` - Railway deployment
- `railway.toml` - Railway config
- `.env` - Environment variables (create this)

## 📚 Documentation

### Main Docs
- `README.md` - Main documentation
- `ARCHITECTURE.md` - System architecture
- `DEPLOYMENT_GUIDE.md` - Deployment instructions
- `PROJECT_SUMMARY.md` - Project overview

### Status & Guides
- `DEPLOYMENT_STATUS.md` - Current status
- `QUICK_REFERENCE.md` - This file
- `FINAL_IMPLEMENTATION_SUMMARY.md` - Features

## 🐛 Troubleshooting

### Port Already in Use
```bash
lsof -ti:8080 | xargs kill -9
```

### Database Not Found
```bash
python improved_extractor.py
python survey_normalizer.py --auto
```

### Import Errors
```bash
pip install -r requirements.txt --force-reinstall
```

### Missing Dependencies
```bash
pip install schedule
```

## 🚀 Railway Deployment

### Deploy
```bash
railway login
railway init
railway up
```

### Configure
```bash
# Set environment variables in Railway Dashboard
APP_PASSWORD=your-secure-password
SECRET_KEY=your-secret-key
REQUIRE_AUTH=true
```

### Initialize Data
```bash
railway run python improved_extractor.py
railway run python survey_normalizer.py --auto
```

## 📊 API Endpoints

### Status & Health
- `GET /health/status` - Health status (JSON)
- `GET /api/stats` - Dashboard stats

### Sync Management
- `GET /api/sync/status` - Sync status
- `POST /api/sync/start` - Start sync
- `POST /api/sync/stop` - Stop sync
- `POST /api/sync/force` - Force sync

## 🎯 Common Tasks

### Refresh Data
```bash
python improved_extractor.py
python survey_normalizer.py --full
```

### View Logs
```bash
# Local: Check console output
# Railway: railway logs
```

### Test Health
```bash
curl http://localhost:8080/health/status
```

### Export Data
- Visit: http://localhost:8080/surveys/analytics
- Click "Export CSV" button

## 📈 Monitoring

### Check Auto-Sync
- Visit: http://localhost:8080/sync
- View status and activity logs

### Check Health
- Visit: http://localhost:8080/health/dashboard
- Review all system components

### View Analytics
- Visit: http://localhost:8080/surveys
- Explore response patterns

## 🔄 Development Workflow

### 1. Setup
```bash
pip install -r requirements.txt
python improved_extractor.py
python survey_normalizer.py --auto
```

### 2. Develop
```bash
python app.py
# Make changes
# App auto-reloads in debug mode
```

### 3. Test
```bash
python healthcheck.py
# Visit http://localhost:8080
# Test all features
```

### 4. Deploy
```bash
git add .
git commit -m "Your changes"
git push origin main
# Railway auto-deploys
```

## 💡 Tips

### Performance
- Auto-sync runs every 5 minutes
- Adjust via `AUTO_SYNC_INTERVAL`
- Monitor health dashboard

### Security
- Change default password
- Use strong SECRET_KEY
- Enable HTTPS in production

### Data
- Backup databases regularly
- Monitor database size
- Review sync logs

## 📞 Quick Help

### Issue: Can't login
- Check password: `survey2025!`
- Or disable auth: `export REQUIRE_AUTH=false`

### Issue: No data showing
- Run: `python improved_extractor.py`
- Then: `python survey_normalizer.py --auto`

### Issue: Port conflict
- Change port: `export PORT=8080`
- Or kill process: `lsof -ti:8080 | xargs kill -9`

### Issue: Health checks failing
- Install deps: `pip install -r requirements.txt`
- Check: `python healthcheck.py`

---

**For detailed information, see [README.md](README.md)**

