# 🏗️ JJF Survey Analytics - System Architecture

## 📋 Table of Contents
- [Overview](#overview)
- [System Components](#system-components)
- [Data Flow](#data-flow)
- [Database Schema](#database-schema)
- [API Architecture](#api-architecture)
- [Deployment Architecture](#deployment-architecture)
- [Security](#security)

## Overview

The JJF Survey Analytics Platform is a multi-tier web application designed to extract, normalize, analyze, and visualize survey data from Google Sheets. The system follows a modular architecture with clear separation of concerns.

### Technology Stack
- **Backend:** Python 3.8+, Flask
- **Database:** SQLite (development), PostgreSQL (production)
- **Frontend:** HTML5, Tailwind CSS, JavaScript
- **Deployment:** Railway (production), Local (development)
- **APIs:** Google Sheets API v4

## System Components

### 1. Data Extraction Layer

#### `improved_extractor.py`
- **Purpose:** Extract raw data from Google Sheets
- **Responsibilities:**
  - Connect to Google Sheets API
  - Download spreadsheet data
  - Store raw data in SQLite database
  - Track extraction jobs and metadata
- **Output:** `surveyor_data_improved.db`

**Key Features:**
- Batch processing of multiple sheets
- Error handling and retry logic
- Job tracking and history
- SHA256 hashing for deduplication

### 2. Data Normalization Layer

#### `survey_normalizer.py`
- **Purpose:** Transform raw data into normalized relational structure
- **Responsibilities:**
  - Parse survey questions and responses
  - Detect and normalize data types
  - Create relational mappings
  - Track respondents and timestamps
- **Output:** `survey_normalized.db`

**Key Features:**
- Automatic type detection (text, number, boolean, date)
- Intelligent change detection
- Full rebuild or incremental sync modes
- Comprehensive error handling

### 3. Analytics Engine

#### `survey_analytics.py`
- **Purpose:** Provide statistical analysis and insights
- **Responsibilities:**
  - Calculate response rates and completion statistics
  - Analyze answer distributions
  - Track respondent patterns
  - Generate time-series data
- **Output:** JSON data for dashboards

**Key Features:**
- Question-level analytics
- Respondent behavior analysis
- Browser and device tracking
- Response frequency patterns

### 4. Auto-Sync Service

#### `auto_sync_service.py`
- **Purpose:** Automatic background synchronization
- **Responsibilities:**
  - Monitor for data changes
  - Trigger normalization when needed
  - Track sync history
  - Provide service management API
- **Output:** Continuous data synchronization

**Key Features:**
- Configurable check intervals
- Intelligent change detection
- Service start/stop/status API
- Activity logging

### 5. Health Check System

#### `healthcheck/` package
- **Purpose:** Monitor system health and dependencies
- **Components:**
  - `api_validators.py` - API key validation
  - `dependency_checker.py` - External service checks
  - `e2e_tests.py` - End-to-end functionality tests
  - `monitoring.py` - Continuous monitoring
  - `config_validator.py` - Configuration validation

**Key Features:**
- Comprehensive health checks
- Real-time monitoring
- Alert generation
- Web dashboard interface

### 6. Web Application

#### `app.py` (Development) / `railway_app.py` (Production)
- **Purpose:** Main web interface and API server
- **Responsibilities:**
  - Serve web pages and dashboards
  - Provide REST API endpoints
  - Handle authentication
  - Manage sessions
- **Output:** HTTP responses

**Key Features:**
- Multiple dashboard views
- RESTful API
- Password authentication
- Session management
- PostgreSQL/SQLite support

## Data Flow

### Extraction Flow
```
Google Sheets → improved_extractor.py → surveyor_data_improved.db
                                      ↓
                                  extraction_jobs table
```

### Normalization Flow
```
surveyor_data_improved.db → survey_normalizer.py → survey_normalized.db
                                                  ↓
                                              normalization_jobs table
```

### Analytics Flow
```
survey_normalized.db → survey_analytics.py → JSON data → Web Dashboard
```

### Auto-Sync Flow
```
Timer → auto_sync_service.py → Check for changes → Trigger normalization
                              ↓
                          sync_tracking table
```

### Request Flow
```
User Browser → Flask App → Database Query → Data Processing → JSON/HTML Response
            ↓
        Authentication Check
            ↓
        Session Validation
```

## Database Schema

### Raw Data Database (`surveyor_data_improved.db`)

#### `spreadsheets` table
```sql
CREATE TABLE spreadsheets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    spreadsheet_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    sheet_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_synced TIMESTAMP
);
```

#### `raw_data` table
```sql
CREATE TABLE raw_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    spreadsheet_id INTEGER NOT NULL,
    data_hash TEXT NOT NULL,
    data_json TEXT NOT NULL,
    row_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (spreadsheet_id) REFERENCES spreadsheets(id)
);
```

#### `extraction_jobs` table
```sql
CREATE TABLE extraction_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status TEXT NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    total_sheets INTEGER,
    successful_sheets INTEGER,
    failed_sheets INTEGER,
    error_message TEXT
);
```

### Normalized Database (`survey_normalized.db`)

#### `surveys` table
```sql
CREATE TABLE surveys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    spreadsheet_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    survey_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `survey_questions` table
```sql
CREATE TABLE survey_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    survey_id INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    question_order INTEGER,
    question_type TEXT,
    FOREIGN KEY (survey_id) REFERENCES surveys(id)
);
```

#### `respondents` table
```sql
CREATE TABLE respondents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT,
    name TEXT,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `survey_responses` table
```sql
CREATE TABLE survey_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    survey_id INTEGER NOT NULL,
    respondent_id INTEGER,
    submitted_at TIMESTAMP,
    browser TEXT,
    device TEXT,
    FOREIGN KEY (survey_id) REFERENCES surveys(id),
    FOREIGN KEY (respondent_id) REFERENCES respondents(id)
);
```

#### `survey_answers` table
```sql
CREATE TABLE survey_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    response_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    answer_text TEXT,
    answer_type TEXT,
    numeric_value REAL,
    boolean_value INTEGER,
    date_value TIMESTAMP,
    FOREIGN KEY (response_id) REFERENCES survey_responses(id),
    FOREIGN KEY (question_id) REFERENCES survey_questions(id)
);
```

#### `sync_tracking` table
```sql
CREATE TABLE sync_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sync_type TEXT NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status TEXT,
    changes_detected INTEGER,
    records_processed INTEGER,
    error_message TEXT
);
```

## API Architecture

### REST API Endpoints

#### Dashboard & Statistics
- `GET /api/stats` - Overall dashboard statistics
- `GET /api/survey/stats` - Survey-specific statistics

#### Survey Data
- `GET /api/survey/search?q=<query>` - Search survey responses
- `GET /api/survey/<id>/export` - Export survey data as CSV
- `GET /api/survey/<id>/analytics` - Detailed analytics for survey

#### Auto-Sync Management
- `GET /api/sync/status` - Current sync service status
- `POST /api/sync/start` - Start auto-sync service
- `POST /api/sync/stop` - Stop auto-sync service
- `POST /api/sync/force` - Force immediate synchronization

#### Health Checks
- `GET /health/status` - System health status (JSON)
- `POST /health/check` - Run specific health checks
- `GET /health/dashboard` - Health check web interface

### Response Format

All API endpoints return JSON with consistent structure:

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully",
  "timestamp": "2025-10-03T12:00:00Z"
}
```

Error responses:
```json
{
  "success": false,
  "error": "Error description",
  "code": "ERROR_CODE",
  "timestamp": "2025-10-03T12:00:00Z"
}
```

## Deployment Architecture

### Local Development
```
┌─────────────────────────────────────┐
│  Developer Machine                  │
│  ┌───────────────────────────────┐  │
│  │  Flask App (app.py)           │  │
│  │  Port: 5001                   │  │
│  │  Debug: True                  │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │  SQLite Databases             │  │
│  │  - surveyor_data_improved.db  │  │
│  │  - survey_normalized.db       │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

### Railway Production
```
┌─────────────────────────────────────┐
│  Railway Platform                   │
│  ┌───────────────────────────────┐  │
│  │  Flask App (railway_app.py)   │  │
│  │  Port: Dynamic (from env)     │  │
│  │  Debug: False                 │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │  PostgreSQL Database          │  │
│  │  (Managed Service)            │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │  Health Check Monitoring      │  │
│  │  Path: /health/status         │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

## Security

### Authentication
- Password-based authentication
- Session management with secure cookies
- Configurable via `REQUIRE_AUTH` environment variable
- Default password: `survey2025!` (should be changed in production)

### Environment Variables
- `SECRET_KEY` - Flask session encryption
- `APP_PASSWORD` - Application password
- `DATABASE_URL` - Database connection string (production)

### Best Practices
- All sensitive data in environment variables
- No hardcoded credentials
- HTTPS enforced in production (Railway)
- Session timeout configuration
- Input validation on all endpoints

### Data Protection
- SHA256 hashing for data deduplication
- Foreign key constraints for data integrity
- Transaction support for atomic operations
- Backup and restore capabilities

---

**Last Updated:** 2025-10-03

