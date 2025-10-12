# Archive Directory

This directory contains historical scripts that were used during initial project setup and migration but are no longer needed for ongoing operations.

## Contents

### deployment/
One-time deployment and fix scripts from the project's early phases. These scripts were used when manual Railway deployments were being tested.

**Current deployment method:** Railway GitHub auto-deployment (see DEPLOYMENT_GUIDE.md in root)

**Files:**
- `deploy-*.sh` - Various deployment attempt scripts (obsolete)
- `debug-railway.sh` - Railway debugging script (one-time use)
- `fix-*.sh` - One-time fix scripts
- `redeploy.sh`, `restore-full-app.sh` - Manual deployment scripts (obsolete)

### migration/
One-time scripts used to migrate from SQLite to PostgreSQL on Railway.

**Status:** Migration complete (October 2024)

**Files:**
- `migrate_sqlite_to_postgres.py` - Main migration script
- `export_data_for_railway.py` - Data export for migration
- `import_to_railway_postgres.py` - PostgreSQL import script
- `railway_import_data.py` - Railway data import
- `railway_data_import.sql` - Raw data SQL dump (65KB)
- `railway_survey_import.sql` - Survey data SQL dump (328KB)
- `init_database.py` - Initial database schema creation

### Backup Files
- `app_old.py` - Previous version of app.py (before refactoring)
- `backup_response.json` - Small test backup file
- `create_backup.py` - One-time backup script
- `data_backup.json` - Old backup data

---

**Note:** These files are preserved for historical reference but should NOT be used in current development or deployment workflows.
