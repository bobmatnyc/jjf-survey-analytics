# CLAUDE.md - AI Agent Instructions

**Project:** JJF Survey Analytics Platform
**Last Updated:** 2025-10-09
**Version:** 1.0.0

> This file provides comprehensive instructions for Claude Code and other AI agents working on this project. All operations follow the "ONE way to do ANYTHING" principle.

---

## Quick Links

- [README.md](README.md) - Project overview and user guide
- [DEVELOPER.md](DEVELOPER.md) - Technical architecture and API docs
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture details
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Deployment procedures
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Common commands

---

## Project Overview

**JJF Survey Analytics Platform** is a comprehensive survey data management and analytics platform that:
- Extracts survey data from Google Sheets
- Normalizes data into a relational database
- Provides real-time analytics dashboards
- Automatically synchronizes with data sources
- Deploys to Railway with PostgreSQL support

**Tech Stack:**
- **Backend:** Python 3.13, Flask 2.3+, SQLAlchemy 2.0+
- **Database:** SQLite (local), PostgreSQL (production)
- **Frontend:** Tailwind CSS, vanilla JavaScript
- **Deployment:** Railway with gunicorn
- **APIs:** Google Sheets API v4

---

## 🔴 CRITICAL - Essential Commands

### Start Local Development Server
```bash
python app.py
```
- **URL:** http://localhost:8080
- **Auth:** Disabled by default (set `REQUIRE_AUTH=true` to enable)
- **Auto-reload:** Enabled in development mode

### Extract Data from Google Sheets
```bash
python improved_extractor.py
```
- Creates/updates `surveyor_data_improved.db`
- Extracts from 6 predefined JJF Technology Assessment spreadsheets

### Normalize Survey Data
```bash
python survey_normalizer.py --auto
```
- Processes raw data into `survey_normalized.db`
- Creates relational structure with proper typing

### Run All Tests
```bash
make test
```
- Executes pytest test suite
- Coverage reports in `htmlcov/`

---

## 🟡 IMPORTANT - Common Operations

### Development Setup
```bash
# Create virtual environment
python -m venv venv

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Database Operations
```bash
# Initialize database
python main.py init-db

# Check extraction status
python main.py status

# Extract with verbose logging
python main.py --verbose extract --use-default-urls
```

### Health Checks
```bash
# Run all health checks
python healthcheck.py

# API validation only
python healthcheck.py --api-only

# Dependencies check only
python healthcheck.py --deps-only
```

### Code Quality
```bash
# Run linting
make lint

# Format code
make format

# Run tests with coverage
make test-cov
```

---

## 🟢 STANDARD - Additional Workflows

### Clean Up Environment
```bash
make clean
```
- Removes `__pycache__`, `.pyc` files
- Cleans build artifacts and coverage reports

### View Application Logs
```bash
# Local development
tail -f app.log

# Railway deployment
railway logs
```

### Manual Data Sync
Visit http://localhost:8080/sync and click "Force Sync Now"

---

## ⚪ OPTIONAL - Advanced Operations

### Railway Deployment (Use with Caution)
```bash
# The definitive deployment is managed by Railway's GitHub integration
# Manual deployments are NOT recommended

