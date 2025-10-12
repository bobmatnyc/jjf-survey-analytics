# Archived Database Files

This directory contains obsolete SQLite database files that are no longer used in production.

## Files Archived

- `simple_data.db` (236K) - Experimental simple app database
- `survey_normalized.db` (296K) - Old normalized survey data
- `surveyor_data_improved.db` (116K) - Improved extraction data format
- `surveyor_data.db` (140K) - Original extraction data format

## Why These Are Obsolete

1. **Production uses PostgreSQL** - The application now uses PostgreSQL on Railway, not SQLite
2. **Data is regenerable** - All data comes from Google Sheets and can be regenerated anytime
3. **Single Source of Truth** - Google Sheets are the single source of truth (see docs/architecture/SOT_ARCHITECTURE.md)
4. **Auto-regeneration** - Railway deployment automatically regenerates PostgreSQL from Google Sheets

## How to Regenerate Data

If you need local SQLite databases for development:

```bash
# Extract from Google Sheets
python improved_extractor.py

# Normalize the data
python survey_normalizer.py --auto
```

This will create fresh databases from the current Google Sheets data.

## Why Archived (Not Deleted)

These files are preserved for:
- Historical reference
- Potential data recovery if needed
- Understanding past data structures
- Development/testing purposes

**Note:** These files are gitignored and will not be committed to version control.

---

*Archived: 2025-10-12*
*Total size: ~788KB*
