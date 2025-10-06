# Single Source of Truth Architecture

**Last Updated:** 2025-10-06
**Status:** ✅ Implemented and Verified

---

## Overview

The JJF Survey Analytics Platform implements a **Single Source of Truth (SOT)** architecture where Google Sheets are the authoritative data source and all databases serve as disposable, regeneratable caches.

---

## Architecture Principles

### 1. Google Sheets = Truth
- All survey data originates from Google Sheets
- Google Sheets URLs are hardcoded as data sources
- No application writes back to Google Sheets
- Sheets are publicly accessible (read-only CSV export)

### 2. Databases = Cache
- SQLite (local) and PostgreSQL (production) are temporary data stores
- Databases can be deleted without data loss
- Databases regenerate automatically from Google Sheets
- No migration scripts needed - schema recreated on demand

### 3. One-Way Data Flow
```
Google Sheets (READ) → Extract → Raw DB → Normalize → Normalized DB → UI (READ)
```
- No reverse flow exists
- No user actions create authoritative data
- All data traces back to Google Sheets

---

## Implementation Details

### Database Abstraction Layer

**File:** `db_utils.py`

Provides unified interface for both SQLite and PostgreSQL:
- Automatic environment detection via `DATABASE_URL`
- SQL syntax adaptation (SQLite ↔ PostgreSQL)
- Connection management
- Parameter placeholder handling

### Extraction Process

**File:** `improved_extractor.py`

Extracts from 6 predefined Google Sheets:
1. Detects database type (SQLite vs PostgreSQL)
2. Fetches CSV exports via HTTP GET (read-only)
3. Parses and stores in raw database tables
4. Logs extraction job status

**Key Point:** Zero write operations to Google Sheets

### Normalization Process

**File:** `survey_normalizer.py`

Transforms raw data into relational structure:
1. Reads from raw database
2. Identifies survey types and questions
3. Creates normalized relational schema
4. Handles both SQLite and PostgreSQL

**Key Point:** No direct Google Sheets interaction

### Auto-Sync Service

**File:** `auto_sync_service.py`

Monitors for changes and re-normalizes:
- Detects database type (SQLite or PostgreSQL)
- Monitors raw database for changes
- Triggers normalization when changes detected
- Runs every 5 minutes

**Key Point:** Does NOT re-extract from Sheets (extraction is startup/manual)

### Railway Deployment

**File:** `railway_init.py`

Automatically regenerates PostgreSQL on deployment:
1. Detects `DATABASE_URL` (PostgreSQL mode)
2. Runs `improved_extractor.py` (5-minute timeout)
3. Runs `survey_normalizer.py --auto` (5-minute timeout)
4. Logs progress and errors
5. Continues even if sync fails (graceful degradation)

**Key Point:** Every deployment gets fresh data from Google Sheets

---

## Database Regeneration

### Local Development (SQLite)

```bash
# Delete databases (safe - data in Google Sheets)
rm surveyor_data_improved.db survey_normalized.db

# Regenerate from Google Sheets
python improved_extractor.py
python survey_normalizer.py --auto

# Resume development
python app.py
```

### Production (PostgreSQL on Railway)

**Automatic (Preferred):**
```bash
# Push to GitHub - Railway auto-deploys and regenerates
git push origin master
```

**Manual:**
```bash
# Restart service - triggers regeneration
railway restart

# Or run commands directly
railway run python improved_extractor.py
railway run python survey_normalizer.py --auto
```

**Emergency:**
```bash
# Delete PostgreSQL database
railway database delete

# Redeploy to regenerate
railway up
```

---

## Compliance Verification

### Zero Writes to Google Sheets

```bash
# Search entire codebase - should return ZERO results
grep -r "sheet.append\|sheet.update\|worksheet.*append\|worksheet.*update" *.py
```

**Expected:** No matches found ✅

### Databases Are Gitignored

```bash
# Check .gitignore
cat .gitignore | grep "*.db"
```

**Expected:** `*.db` is ignored ✅

### Full Refresh Strategy

All sync operations delete and recreate:
- `improved_extractor.py`: `DELETE FROM raw_data WHERE spreadsheet_id = ?`
- `survey_normalizer.py`: `DROP TABLE IF EXISTS` + `CREATE TABLE`

**Expected:** No incremental updates ✅

---

## Data Source Configuration

### Google Sheets URLs (Hardcoded)

**File:** `improved_extractor.py` (lines 51-103)

```python
DEFAULT_URLS = {
    # Survey URLs (2)
    'https://docs.google.com/spreadsheets/d/.../export?format=csv',
    'https://docs.google.com/spreadsheets/d/.../export?format=csv',

    # Technology Assessment URLs (3)
    'https://docs.google.com/spreadsheets/d/.../export?format=csv',
    'https://docs.google.com/spreadsheets/d/.../export?format=csv',
    'https://docs.google.com/spreadsheets/d/.../export?format=csv',

    # Health Safety Inventory URL (1)
    'https://docs.google.com/spreadsheets/d/.../export?format=csv'
}
```

**To update data sources:** Modify `DEFAULT_URLS` in `improved_extractor.py`

---

## Benefits of SOT Architecture

### For Development
✅ No database migrations needed
✅ Easy to reset to clean state
✅ Test with real data anytime
✅ No risk of data corruption
✅ Schema changes are simple

### For Operations
✅ No database backups needed (data in Sheets)
✅ Easy disaster recovery (regenerate from Sheets)
✅ No data drift between environments
✅ Deployments are stateless
✅ Can recreate production data locally

### For Data Integrity
✅ Single authoritative source
✅ No synchronization conflicts
✅ Audit trail in Google Sheets version history
✅ Non-technical users can edit data
✅ Changes automatically propagate

---

## Common Questions

**Q: What if Google Sheets are unavailable?**
A: Application continues with cached data. Auto-sync logs errors. Manual sync available when Sheets return.

**Q: How long does regeneration take?**
A: ~60-90 seconds for full extraction and normalization.

**Q: Can I modify data in the database directly?**
A: Technically yes, but changes will be lost on next sync. Always edit Google Sheets.

**Q: What if I need to add a new survey?**
A: Add Google Sheets URL to `DEFAULT_URLS` in `improved_extractor.py` and redeploy.

**Q: How do I know if data is stale?**
A: Check `/sync` dashboard for last sync time. Auto-sync runs every 5 minutes.

**Q: Can I use a different database?**
A: Yes - update `db_utils.py` connection logic. MySQL, SQLite, PostgreSQL all supported via SQLAlchemy patterns.

---

## Files Modified for SOT Implementation

1. **NEW: db_utils.py** - Database abstraction layer
2. **MODIFIED: improved_extractor.py** - PostgreSQL support
3. **MODIFIED: survey_normalizer.py** - PostgreSQL support
4. **MODIFIED: auto_sync_service.py** - Database type detection
5. **MODIFIED: railway_init.py** - Automatic sync on startup

---

## Validation Checklist

Before deployment, verify:

- [ ] Google Sheets URLs are accessible (public)
- [ ] No write operations to Sheets in codebase
- [ ] Databases are gitignored
- [ ] `railway_init.py` runs extraction on startup
- [ ] Auto-sync service detects correct database type
- [ ] Manual regeneration works locally
- [ ] Production regeneration works on Railway

---

## Monitoring

**Health Check Endpoint:** `/health`

**Auto-Sync Dashboard:** `/sync`

**Logs to Monitor:**
- Extraction job status
- Normalization completion
- Sync service status
- Database connection errors

---

**Built with Google Sheets as the single source of truth.**
**Databases are disposable. Data is eternal.**