# If you must deploy manually:
railway up  # Only if railway CLI is configured
```

**PREFERRED METHOD:** Push to GitHub, Railway auto-deploys from master branch

### Custom CLI Commands
```bash
# Using the surveyor CLI tool
surveyor extract --use-default-urls
surveyor status
```

---

## 🏗️ Project Architecture

### Directory Structure
```
jjf-survey-analytics/
├── app.py                      # 🔴 Main Flask application
├── railway_app.py              # Railway-specific deployment
├── survey_analytics.py         # Analytics engine
├── survey_normalizer.py        # 🔴 Data normalization
├── improved_extractor.py       # 🔴 Google Sheets extractor
├── auto_sync_service.py        # Background sync service
├── healthcheck.py              # Health monitoring
│
├── healthcheck/                # Health check modules
│   ├── api_validators.py
│   ├── dependency_checker.py
│   ├── e2e_tests.py
│   └── monitoring.py
│
├── templates/                  # 🟡 Jinja2 HTML templates
│   ├── base.html              # Base template with nav
│   ├── dashboard.html         # Main dashboard
│   ├── survey_analytics.html  # Analytics view
│   ├── survey_responses.html  # Response activity
│   ├── sync_dashboard.html    # Auto-sync management
│   └── health_dashboard.html  # Health monitoring
│
├── src/surveyor/              # 🟢 Core library (optional)
│   ├── cli/                   # CLI commands
│   ├── config/                # Configuration
│   ├── models/                # Data models
│   ├── repositories/          # Data access
│   ├── services/              # Business logic
│   └── utils/                 # Utilities
│
├── hybrid_surveyor/           # ⚪ Advanced CLI tool (separate package)
├── tests/                     # Test suite
│   ├── unit/
│   └── integration/
│
├── docs/                      # Documentation
│   ├── PROGRESS.md
│   └── work-logs/
│
├── surveyor_data_improved.db  # 🔴 Raw spreadsheet data
├── survey_normalized.db       # 🔴 Normalized survey data
│
├── requirements.txt           # 🔴 Python dependencies
├── pyproject.toml            # Project configuration
├── Makefile                  # 🟡 Development commands
├── Procfile                  # 🔴 Railway startup
└── railway.toml              # Railway configuration
```

### Key Files Priority
- 🔴 **CRITICAL:** Required for core functionality
- 🟡 **IMPORTANT:** Needed for development workflow
- 🟢 **STANDARD:** Optional but recommended
- ⚪ **OPTIONAL:** Advanced features

---

## 🗄️ Database Schema

### Raw Data Database (`surveyor_data_improved.db`)
```
spreadsheets
├── id (PRIMARY KEY)
├── spreadsheet_id
├── title
├── type (Survey/Assessment/Inventory)
└── last_synced

raw_data
├── id (PRIMARY KEY)
├── spreadsheet_id (FOREIGN KEY)
├── sheet_name
├── data (JSON)
└── extracted_at

extraction_jobs
├── id (PRIMARY KEY)
├── status
├── started_at
└── completed_at
```

### Normalized Survey Database (`survey_normalized.db`)
```
surveys
├── id (PRIMARY KEY)
├── name
├── type
└── created_at

survey_questions
├── id (PRIMARY KEY)
├── survey_id (FOREIGN KEY)
├── question_text
├── question_type
└── order_index

survey_responses
├── id (PRIMARY KEY)
├── survey_id (FOREIGN KEY)
├── respondent_id (FOREIGN KEY)
├── submitted_at
└── raw_data (JSON)

survey_answers
├── id (PRIMARY KEY)
├── response_id (FOREIGN KEY)
├── question_id (FOREIGN KEY)
├── answer_value
├── answer_type
└── parsed_value

respondents
├── id (PRIMARY KEY)
├── email
├── name
└── organization

sync_tracking
├── id (PRIMARY KEY)
├── last_sync
├── records_synced
└── status

normalization_jobs
├── id (PRIMARY KEY)
├── status
├── started_at
└── completed_at
```

---

## 🔒 Data Architecture: Single Source of Truth

### Google Sheets as Single Source of Truth

**CRITICAL PRINCIPLE:** Google Sheets are the ONLY authoritative data source. All databases are disposable caches.

#### Architecture Rules

1. ✅ **Google Sheets → Databases** (One-way data flow)
2. ❌ **Databases → Google Sheets** (NO reverse flow)
3. ✅ **Databases can be deleted safely** (Data lives in Google Sheets)
4. ✅ **Databases regenerate automatically** (From Google Sheets)

#### Data Flow Architecture

```
Google Sheets (SINGLE SOURCE OF TRUTH)
        ↓ READ-ONLY
