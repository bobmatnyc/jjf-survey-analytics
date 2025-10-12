# DEVELOPER.md - Technical Architecture Guide

**Project:** JJF Survey Analytics Platform
**Last Updated:** 2025-10-06
**Target Audience:** Developers, Engineers, Technical Contributors

> Comprehensive technical documentation covering architecture, APIs, data models, and implementation details.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Technology Stack](#technology-stack)
3. [Project Structure](#project-structure)
4. [Data Models](#data-models)
5. [API Documentation](#api-documentation)
6. [Core Components](#core-components)
7. [Database Design](#database-design)
8. [Authentication](#authentication)
9. [Auto-Sync Service](#auto-sync-service)
10. [Health Check System](#health-check-system)
11. [Development Workflows](#development-workflows)
12. [Testing Strategy](#testing-strategy)
13. [Deployment Architecture](#deployment-architecture)
14. [Performance Considerations](#performance-considerations)
15. [Security](#security)
16. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Google Sheets API                        │
│              (6 JJF Technology Assessment Sheets)            │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/REST
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Data Extraction Layer                       │
│              (improved_extractor.py)                         │
│  • Google Sheets API v4 Integration                          │
│  • Batch data retrieval                                      │
│  • JSON serialization                                        │
└────────────────────┬────────────────────────────────────────┘
                     │ SQLite Write
                     ▼
┌─────────────────────────────────────────────────────────────┐
│               Raw Data Storage                               │
│          (surveyor_data_improved.db)                         │
│  • spreadsheets table                                        │
│  • raw_data table (JSON)                                     │
│  • extraction_jobs table                                     │
└────────────────────┬────────────────────────────────────────┘
                     │ Read
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Data Normalization Layer                        │
│            (survey_normalizer.py)                            │
│  • Type detection and parsing                                │
│  • Relational modeling                                       │
│  • Deduplication (SHA256)                                    │
└────────────────────┬────────────────────────────────────────┘
                     │ SQLite Write
                     ▼
┌─────────────────────────────────────────────────────────────┐
│            Normalized Data Storage                           │
│           (survey_normalized.db)                             │
│  • surveys, questions, responses, answers                    │
│  • respondents, sync_tracking                                │
│  • Foreign key relationships                                 │
└────────────────────┬────────────────────────────────────────┘
                     │ Read
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                Web Application Layer                         │
│                    (app.py)                                  │
│  • Flask HTTP server                                         │
│  • Jinja2 template rendering                                 │
│  • REST API endpoints                                        │
│  • Session management                                        │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/JSON
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                     Web Browser                              │
│  • Tailwind CSS UI                                           │
│  • JavaScript interactivity                                  │
│  • AJAX API calls                                            │
└─────────────────────────────────────────────────────────────┘
```

### System Components

1. **Data Extraction** - Google Sheets → SQLite
2. **Data Normalization** - Raw JSON → Relational structure
3. **Web Application** - Flask REST API + UI
4. **Auto-Sync Service** - Background change detection
5. **Health Monitoring** - System status validation
6. **Analytics Engine** - Statistical analysis

---

## Technology Stack

### Backend
- **Python 3.13** - Primary language
- **Flask 2.3+** - Web framework
- **SQLAlchemy 2.0+** - ORM (optional, direct SQL also used)
- **SQLite** - Local database (development)
- **PostgreSQL** - Production database (Railway)
- **gunicorn** - Production WSGI server

### Frontend
- **Tailwind CSS 3.x** - Utility-first CSS framework
- **Font Awesome 6.x** - Icon library
- **Vanilla JavaScript** - Client-side interactions
- **Jinja2** - Server-side templating

### External Services
- **Google Sheets API v4** - Data source
- **Railway** - Production hosting
- **GitHub** - Version control and CI/CD trigger

### Development Tools
- **pytest** - Testing framework
- **black** - Code formatter
- **flake8** - Linting
- **mypy** - Type checking
- **coverage.py** - Test coverage

---

## Project Structure

### Root Directory

```
jjf-survey-analytics/
├── app.py                          # 🔴 Main Flask application (1449 lines)
├── railway_app.py                  # Railway-specific entry point
├── survey_analytics.py             # Analytics computation engine
├── survey_normalizer.py            # Data normalization service
├── improved_extractor.py           # Google Sheets extraction
├── auto_sync_service.py            # Background sync service
├── healthcheck.py                  # Health check entry point
├── main.py                         # CLI entry point
│
├── requirements.txt                # Production dependencies
├── pyproject.toml                  # Project metadata & dev config
├── Makefile                        # Development commands
├── Procfile                        # Railway startup command
├── railway.toml                    # Railway configuration
├── runtime.txt                     # Python version specification
│
├── surveyor_data_improved.db       # Raw spreadsheet data (SQLite)
├── survey_normalized.db            # Normalized survey data (SQLite)
│
└── .env.example                    # Environment variable template
```

### Module Structure

```
src/surveyor/                       # Optional CLI library
├── __init__.py
├── cli/                            # Command-line interface
│   ├── __init__.py
│   ├── main.py                     # CLI entry point
│   └── commands.py                 # CLI commands
├── config/                         # Configuration
│   ├── __init__.py
│   ├── settings.py                 # Settings management
│   └── container.py                # Dependency injection
├── models/                         # Data models
│   ├── __init__.py
│   ├── base.py                     # Base model classes
│   └── models.py                   # Domain models
├── repositories/                   # Data access layer
│   ├── __init__.py
│   ├── base_repository.py          # Base repository
│   └── spreadsheet_repository.py   # Spreadsheet data access
├── services/                       # Business logic
│   ├── __init__.py
│   ├── google_sheets_service.py    # Google Sheets integration
│   └── data_extraction_service.py  # Extraction orchestration
└── utils/                          # Utilities
    ├── __init__.py
    └── data_type_detector.py       # Type detection logic
```

### Templates

```
templates/
├── base.html                       # Base layout with navigation
├── dashboard.html                  # Main dashboard (recent activity)
├── survey_analytics.html           # Survey analytics dashboard
├── survey_dashboard.html           # Survey overview
├── survey_responses.html           # Response activity monitor
├── sync_dashboard.html             # Auto-sync management
├── health_dashboard.html           # Health monitoring
├── spreadsheets.html               # Spreadsheets listing
├── spreadsheet_detail.html         # Individual spreadsheet view
├── jobs.html                       # Extraction jobs history
├── login.html                      # Authentication page
└── error.html                      # Error page
```

### Health Check System

```
healthcheck/
├── __init__.py
├── api_validators.py               # Google Sheets API validation
├── dependency_checker.py           # External dependency checks
├── e2e_tests.py                    # End-to-end workflow tests
├── monitoring.py                   # Continuous monitoring
└── config_validator.py             # Configuration validation
```

### Tests

```
tests/
├── __init__.py
├── unit/                           # Unit tests
│   └── test_basic.py
└── integration/                    # Integration tests
    └── (future tests)
```

---

## Data Models

### Raw Data Models

#### Spreadsheet
```python
{
    "id": int,                      # Primary key
    "spreadsheet_id": str,          # Google Sheets ID
    "title": str,                   # Sheet title
    "type": str,                    # Survey/Assessment/Inventory
    "url": str,                     # Google Sheets URL
    "last_synced": datetime,        # Last sync timestamp
    "row_count": int,               # Number of rows
    "created_at": datetime,
    "updated_at": datetime
}
```

#### Raw Data
```python
{
    "id": int,                      # Primary key
    "spreadsheet_id": int,          # Foreign key → spreadsheets
    "sheet_name": str,              # Tab name
    "data": dict,                   # JSON data
    "row_hash": str,                # SHA256 hash
    "extracted_at": datetime
}
```

#### Extraction Job
```python
{
    "id": int,                      # Primary key
    "status": str,                  # pending/running/completed/failed
    "total_sheets": int,
    "processed_sheets": int,
    "total_rows": int,
    "started_at": datetime,
    "completed_at": datetime,
    "error_message": str
}
```

### Normalized Data Models

#### Survey
```python
{
    "id": int,                      # Primary key
    "name": str,                    # Survey name
    "type": str,                    # Survey type
    "spreadsheet_id": str,          # Source Google Sheets ID
    "description": str,
    "created_at": datetime,
    "updated_at": datetime
}
```

#### Survey Question
```python
{
    "id": int,                      # Primary key
    "survey_id": int,               # Foreign key → surveys
    "question_text": str,           # Question content
    "question_type": str,           # text/number/boolean/date
    "order_index": int,             # Display order
    "is_required": bool,
    "metadata": dict                # Additional question data
}
```

#### Survey Response
```python
{
    "id": int,                      # Primary key
    "survey_id": int,               # Foreign key → surveys
    "respondent_id": int,           # Foreign key → respondents
    "submitted_at": datetime,       # Submission timestamp
    "raw_data": dict,               # Original response JSON
    "response_hash": str,           # SHA256 deduplication hash
    "created_at": datetime
}
```

#### Survey Answer
```python
{
    "id": int,                      # Primary key
    "response_id": int,             # Foreign key → survey_responses
    "question_id": int,             # Foreign key → survey_questions
    "answer_value": str,            # Raw answer
    "answer_type": str,             # Detected type
    "parsed_value": Any,            # Type-parsed value
    "created_at": datetime
}
```

#### Respondent
```python
{
    "id": int,                      # Primary key
    "email": str,                   # Respondent email (unique)
    "name": str,                    # Respondent name
    "organization": str,            # Organization
    "created_at": datetime,
    "last_response_at": datetime
}
```

#### Sync Tracking
```python
{
    "id": int,                      # Primary key
    "spreadsheet_id": str,          # Tracked spreadsheet
    "last_sync": datetime,          # Last successful sync
    "last_hash": str,               # Last data hash
    "records_synced": int,          # Count of synced records
    "status": str,                  # up_to_date/syncing/error
    "error_message": str
}
```

---

## API Documentation

### Web Routes (HTML Responses)

#### Main Dashboard
```
GET /
    Returns: HTML dashboard with recent activity
    Auth: Required if REQUIRE_AUTH=true
    Template: dashboard.html
    Data:
        - recent_updates: List of latest spreadsheet updates
        - stats: Overall statistics
```

#### Authentication
```
GET /login
    Returns: Login page
    Template: login.html

POST /login
    Body: { password: str }
    Returns: Redirect to / or error
    Sets: session['authenticated'] = True

GET /logout
    Returns: Redirect to /login
    Clears: session
```

#### Spreadsheets
```
GET /spreadsheets
    Returns: Grid view of all spreadsheets
    Auth: Required
    Template: spreadsheets.html
    Query Params:
        - search: str (filter by title)
        - type: str (filter by type)

GET /spreadsheet/<id>
    Returns: Detailed view of single spreadsheet
    Auth: Required
    Template: spreadsheet_detail.html
    Path Params:
        - id: int (spreadsheet primary key)
```

#### Surveys
```
GET /surveys
    Returns: Survey analytics dashboard
    Auth: Required
    Template: survey_analytics.html
    Data:
        - total_surveys
        - total_responses
        - total_respondents
        - response_rate
        - survey_breakdown
        - completion_stats

GET /surveys/analytics
    Returns: Detailed question-level analysis
    Auth: Required
    Template: survey_analytics.html
    Query Params:
        - survey_id: int (optional filter)

GET /surveys/responses
    Returns: Response activity timeline
    Auth: Required
    Template: survey_responses.html
    Data:
        - response_timeline
        - browser_stats
        - device_stats
```

#### Auto-Sync
```
GET /sync
    Returns: Auto-sync management dashboard
    Auth: Required
    Template: sync_dashboard.html
    Data:
        - service_status
        - last_sync
        - sync_history
```

#### Health Checks
```
GET /health/dashboard
    Returns: Health monitoring dashboard
    Auth: Required
    Template: health_dashboard.html
    Data:
        - api_status
        - dependency_status
        - e2e_test_results

GET /health/test
    Returns: Run health checks and show results
    Auth: Required
    Runs: All health check modules
```

### API Routes (JSON Responses)

#### Statistics
```
GET /api/stats
    Returns: {
        total_spreadsheets: int,
        total_rows: int,
        last_sync: datetime,
        spreadsheet_types: {
            Survey: int,
            Assessment: int,
            Inventory: int
        }
    }
    Auth: Required
    Content-Type: application/json
```

#### Spreadsheet Data
```
GET /api/spreadsheet/<id>/data
    Returns: {
        spreadsheet: {...},
        data: [...],
        row_count: int
    }
    Auth: Required
    Path Params:
        - id: int
    Content-Type: application/json
```

#### Auto-Sync Control
```
GET /api/sync/status
    Returns: {
        running: bool,
        last_sync: datetime,
        records_synced: int,
        status: str
    }
    Auth: Required
    Content-Type: application/json

POST /api/sync/start
    Returns: {
        success: bool,
        message: str
    }
    Auth: Required
    Content-Type: application/json

POST /api/sync/stop
    Returns: {
        success: bool,
        message: str
    }
    Auth: Required
    Content-Type: application/json

POST /api/sync/force
    Returns: {
        success: bool,
        records_synced: int,
        message: str
    }
    Auth: Required
    Content-Type: application/json
```

#### Survey Search & Export
```
GET /api/survey/search
    Query Params:
        - q: str (search query)
        - survey_id: int (optional)
    Returns: {
        results: [...],
        total: int
    }
    Auth: Required
    Content-Type: application/json

GET /api/survey/<id>/export
    Returns: CSV file download
    Auth: Required
    Path Params:
        - id: int (survey ID)
    Content-Type: text/csv
```

#### Health Status
```
GET /health/status
    Returns: {
        status: "healthy" | "degraded" | "unhealthy",
        checks: {
            api: {...},
            database: {...},
            dependencies: {...}
        },
        timestamp: datetime
    }
    Auth: Not required (public health endpoint)
    Content-Type: application/json

POST /health/check
    Body: {
        checks: ["api", "database", "dependencies"]
    }
    Returns: {
        results: {...}
    }
    Auth: Required
    Content-Type: application/json
```

---

## Core Components

### app.py - Main Application

**Key Classes:**

```python
class DatabaseManager:
    """Manages database connections and queries"""

    def get_connection(db_path: str) -> sqlite3.Connection:
        """Get database connection with row factory"""

    def get_all_spreadsheets() -> List[Dict]:
        """Fetch all spreadsheets"""

    def get_spreadsheet_by_id(id: int) -> Dict:
        """Fetch single spreadsheet"""

    def get_latest_updates(limit: int = 20) -> List[Dict]:
        """Get recent spreadsheet updates with filtering"""

    def get_dashboard_stats() -> Dict:
        """Compute dashboard statistics"""
```

**Key Routes:**
- Authentication: `/login`, `/logout`
- Dashboards: `/`, `/surveys`, `/sync`, `/health/dashboard`
- API: `/api/*`

### survey_analytics.py - Analytics Engine

```python
class SurveyAnalytics:
    """Survey data analytics and statistics"""

    def get_survey_stats() -> Dict:
        """Overall survey statistics"""

    def get_survey_breakdown() -> List[Dict]:
        """Per-survey metrics"""

    def get_completion_stats() -> Dict:
        """Completion rate analysis"""

    def get_respondent_analysis() -> Dict:
        """Respondent patterns"""

    def get_question_analytics(survey_id: int) -> List[Dict]:
        """Question-level analysis"""
```

### survey_normalizer.py - Data Normalization

```python
class SurveyNormalizer:
    """Normalize raw Google Sheets data into relational structure"""

    def normalize_all(auto_mode: bool = False) -> None:
        """Normalize all spreadsheet data"""

    def detect_question_type(value: Any) -> str:
        """Detect data type of field"""

    def parse_value(value: str, type: str) -> Any:
        """Parse value based on detected type"""

    def deduplicate_responses(responses: List[Dict]) -> List[Dict]:
        """Remove duplicate responses using SHA256"""
```

### improved_extractor.py - Google Sheets Extraction

```python
class ImprovedExtractor:
    """Extract data from Google Sheets"""

    DEFAULT_URLS = [
        # 6 predefined JJF Technology Assessment spreadsheets
    ]

    def extract_spreadsheet(url: str) -> Dict:
        """Extract single spreadsheet"""

    def extract_all_default() -> None:
        """Extract all default spreadsheets"""

    def create_extraction_job() -> int:
        """Create job tracking record"""

    def update_job_status(job_id: int, status: str) -> None:
        """Update job status"""
```

### auto_sync_service.py - Background Sync

```python
class AutoSyncService:
    """Automatic data synchronization service"""

    def __init__(self, interval: int = 300):
        """Initialize with sync interval (seconds)"""

    async def start(self) -> None:
        """Start background sync service"""

    async def stop(self) -> None:
        """Stop background sync service"""

    async def force_sync(self) -> int:
        """Force immediate sync"""

    async def check_for_changes() -> List[Dict]:
        """Detect changed spreadsheets"""

    async def sync_spreadsheet(spreadsheet_id: str) -> int:
        """Sync single spreadsheet"""
```

---

## Database Design

### Schema Relationships

```
spreadsheets (Raw Data DB)
    ↓ 1:N
raw_data

extraction_jobs (Independent)

surveys (Normalized DB)
    ↓ 1:N
survey_questions
    ↓ 1:N
survey_answers
    ↓ N:1
survey_responses
    ↓ N:1
respondents

sync_tracking (Independent)
```

### Indexes

**Raw Data DB:**
```sql
CREATE INDEX idx_spreadsheets_type ON spreadsheets(type);
CREATE INDEX idx_raw_data_spreadsheet_id ON raw_data(spreadsheet_id);
CREATE INDEX idx_raw_data_hash ON raw_data(row_hash);
```

**Normalized DB:**
```sql
CREATE INDEX idx_survey_responses_survey_id ON survey_responses(survey_id);
CREATE INDEX idx_survey_responses_respondent_id ON survey_responses(respondent_id);
CREATE INDEX idx_survey_answers_response_id ON survey_answers(response_id);
CREATE INDEX idx_survey_answers_question_id ON survey_answers(question_id);
CREATE INDEX idx_respondents_email ON respondents(email);
CREATE INDEX idx_sync_tracking_spreadsheet_id ON sync_tracking(spreadsheet_id);
```

---

## Authentication

### Session-Based Authentication

```python
# Configuration
REQUIRE_AUTH = os.getenv('REQUIRE_AUTH', 'false').lower() == 'true'
APP_PASSWORD = os.getenv('APP_PASSWORD', 'survey2025!')

# Decorator
@require_auth
def protected_route():
    # Route logic
    pass

# Login flow
POST /login
    → Validate password
    → Set session['authenticated'] = True
    → Redirect to /

# Logout flow
GET /logout
    → Clear session
    → Redirect to /login
```

### Local Development
- **Default:** Authentication disabled (`REQUIRE_AUTH=false`)
- **No password required** for local testing

### Production
- **Set:** `REQUIRE_AUTH=true`
- **Configure:** `APP_PASSWORD` environment variable
- **Session:** Flask secure sessions with `SECRET_KEY`

---

## Auto-Sync Service

### Architecture

```
┌─────────────────────────────────────┐
│   Auto-Sync Service (async)         │
│                                     │
│  1. Wake up (every 5 minutes)       │
│  2. Check for changes (hash compare)│
│  3. Extract changed sheets          │
│  4. Normalize new data              │
│  5. Update sync_tracking            │
│  6. Sleep                           │
└─────────────────────────────────────┘
```

### Change Detection

```python
# Hash-based change detection
current_hash = sha256(spreadsheet_data)
last_hash = get_last_sync_hash(spreadsheet_id)

if current_hash != last_hash:
    sync_spreadsheet(spreadsheet_id)
    update_sync_tracking(spreadsheet_id, current_hash)
```

### Service Management

```bash
# Web UI
http://localhost:8080/sync
    → Start Service button
    → Stop Service button
    → Force Sync Now button

# API
POST /api/sync/start
POST /api/sync/stop
POST /api/sync/force
```

---

## Health Check System

### Components

1. **API Validators** - Google Sheets API connectivity
2. **Dependency Checker** - External service availability
3. **E2E Tests** - Complete workflow validation
4. **Config Validator** - Environment variable validation
5. **Continuous Monitoring** - Background health checks

### Health Check Flow

```python
# Run all checks
python healthcheck.py

# Results:
{
    "api_validation": "pass" | "fail",
    "dependencies": "pass" | "fail",
    "e2e_tests": "pass" | "fail",
    "config": "pass" | "fail",
    "overall_status": "healthy" | "degraded" | "unhealthy"
}
```

### Health Endpoint

```
GET /health/status
    → Quick health check for Railway monitoring
    → Returns 200 if healthy, 503 if unhealthy
```

---

## Development Workflows

### Setup New Development Environment

```bash
# 1. Clone repository
git clone <repo-url>
cd jjf-survey-analytics

# 2. Create virtual environment
make setup

# 3. Activate virtual environment
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# 4. Install dependencies
make install

# 5. Extract and normalize data
make build

# 6. Start development server
make dev
```

### Daily Development Workflow

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Pull latest changes
git pull origin master

# 3. Update dependencies if needed
make install

# 4. Make code changes
# ... edit files ...

# 5. Run quality checks
make quality

# 6. Test locally
make dev

# 7. Commit and push
git add .
git commit -m "feat: Your feature description"
git push origin master

# Railway auto-deploys from master
```

### Adding a New Feature

```bash
# 1. Create feature branch
git checkout -b feature/new-feature

# 2. Develop feature
# ... code changes ...

# 3. Run tests
make test

# 4. Format code
make format

# 5. Commit changes
git commit -m "feat: Add new feature"

# 6. Push and create PR
git push origin feature/new-feature
# Create pull request on GitHub

# 7. After review, merge to master
# Railway auto-deploys
```

---

## Testing Strategy

### Test Pyramid

```
       /\
      /E2E\           Few, critical workflows
     /------\
    / Integ \        Moderate, component interactions
   /----------\
  /   Unit     \     Many, fast, isolated
 /--------------\
```

### Running Tests

```bash
# All tests
make test

# With coverage
make test-cov

# Specific test file
pytest tests/unit/test_basic.py -v

# Integration tests
pytest tests/integration/ -v
```

### Writing Tests

```python
# tests/unit/test_example.py
import pytest

def test_example():
    """Test description"""
    result = function_under_test()
    assert result == expected_value

@pytest.fixture
def sample_data():
    """Reusable test data"""
    return {"key": "value"}

def test_with_fixture(sample_data):
    """Test using fixture"""
    assert sample_data["key"] == "value"
```

---

## Deployment Architecture

### Railway Production

```
GitHub (master branch)
    ↓ Push trigger
Railway Build
    ↓ gunicorn + app.py
Railway Container
    ├── PostgreSQL database
    ├── Environment variables
    └── Health checks (/health)
    ↓ HTTPS
Public URL
```

### Environment Variables (Railway)

```bash
# Set in Railway dashboard
PORT=<auto-assigned>              # Railway sets this
DATABASE_URL=<auto-provisioned>   # Railway sets this
SECRET_KEY=<random-generated>
APP_PASSWORD=<secure-password>
REQUIRE_AUTH=true
LOG_LEVEL=INFO
RAILWAY_ENVIRONMENT=production
```

### Deployment Process

```bash
# 1. Make changes locally
# 2. Test thoroughly
make test
make dev

# 3. Commit and push
git commit -m "Description"
git push origin master

# 4. Railway automatically:
#    - Detects push
#    - Builds container
#    - Runs health checks
#    - Deploys if healthy
#    - Routes traffic

# 5. Monitor deployment
railway logs --tail
```

---

## Performance Considerations

### Database Optimization
- **Indexes:** All foreign keys and search fields
- **Connection Pooling:** Reuse connections
- **Query Optimization:** Use EXPLAIN for slow queries
- **Batch Operations:** Bulk inserts for large datasets

### Caching Strategy
- **Static Assets:** Browser caching
- **Template Caching:** Jinja2 cache (production)
- **API Responses:** Short-lived cache for stats

### Async Operations
- **Auto-Sync:** Background async tasks
- **Long Operations:** Async/await pattern
- **Non-blocking:** Don't block web requests

---

## Security

### Best Practices
- ✅ **No secrets in code** - Use environment variables
- ✅ **Session security** - Secure cookies, SECRET_KEY
- ✅ **SQL injection prevention** - Parameterized queries
- ✅ **XSS protection** - Jinja2 auto-escaping
- ✅ **CSRF tokens** - For POST requests (future)

### Environment Variables
```bash
# Never commit these
SECRET_KEY=<strong-random-key>
APP_PASSWORD=<secure-password>
DATABASE_URL=<connection-string>
GOOGLE_API_KEY=<api-key>  # If using API key auth
```

---

## Troubleshooting

### Common Issues

**Database locked:**
```python
# Use WAL mode for concurrent access
connection.execute("PRAGMA journal_mode=WAL")
```

**Memory issues with large datasets:**
```python
# Use generators and batch processing
for batch in batch_generator(data, size=100):
    process_batch(batch)
```

**Slow queries:**
```sql
-- Add indexes
CREATE INDEX idx_column ON table(column);

-- Analyze query plan
EXPLAIN QUERY PLAN SELECT ...;
```

---

## Additional Resources

- [CLAUDE.md](CLAUDE.md) - AI agent instructions
- [README.md](README.md) - Project overview
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Deployment procedures

---

**Last Updated:** 2025-10-06
**Maintainers:** Development Team
**Status:** Active Development
