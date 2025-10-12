# PROJECT_ORGANIZATION.md - JJF Survey Analytics Organization Standard

**Project:** JJF Survey Analytics Platform
**Created:** 2025-10-11
**Version:** 1.0.0
**Framework:** Flask 2.3+ (Python 3.13)

> This document defines the official organization standard for the JJF Survey Analytics project. All files must follow these conventions to maintain consistency and developer experience.

---

## Table of Contents

1. [Directory Structure](#directory-structure)
2. [File Placement Rules](#file-placement-rules)
3. [Naming Conventions](#naming-conventions)
4. [Flask-Specific Organization](#flask-specific-organization)
5. [Migration Procedures](#migration-procedures)
6. [Version History](#version-history)

---

## Directory Structure

### Overview

```
jjf-survey-analytics/
├── app.py                          # Main Flask application entry point
├── railway_app.py                  # Railway deployment entry point
├── main.py                         # CLI entry point
├── requirements.txt                # Python dependencies
├── Procfile                        # Railway process definition
├── Makefile                        # Development commands
├── pyproject.toml                  # Project configuration
├── railway.toml                    # Railway configuration
├── .gitignore                      # Git ignore patterns
├── README.md                       # Project overview
├── CLAUDE.md                       # AI agent instructions
│
├── docs/                           # All documentation
│   ├── reference/                  # Technical reference documentation
│   ├── features/                   # Feature-specific documentation
│   ├── deployment/                 # Deployment documentation
│   ├── development/                # Development process documentation
│   ├── simple-app/                 # Simple app alternative documentation
│   ├── reports/                    # Report system documentation
│   ├── PROGRESS.md                 # Project progress tracking
│   ├── work-logs/                  # Development work logs
│   └── _archive/                   # Archived documentation
│
├── src/                            # Application source code
│   ├── extractors/                 # Data extraction modules
│   ├── normalizers/                # Data normalization modules
│   ├── analytics/                  # Analytics and analysis modules
│   ├── services/                   # Business logic services
│   ├── healthcheck/                # Health check modules
│   └── utils/                      # Utility modules
│
├── scripts/                        # Operational scripts
│   ├── deployment/                 # Deployment scripts
│   ├── database/                   # Database management scripts
│   ├── testing/                    # Testing utility scripts
│   └── utilities/                  # General utility scripts
│
├── templates/                      # Flask Jinja2 templates
│   ├── base.html                   # Main app base template
│   ├── dashboard.html              # Main app templates
│   ├── ...
│   ├── simple/                     # Simple app templates
│   └── reports/                    # Report system templates
│
├── tests/                          # Test suite
│   ├── unit/                       # Unit tests
│   └── integration/                # Integration tests
│
├── tmp/                            # Temporary and backup files
│
├── hybrid_surveyor/                # Separate surveyor package
│
└── src/surveyor/                   # Legacy surveyor package
```

---

## File Placement Rules

### Root Level Files (STRICT - Maximum 15 files)

**Only these files belong in the root:**

| File | Purpose | Priority |
|------|---------|----------|
| app.py | Main Flask application | CRITICAL |
| railway_app.py | Railway deployment entry | CRITICAL |
| main.py | CLI entry point | CRITICAL |
| requirements.txt | Python dependencies | CRITICAL |
| Procfile | Railway process definition | CRITICAL |
| Makefile | Development commands | IMPORTANT |
| pyproject.toml | Project configuration | IMPORTANT |
| railway.toml | Railway configuration | CRITICAL |
| .gitignore | Git ignore patterns | CRITICAL |
| README.md | Project overview | CRITICAL |
| CLAUDE.md | AI agent instructions | CRITICAL |
| .env | Environment variables (gitignored) | IMPORTANT |
| .env.example | Environment template | STANDARD |
| LICENSE | Project license | STANDARD |
| CHANGELOG.md | Version history | OPTIONAL |

**RULE: Any other .py or .md file in root is MISPLACED**

---

### Documentation Files

**Location:** `docs/`

#### Reference Documentation (`docs/reference/`)

**Purpose:** Technical reference, architecture, and API documentation

**Files:**
- PROJECT_ORGANIZATION.md (this file)
- ARCHITECTURE.md
- DEVELOPER.md
- DEPLOYMENT_GUIDE.md
- SOT_ARCHITECTURE.md
- QUICK_REFERENCE.md
- POSTGRESQL_SCHEMA_FIX.md

**Naming:** SCREAMING_SNAKE_CASE.md (for compatibility with existing links)

#### Feature Documentation (`docs/features/`)

**Purpose:** Individual feature implementation details

**Files:**
- authentication.md (from AUTHENTICATION_CONFIG.md)
- auto-sync.md (from AUTO_SYNC_IMPLEMENTATION.md)
- health-checks.md (from HEALTHCHECK_README.md)
- health-check-endpoints.md (from HEALTHCHECK_ENDPOINTS.md)
- data-sync.md (from DATA_SYNC_FIXES.md)
- empty-row-validation.md (from EMPTY_ROW_VALIDATION.md)
- local-auth-disabled.md (from AUTH_DISABLED_FOR_LOCAL.md)

**Naming:** kebab-case.md

#### Deployment Documentation (`docs/deployment/`)

**Purpose:** Deployment procedures and configuration

**Files:**
- railway.md (from RAILWAY_DEPLOYMENT.md)
- railway-health.md (from RAILWAY_HEALTH_CONFIG.md)
- security.md (from SECURITY_DEBT.md)

**Naming:** kebab-case.md

#### Development Documentation (`docs/development/`)

**Purpose:** Development process, summaries, and implementation notes

**Files:**
- dashboard-improvements.md
- extraction-summary.md
- survey-analytics-summary.md
- project-summary.md
- claude-mpm-init.md
- implementation-summaries/
  - final.md

**Naming:** kebab-case.md

#### Simple App Documentation (`docs/simple-app/`)

**Purpose:** Alternative "simple app" implementation documentation

**Files:**
- README.md (index for simple app)
- QUICKSTART.md
- ARCHITECTURE.md
- INDEX.md
- tabs-reference.md
- extractor-tabs.md
- dashboard-design.md
- dashboard-implementation.md
- refactor-summary.md
- analysis/
  - db-analysis.md
  - extraction-results.md
  - sheet-mapping.md
  - mapping-results.md

**Naming:** kebab-case.md for new files, SCREAMING_SNAKE_CASE.md for index files

#### Report System Documentation (`docs/reports/`)

**Purpose:** Planned reporting system documentation

**Files:**
- README.md (index)
- design-specifications.md
- analysis-summary.md
- quickstart.md

**Naming:** kebab-case.md

---

### Python Source Files

**Location:** `src/`

#### Data Extractors (`src/extractors/`)

**Purpose:** Google Sheets data extraction modules

**Files:**
- __init__.py
- improved_extractor.py
- simple_extractor.py
- sheets_reader.py

**Import Pattern:**
```python
from src.extractors.improved_extractor import extract_data
```

#### Data Normalizers (`src/normalizers/`)

**Purpose:** Survey data normalization and transformation

**Files:**
- __init__.py
- survey_normalizer.py

**Import Pattern:**
```python
from src.normalizers.survey_normalizer import normalize_surveys
```

#### Analytics (`src/analytics/`)

**Purpose:** Survey analytics, analysis, and AI features

**Files:**
- __init__.py
- survey_analytics.py
- maturity_rubric.py
- ai_analyzer.py

**Import Pattern:**
```python
from src.analytics.survey_analytics import SurveyAnalytics
from src.analytics.maturity_rubric import MaturityRubric
from src.analytics.ai_analyzer import AIAnalyzer
```

#### Services (`src/services/`)

**Purpose:** Business logic services

**Files:**
- __init__.py
- auto_sync_service.py
- report_generator.py

**Import Pattern:**
```python
from src.services.auto_sync_service import AutoSyncService
```

#### Health Checks (`src/healthcheck/`)

**Purpose:** Application health monitoring

**Files:**
- __init__.py
- api_validators.py
- dependency_checker.py
- e2e_tests.py
- monitoring.py

**Note:** Keep existing structure, already well-organized

#### Utilities (`src/utils/`)

**Purpose:** Shared utility functions and helpers

**Files:**
- __init__.py
- db_utils.py
- view_tab_summary.py

**Import Pattern:**
```python
from src.utils.db_utils import get_db_connection
```

---

### Scripts

**Location:** `scripts/`

**Purpose:** Operational scripts that are not imported as modules

#### Deployment Scripts (`scripts/deployment/`)

**Files:**
- railway_init.py
- railway_import_data.py
- pre_deploy_check.py
- export_data_for_railway.py

**Note:** Consider keeping railway_app.py in root for Railway Procfile simplicity

#### Database Scripts (`scripts/database/`)

**Files:**
- init_database.py
- check_db.py
- create_backup.py
- migrate_sqlite_to_postgres.py
- import_to_railway_postgres.py
- analyze_data.py

#### Testing Scripts (`scripts/testing/`)

**Files:**
- test_maturity_fixed.py
- test_survey_endpoints.py
- test_templates.py
- run_healthcheck.py

**Note:** Keep healthcheck.py in root for easy access: `python healthcheck.py`

---

### Templates

**Location:** `templates/`

**Flask Convention:** All Jinja2 templates in templates/ directory

#### Main App Templates (templates/)

**Files:**
- base.html (base template with navigation)
- dashboard.html
- survey_analytics.html
- survey_responses.html
- sync_dashboard.html
- health_dashboard.html
- login.html
- ... (all main app templates)

**Naming:** snake_case.html

#### Simple App Templates (`templates/simple/`)

**Purpose:** Templates for alternative "simple app" implementation

**Files:**
- admin.html (from simple_admin.html)
- base.html (from simple_base.html)
- data_nav.html (from simple_data_nav.html)
- home.html (from simple_home.html)
- summary.html (from simple_summary.html)
- tab_view.html (from simple_tab_view.html)

**Naming:** snake_case.html (remove "simple_" prefix, directory provides context)

**Template References:**
```python
# In simple_app.py
return render_template('simple/home.html')
```

#### Report Templates (`templates/reports/`)

**Purpose:** Report generation templates

**Files:**
- contact_detail.html
- organization_detail.html

**Naming:** snake_case.html

---

### Tests

**Location:** `tests/`

**Structure:**
```
tests/
├── __init__.py
├── conftest.py              # Pytest configuration
├── unit/                    # Unit tests
│   ├── __init__.py
│   └── test_basic.py
└── integration/             # Integration tests
    ├── __init__.py
    ├── test_extractors.py
    ├── test_normalizers.py
    └── test_api.py
```

**Naming:** test_*.py

**Import Pattern:**
```python
# Tests import from src/
from src.extractors.improved_extractor import extract_data
```

---

### Temporary Files

**Location:** `tmp/`

**Purpose:** Backup files, legacy code, temporary artifacts

**Files:**
- app_old.py
- *.bak
- *.tmp

**Git:** Add `tmp/` to .gitignore

---

## Naming Conventions

### File Types

| File Type | Convention | Example |
|-----------|------------|---------|
| Python modules | snake_case.py | improved_extractor.py |
| Python packages | snake_case/ | src/extractors/ |
| Templates | snake_case.html | survey_analytics.html |
| Documentation (reference) | SCREAMING_SNAKE_CASE.md | ARCHITECTURE.md |
| Documentation (feature) | kebab-case.md | auto-sync.md |
| Test files | test_*.py | test_extractors.py |
| Scripts | snake_case.py | init_database.py |
| Configuration | lowercase | Makefile, Procfile |

### Python Naming

```python
# Modules and packages
import improved_extractor
from src.extractors import sheets_reader

# Classes
class SurveyAnalytics:
class MaturityRubric:

# Functions
def extract_data():
def normalize_surveys():

# Constants
DATABASE_URL = "..."
MAX_RETRIES = 3

# Variables
survey_data = {}
response_count = 0
```

### Directory Naming

- All directories: lowercase with underscores (snake_case)
- Examples: `src/extractors/`, `docs/simple-app/`, `scripts/deployment/`

---

## Flask-Specific Organization

### Application Entry Points

**Development:** `app.py`
```python
# app.py - Main Flask application
from flask import Flask
app = Flask(__name__)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
```

**Production (Railway):** `railway_app.py`
```python
# railway_app.py - Railway-specific initialization
from app import app
# Railway-specific setup
```

**CLI:** `main.py`
```python
# main.py - Command-line interface
import click
@click.command()
def cli():
    pass
```

### Template Organization

**Base Template Pattern:**
```
templates/
├── base.html                # Main app base
├── dashboard.html           # Extends base.html
├── simple/
│   ├── base.html           # Simple app base
│   └── home.html           # Extends simple/base.html
└── reports/
    └── contact_detail.html  # Standalone report template
```

**Template Inheritance:**
```jinja2
{# templates/dashboard.html #}
{% extends "base.html" %}

{# templates/simple/home.html #}
{% extends "simple/base.html" %}
```

### Static Files (when added)

**Future Structure:**
```
static/
├── css/
│   └── styles.css
├── js/
│   └── app.js
└── images/
    └── logo.png
```

### Blueprint Organization (when needed)

**Future Structure:**
```
src/
├── blueprints/
│   ├── __init__.py
│   ├── main/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py
│   └── simple/
│       ├── __init__.py
│       └── routes.py
```

---

## Migration Procedures

### Moving Files Safely

#### Step 1: Create Directory Structure
```bash
mkdir -p docs/reference
mkdir -p docs/features
mkdir -p docs/deployment
mkdir -p docs/development
mkdir -p docs/simple-app/analysis
mkdir -p docs/reports
mkdir -p src/extractors
mkdir -p src/normalizers
mkdir -p src/analytics
mkdir -p src/services
mkdir -p src/utils
mkdir -p scripts/deployment
mkdir -p scripts/database
mkdir -p scripts/testing
mkdir -p templates/simple
mkdir -p templates/reports
mkdir -p tests/integration
mkdir -p tmp
```

#### Step 2: Create Backup
```bash
tar -czf backup_$(date +%Y%m%d_%H%M%S).tar.gz \
  --exclude=venv \
  --exclude=hybrid_surveyor/venv \
  --exclude=__pycache__ \
  --exclude=.git \
  .
```

#### Step 3: Move Files with Git

**For tracked files:**
```bash
git mv old_location.py new_location/file.py
```

**For untracked files:**
```bash
git add untracked_file.py
git mv untracked_file.py new_location/
```

**For documentation:**
```bash
git mv FEATURE_DOC.md docs/features/feature-doc.md
```

#### Step 4: Update Imports

**Before:**
```python
from improved_extractor import extract_data
from survey_normalizer import normalize_surveys
```

**After:**
```python
from src.extractors.improved_extractor import extract_data
from src.normalizers.survey_normalizer import normalize_surveys
```

#### Step 5: Update Template References

**Before:**
```python
render_template('simple_home.html')
```

**After:**
```python
render_template('simple/home.html')
```

#### Step 6: Test After Changes
```bash
# Run all tests
make test

# Test main app
python app.py

# Test CLI
python main.py status

# Run health checks
python healthcheck.py
```

#### Step 7: Update Documentation Links

**Files to update:**
- CLAUDE.md
- README.md
- DEVELOPER.md
- All docs with cross-references

### Rollback Procedure

**If issues occur:**
```bash
# Restore from backup
tar -xzf backup_YYYYMMDD_HHMMSS.tar.gz

# Or use git
git reset --hard HEAD
git clean -fd
```

---

## .gitignore Requirements

**Database Files:**
```gitignore
*.db
*.db-journal
survey_*.db
surveyor_*.db
```

**Temporary Files:**
```gitignore
tmp/
*.tmp
*.bak
```

**Environment Files:**
```gitignore
.env
*.env
!.env.example
```

**Python Files:**
```gitignore
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
```

**Testing:**
```gitignore
.pytest_cache/
.coverage
htmlcov/
```

**IDE:**
```gitignore
.vscode/
.idea/
*.swp
*.swo
.DS_Store
```

---

## Decision Tree for File Placement

### Is it a Python file?

**YES → Is it imported as a module?**
- YES → `src/` (by type: extractors, normalizers, analytics, services, utils)
- NO → Is it a script?
  - YES → `scripts/` (by purpose: deployment, database, testing)
  - NO → Is it an entry point?
    - YES → Root (app.py, main.py, railway_app.py)
    - NO → `tmp/` or DELETE

### Is it a Markdown file?

**YES → Is it CLAUDE.md or README.md?**
- YES → Root
- NO → Is it reference documentation?
  - YES → `docs/reference/`
  - NO → Is it feature documentation?
    - YES → `docs/features/`
    - NO → Is it about simple app?
      - YES → `docs/simple-app/`
      - NO → Is it about reports?
        - YES → `docs/reports/`
        - NO → Is it about development process?
          - YES → `docs/development/`
          - NO → Is it about deployment?
            - YES → `docs/deployment/`
            - NO → `docs/` (general)

### Is it an HTML file?

**YES → Is it a Jinja2 template?**
- YES → Is it for simple app?
  - YES → `templates/simple/`
  - NO → Is it for reports?
    - YES → `templates/reports/`
    - NO → `templates/` (main app)
- NO → DELETE or move to `static/` if static HTML

### Is it a test file?

**YES → Is it a unit test?**
- YES → `tests/unit/`
- NO → Is it an integration test?
  - YES → `tests/integration/`
  - NO → Is it a test script?
    - YES → `scripts/testing/`
    - NO → `tests/` (root of tests/)

### Is it a configuration file?

**YES → Is it project-level config?**
- YES → Root (requirements.txt, Procfile, Makefile, pyproject.toml, railway.toml)
- NO → Specific to a module?
  - YES → With that module in `src/`
  - NO → Root

---

## Examples

### Example 1: New Feature Module

**Feature:** Email notification service

**Files to Create:**
```
src/services/email_service.py          # Service module
tests/unit/test_email_service.py       # Unit tests
docs/features/email-notifications.md   # Documentation
```

**Not Acceptable:**
```
email_service.py                       # ❌ Root level
EMAIL_SERVICE.md                       # ❌ Root level
templates/email.html                   # ❌ If it's email template, use separate dir
```

### Example 2: New Report Type

**Feature:** PDF report generator

**Files to Create:**
```
src/services/pdf_generator.py          # Service module
templates/reports/pdf_template.html    # Template
docs/reports/pdf-generation.md         # Documentation
scripts/testing/test_pdf_generation.py # Test script
```

### Example 3: Deployment Script

**Feature:** Database migration script

**Files to Create:**
```
scripts/database/migrate_v2.py         # Migration script
docs/deployment/migration-v2.md        # Migration guide
```

**Not Acceptable:**
```
migrate_v2.py                          # ❌ Root level
MIGRATION_V2.md                        # ❌ Root level
```

---

## Validation

### Automated Checks

**Script to validate organization:**
```bash
#!/bin/bash
# scripts/utilities/validate_organization.sh

echo "Checking for misplaced Python files in root..."
find . -maxdepth 1 -name "*.py" -type f ! -name "app.py" ! -name "railway_app.py" ! -name "main.py"

echo "Checking for misplaced markdown files in root..."
find . -maxdepth 1 -name "*.md" -type f ! -name "README.md" ! -name "CLAUDE.md" ! -name "CHANGELOG.md"

echo "Checking for database files in git..."
git ls-files | grep "\.db$"

echo "Checking for proper __init__.py in packages..."
find src -type d -not -path "*/\.*" | while read dir; do
  if [ ! -f "$dir/__init__.py" ]; then
    echo "Missing __init__.py in $dir"
  fi
done
```

### Manual Review Checklist

- [ ] Root directory has 15 or fewer files
- [ ] All documentation is in `docs/`
- [ ] All modules are in `src/`
- [ ] All scripts are in `scripts/`
- [ ] All templates are in `templates/`
- [ ] All tests are in `tests/`
- [ ] No .db files are tracked in git
- [ ] All packages have __init__.py
- [ ] Import statements use `from src.*`
- [ ] Template references use subdirectories
- [ ] CLAUDE.md links are updated
- [ ] README.md links are updated

---

## Version History

### Version 1.0.0 (2025-10-11)

**Initial organization standard created**

**Context:**
- Project had 31 Python files in root
- 40+ markdown files in root
- Multiple feature sets (main app, simple app, reports)
- 24 untracked files from recent development

**Changes:**
- Defined directory structure
- Created file placement rules
- Documented naming conventions
- Added Flask-specific organization
- Created migration procedures
- Added validation tools

**Impact:**
- Reduces root directory from 71+ files to ~15 files
- Improves discoverability of documentation
- Enables better IDE navigation
- Simplifies import statements
- Maintains Flask conventions

---

## References

- [Flask Project Layout](https://flask.palletsprojects.com/en/2.3.x/tutorial/layout/)
- [Python Packaging Guide](https://packaging.python.org/en/latest/)
- [PEP 8 - Style Guide for Python Code](https://pep8.org/)
- [CLAUDE.md](../../CLAUDE.md) - AI agent instructions
- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture

---

**For questions or updates to this standard, please:**
1. Review current structure against this document
2. Propose changes via git branch
3. Update version history when approved
4. Update CLAUDE.md references

---

**Last Updated:** 2025-10-11
**Maintained by:** Project Team
**Next Review:** When adding major new features or subsystems