improved_extractor.py (Extract)
        ↓
Raw Database (DISPOSABLE CACHE)
├─ SQLite: surveyor_data_improved.db (local)
└─ PostgreSQL: Raw tables (production)
        ↓
survey_normalizer.py (Normalize)
        ↓
Normalized Database (DISPOSABLE CACHE)
├─ SQLite: survey_normalized.db (local)
└─ PostgreSQL: Normalized tables (production)
        ↓
Flask Application (app.py)
        ↓
User Interface (READ-ONLY)
```

#### Database Regeneration

**Local Development (SQLite):**
```bash
# Safe to delete - data lives in Google Sheets
rm surveyor_data_improved.db survey_normalized.db

# Regenerate from Google Sheets (takes ~60 seconds)
python improved_extractor.py
python survey_normalizer.py --auto
```

**Production (PostgreSQL on Railway):**
- **Automatic:** Railway deployment regenerates PostgreSQL from Google Sheets on startup
- **Manual:** Restart Railway service to force full regeneration
- **Emergency:** Delete PostgreSQL database - will regenerate on next deployment

#### Database Environment Detection

The system automatically detects the environment:

- **`DATABASE_URL` NOT set** → SQLite mode (local development)
  - Creates `.db` files in project directory
  - Suitable for development and testing

- **`DATABASE_URL` IS set** → PostgreSQL mode (production)
  - Connects to PostgreSQL via DATABASE_URL
  - Railway automatically sets this variable
  - No `.db` files created

#### SOT Compliance Guarantees

✅ **Zero write operations to Google Sheets** - All code is read-only
✅ **Databases are gitignored** - Not version controlled
✅ **Full refresh on sync** - Not incremental updates
✅ **Automatic regeneration** - Railway startup extracts from Sheets
✅ **Manual regeneration** - Run extractor anytime

#### What This Means for Development

**You CAN safely:**
- Delete any database file (`.db` or PostgreSQL)
- Modify database schema without migrations
- Experiment with database structure locally
- Reset to clean state anytime

**You CANNOT:**
- Modify survey data without updating Google Sheets
- Create "admin" features that edit database directly
- Trust database as authoritative source
- Rely on database data persisting across deployments

#### Troubleshooting Data Issues

**Problem:** Production data looks wrong
**Solution:** Restart Railway service to regenerate from Google Sheets

**Problem:** Local database is corrupted
**Solution:** `rm *.db && python improved_extractor.py && python survey_normalizer.py --auto`

**Problem:** Changes in Google Sheets not showing
**Solution:** Wait for auto-sync (5 minutes) or force sync via `/sync` dashboard

---

## 🌐 API Endpoints

### Web Routes (User Interface)
```
GET  /                        # Main dashboard
GET  /login                   # Authentication page
GET  /logout                  # Logout
GET  /spreadsheets            # Spreadsheets listing
GET  /spreadsheet/<id>        # Individual spreadsheet view
GET  /jobs                    # Extraction jobs history
GET  /surveys                 # Survey analytics dashboard
GET  /surveys/analytics       # Detailed question analysis
GET  /surveys/responses       # Response activity monitor
GET  /sync                    # Auto-sync management dashboard
GET  /health/dashboard        # Health check dashboard
GET  /health/test             # Run health checks
```

### API Routes (JSON)
```
GET  /api/stats                    # Dashboard statistics
GET  /api/spreadsheet/<id>/data    # Spreadsheet data
GET  /api/sync/status              # Auto-sync service status
POST /api/sync/start               # Start auto-sync service
POST /api/sync/stop                # Stop auto-sync service
POST /api/sync/force               # Force immediate sync
GET  /api/survey/search            # Search survey responses
GET  /api/survey/<id>/export       # Export survey data (CSV)
GET  /health/status                # Health check status
POST /health/check                 # Run specific health checks
```

---

## 🔧 Configuration

### Environment Variables
```bash
# Application
PORT=8080                           # Server port (Railway sets this)
SECRET_KEY=your-secret-key          # Flask secret key

# Authentication
REQUIRE_AUTH=false                  # Enable/disable auth (true in production)
APP_PASSWORD=survey2025!            # App password when auth enabled

# Database
DATABASE_URL=postgresql://...       # PostgreSQL URL (Railway provides this)

# Logging
LOG_LEVEL=INFO                      # Logging verbosity

# Auto-Sync
AUTO_SYNC_INTERVAL=300              # Sync interval in seconds (5 minutes)

# Google Sheets API
GOOGLE_API_KEY=your-key             # Optional for API key auth
```

### Local Development Configuration
Create `.env` file in project root:
```env
PORT=8080
SECRET_KEY=dev-secret-key-change-in-production
REQUIRE_AUTH=false
APP_PASSWORD=survey2025!
LOG_LEVEL=DEBUG
AUTO_SYNC_INTERVAL=300
```

---

## 🚀 Deployment

### ONE Way to Deploy: Railway GitHub Integration

**DO NOT use manual deployment scripts.** Railway automatically deploys from GitHub.

**Deployment Workflow:**
1. Make changes locally
2. Commit to git: `git commit -m "Description"`
3. Push to GitHub: `git push origin master`
4. Railway automatically builds and deploys
5. Monitor at Railway dashboard

**Health Check:** Railway uses `/health` endpoint (configured in `railway.toml`)

**Database:** Railway automatically provisions PostgreSQL and sets `DATABASE_URL`

**See:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions

---

## 🧪 Testing

### Test Structure
```
tests/
├── unit/              # Unit tests
├── integration/       # Integration tests
└── __init__.py
```

### Run Tests
```bash
# All tests
make test

# With coverage report
make test-cov

# Specific test file
python -m pytest tests/unit/test_basic.py -v

# Integration tests only
python -m pytest tests/integration/ -v
```

### Test Coverage Goals
- **Unit Tests:** 80%+ coverage
- **Integration Tests:** Critical paths covered
- **E2E Tests:** Main user workflows validated

---

## 📊 Data Flow

```
Google Sheets (Source)
    ↓
improved_extractor.py (Extract)
    ↓
surveyor_data_improved.db (Raw Data)
    ↓
survey_normalizer.py (Normalize)
    ↓
survey_normalized.db (Relational)
    ↓
app.py (Flask Application)
    ↓
Templates (Jinja2)
    ↓
User Browser (Dashboards)
```

---

## 🔍 Troubleshooting

### Database Not Found
```bash
# Solution: Run extractor and normalizer
python improved_extractor.py
python survey_normalizer.py --auto
```

### Port Already in Use
```bash
# Find process using port 8080
lsof -ti:8080

# Kill process
lsof -ti:8080 | xargs kill -9

# Or change port
export PORT=8081
python app.py
```

### Authentication Issues
```bash
# Disable auth for local development
export REQUIRE_AUTH=false

# Or set password
export APP_PASSWORD=your-password
```

### Google Sheets Access Denied
- Verify sheets are publicly accessible
- Check internet connection
- Validate URLs in extractor configuration

### Auto-Sync Not Working
- Check `/sync` dashboard
- Verify service is started
- Review logs for errors
- Ensure source data has changed

### Health Checks Failing
```bash
# Run manual health check
python healthcheck.py

# Check specific components
python healthcheck.py --api-only
python healthcheck.py --deps-only
```

---

## 🎯 Current Project Status

### Production Statistics (As of 2025-10-03)
- **22 survey responses** processed across 5 surveys
- **240 questions** normalized with proper typing
- **585 answers** analyzed with statistical insights
- **13 unique respondents** tracked
- **6 Google Sheets** sources (2 Surveys, 3 Assessments, 1 Inventory)

### Recent Updates (Last 30 Days)
- ✅ **PostgreSQL Schema Migration** - Full compatibility with Railway production database
- ✅ **Single Source of Truth Architecture** - Auto-regenerating PostgreSQL from Google Sheets
- ✅ **Sync Tracking Improvements** - Fixed INSERT OR REPLACE conversion for PostgreSQL
- ✅ **UI Terminology Standardization** - Unified 'submission' terminology across interface
- ✅ **Comprehensive Documentation** - Added development guides and deployment docs
- ✅ **Enhanced Makefile** - Complete command system with shortcuts
- ✅ **Security Documentation** - Added v1.0.1 security debt tracking

### Deployment Status
- ✅ **Railway Production:** Live and auto-deploying from GitHub
- ✅ **PostgreSQL:** Database provisioned and connected
- ✅ **Health Checks:** Active monitoring at `/health`
- ✅ **Authentication:** Configurable (disabled for local dev)

---

## 📝 Development Guidelines

### Code Style
- **Python:** PEP 8 compliant, use Black formatter (line length 100)
- **Type Hints:** Use type hints for all function signatures
- **Docstrings:** Required for public functions and classes
- **Imports:** Organize with isort (stdlib, third-party, local)

### Git Workflow
```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: Add your feature description"

# Push to GitHub
git push origin feature/your-feature-name

# Create pull request on GitHub
# After review, merge to master
# Railway auto-deploys from master
```

### Commit Message Convention
```
feat: Add new feature
fix: Fix bug
docs: Update documentation
style: Format code
refactor: Refactor code structure
test: Add tests
chore: Update dependencies
```

---

## 🧠 Memory System

This project uses Claude MPM (Memory and Project Management) for knowledge retention.

**Memories Location:** `.claude-mpm/memories/`

**Update Memories When:**
- Learning new project patterns
- Discovering architecture decisions
- Identifying important workflows
- Solving complex bugs

**Memory Format:**
```json
{
  "memory-update": {
    "Project Architecture": ["Key architectural insight"],
    "Implementation Guidelines": ["Important coding practice"],
    "Current Technical Context": ["Project-specific detail"]
  }
}
```

---

## ⚠️ Important Warnings

### DO NOT
- ❌ **Manual Railway Deployments** - Use GitHub integration only
- ❌ **Commit Secrets** - Never commit `.env` files or API keys
- ❌ **Modify Production DB Directly** - Use migration scripts
- ❌ **Skip Tests** - Always run tests before pushing
- ❌ **Use Multiple Deployment Scripts** - One method: GitHub → Railway

### DO
- ✅ **Use Virtual Environment** - Isolate dependencies
- ✅ **Run Health Checks** - Before and after changes
- ✅ **Update Documentation** - Keep docs synchronized
- ✅ **Test Locally First** - Verify changes before push
- ✅ **Follow Git Workflow** - Branch, commit, push, PR

---

## 📚 Additional Documentation

### Primary Documentation
- [README.md](README.md) - Comprehensive project overview
- [DEVELOPER.md](DEVELOPER.md) - Technical architecture and development guide
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design and architecture
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Deployment procedures
- [SOT_ARCHITECTURE.md](SOT_ARCHITECTURE.md) - Single Source of Truth architecture

### Feature Documentation
- [AUTO_SYNC_IMPLEMENTATION.md](AUTO_SYNC_IMPLEMENTATION.md) - Auto-sync service details
- [AUTHENTICATION_CONFIG.md](AUTHENTICATION_CONFIG.md) - Authentication setup
- [HEALTHCHECK_README.md](HEALTHCHECK_README.md) - Health check system

### Operational Documentation
- [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) - Railway deployment guide
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Common commands reference
- [DASHBOARD_IMPROVEMENTS.md](DASHBOARD_IMPROVEMENTS.md) - Dashboard feature history

### Status Documentation
- [SIMPLIFIED_DASHBOARD.md](SIMPLIFIED_DASHBOARD.md) - Recent dashboard changes
- [ANONYMOUS_ROW_FILTERING.md](ANONYMOUS_ROW_FILTERING.md) - Row filtering implementation
- [EMPTY_ROW_VALIDATION.md](EMPTY_ROW_VALIDATION.md) - Validation logic
- [LOCAL_SITE_RUNNING.md](LOCAL_SITE_RUNNING.md) - Local development status

---

## 🎓 Learning Resources

### Flask Documentation
- https://flask.palletsprojects.com/
- Template rendering, routing, sessions

### SQLAlchemy
- https://www.sqlalchemy.org/
- ORM patterns, migrations

### Google Sheets API
- https://developers.google.com/sheets/api
- Authentication, data extraction

### Railway Platform
- https://railway.app/docs
- Deployment, environment variables, databases

---

## 🆘 Getting Help

### Health Check First
```bash
python healthcheck.py
```

### Check Logs
```bash
# Local
tail -f app.log

# Railway
railway logs --tail
```

### Common Issues
See [Troubleshooting](#-troubleshooting) section above

### Additional Resources
1. Check relevant documentation in [Additional Documentation](#-additional-documentation)
2. Review [Recent Updates](#recent-updates) for latest changes
3. Examine git commit history for context
4. Run health checks for system status

---

## 📞 Support

**For issues or questions:**
1. Check [Troubleshooting](#-troubleshooting) section
2. Review [Additional Documentation](#-additional-documentation)
3. Run health checks: `python healthcheck.py`
4. Check application logs for detailed error messages
5. Review recent git commits for related changes

---

**Built with Python, Flask, SQLite/PostgreSQL, and Tailwind CSS**
**Optimized for Claude Code and agentic coders**

---

## 📈 Recent Activity Summary (Last 30 Days)

### Development Statistics
- **82 commits** by Robert (Masa) Matsuoka
- **Primary focus:** PostgreSQL migration and production stability
- **Most modified file:** app.py (56 changes)
- **Active branch:** master (stable)

### Key Development Areas

#### Database Migration (Oct 6-7)
- Fixed PostgreSQL schema compatibility for survey normalization
- Improved INSERT OR REPLACE conversion for sync_tracking table
- Ensured sync_tracking table creation on PostgreSQL startup
- Migrated from SQLite to PostgreSQL with full schema parity

#### Architecture Improvements (Oct 6)
- Implemented single source of truth architecture with auto-regenerating PostgreSQL
- Added API endpoints for SQLite to PostgreSQL migration
- Updated schema to match SQLite normalized structure exactly
- Created database verification and recreation endpoints

#### Documentation Enhancements (Oct 6)
- Added comprehensive development guides and deployment documentation
- Created security debt documentation for v1.0.1
- Enhanced Makefile with comprehensive command system
- Removed obsolete deployment documentation

#### User Experience (Oct 6)
- Standardized UI terminology from 'response' to 'submission'
- Fixed cache headers and PostgreSQL route detection
- Improved survey data verification endpoints

### Technical Debt Addressed
- ✅ PostgreSQL boolean casting and foreign key handling
- ✅ SQLite datetime() to PostgreSQL conditional query conversion
- ✅ RealDictCursor dictionary access compatibility
- ✅ Schema synchronization between local and production environments

### Files with Significant Updates
1. **app.py** - Core application logic (56 modifications)
2. **templates/dashboard.html** - UI improvements (6 modifications)
3. **survey_analytics.py** - Analytics engine updates (5 modifications)
4. **railway_init.py** - Production initialization (4 modifications)
5. **survey_normalizer.py** - Schema compatibility fixes (3 modifications)

### Next Focus Areas
- Continue monitoring PostgreSQL production stability
- Enhance health check coverage for database migrations
- Improve error handling for edge cases
- Expand test coverage for PostgreSQL-specific logic

---

*Last updated: 2025-10-09*
*CLAUDE.md Version: 1.0.0*
