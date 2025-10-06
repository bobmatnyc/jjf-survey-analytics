#!/usr/bin/env python3
"""
Migrate SQLite data to PostgreSQL on Railway

This script reads data from local SQLite databases and imports it to Railway PostgreSQL.

Usage:
  # Upload local databases to Railway and run migration
  railway shell python migrate_sqlite_to_postgres.py

  # Or commit databases and run on Railway
  git add *.db migrate_sqlite_to_postgres.py
  git commit -m "Add survey data"
  railway up
  railway shell python migrate_sqlite_to_postgres.py
"""

import sqlite3
import os
import sys
from datetime import datetime

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("Installing psycopg2-binary...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'psycopg2-binary'])
    import psycopg2
    import psycopg2.extras

def migrate_data():
    """Migrate all data from SQLite to PostgreSQL."""

    # Check if DATABASE_URL is set (Railway environment)
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL not set.")
        print("   Run with: railway shell python migrate_sqlite_to_postgres.py")
        sys.exit(1)

    print("🔄 SQLite to PostgreSQL Migration")
    print("=" * 50)

    # Check source databases exist
    source_dbs = {
        'surveyor_data_improved.db': ['spreadsheets', 'raw_data', 'extraction_jobs'],
        'survey_normalized.db': ['surveys', 'survey_questions', 'respondents', 'survey_responses', 'survey_answers']
    }

    missing_dbs = [db for db in source_dbs.keys() if not os.path.exists(db)]
    if missing_dbs:
        print(f"❌ Missing source databases: {missing_dbs}")
        print("   Please run 'make build' first to create the databases locally")
        sys.exit(1)

    # Connect to PostgreSQL
    print(f"🐘 Connecting to PostgreSQL...")
    try:
        pg_conn = psycopg2.connect(database_url)
        pg_conn.autocommit = False  # Use explicit transactions
        pg_cursor = pg_conn.cursor()
        print("✅ Connected to PostgreSQL")
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        sys.exit(1)

    # Define boolean columns for type casting
    boolean_columns = {
        'survey_questions': ['is_required'],
        'survey_answers': ['answer_boolean', 'is_empty']
    }

    total_migrated = 0

    # Migrate each database
    for db_path, tables in source_dbs.items():
        print(f"\n📊 Migrating {db_path}...")

        try:
            sqlite_conn = sqlite3.connect(db_path)
            sqlite_conn.row_factory = sqlite3.Row
            sqlite_cursor = sqlite_conn.cursor()

            for table in tables:
                print(f"  📋 Migrating table: {table}")

                # Get row count from SQLite
                sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = sqlite_cursor.fetchone()[0]

                if row_count == 0:
                    print(f"    ⚠️  No data in {table}")
                    continue

                print(f"    📊 Source rows: {row_count}")

                # Get all data from SQLite
                sqlite_cursor.execute(f"SELECT * FROM {table}")
                rows = sqlite_cursor.fetchall()

                if not rows:
                    continue

                # Get column names
                columns = [desc[0] for desc in sqlite_cursor.description]

                # Clear existing data in PostgreSQL table using TRUNCATE CASCADE
                try:
                    pg_cursor.execute(f"TRUNCATE TABLE {table} CASCADE")
                    pg_conn.commit()
                    print(f"    🗑️  Cleared existing data from {table}")
                except Exception as e:
                    print(f"    ⚠️  Could not truncate table: {e}")
                    # Try DELETE as fallback
                    try:
                        pg_cursor.execute(f"DELETE FROM {table}")
                        pg_conn.commit()
                        print(f"    🗑️  Deleted existing data from {table}")
                    except Exception as e2:
                        print(f"    ⚠️  Could not clear table (may not exist): {e2}")
                        pg_conn.rollback()

                # Insert data into PostgreSQL
                migrated_count = 0
                error_count = 0

                for row in rows:
                    # Convert row to dict
                    row_dict = dict(row)

                    # Build INSERT statement
                    placeholders = ', '.join(['%s'] * len(columns))
                    columns_str = ', '.join([f'"{col}"' for col in columns])

                    # Process values with boolean casting
                    processed_values = []
                    for i, col in enumerate(columns):
                        val = row_dict[col]

                        # Handle None/NULL values
                        if val is None:
                            processed_values.append(None)
                        # Cast SQLite INTEGER booleans to PostgreSQL BOOLEAN
                        elif table in boolean_columns and col in boolean_columns[table]:
                            # SQLite stores booleans as INTEGER (0/1)
                            processed_values.append(bool(val) if val is not None else False)
                        # Preserve datetime objects
                        elif isinstance(val, datetime):
                            processed_values.append(val)
                        else:
                            processed_values.append(val)

                    try:
                        pg_cursor.execute(
                            f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})",
                            processed_values
                        )
                        migrated_count += 1
                    except Exception as e:
                        error_count += 1
                        if error_count <= 3:  # Only show first 3 errors
                            print(f"    ⚠️  Error inserting row {migrated_count + error_count}: {e}")
                        # Continue with next row instead of failing completely
                        pg_conn.rollback()
                        continue

                # Commit after each table to prevent full rollback
                try:
                    pg_conn.commit()
                    print(f"    ✅ Migrated {migrated_count} rows")
                    if error_count > 0:
                        print(f"    ⚠️  Skipped {error_count} rows due to errors")
                    total_migrated += migrated_count
                except Exception as e:
                    print(f"    ❌ Error committing table {table}: {e}")
                    pg_conn.rollback()

            sqlite_conn.close()

        except Exception as e:
            print(f"  ❌ Error migrating {db_path}: {e}")
            import traceback
            traceback.print_exc()
            pg_conn.rollback()

    # Verify migration
    print(f"\n🔍 Verifying migration...")
    verification_tables = [
        'spreadsheets', 'raw_data', 'extraction_jobs',
        'surveys', 'survey_questions', 'respondents',
        'survey_responses', 'survey_answers'
    ]

    try:
        for table in verification_tables:
            try:
                pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = pg_cursor.fetchone()[0]
                if count > 0:
                    print(f"  ✅ {table}: {count} rows")
                else:
                    print(f"  ⚠️  {table}: 0 rows")
            except Exception as e:
                print(f"  ❌ {table}: Error - {e}")

        # Check critical tables
        pg_cursor.execute("SELECT COUNT(*) FROM surveys")
        surveys_count = pg_cursor.fetchone()[0]

        pg_cursor.execute("SELECT COUNT(*) FROM survey_responses")
        responses_count = pg_cursor.fetchone()[0]

        if surveys_count > 0 and responses_count > 0:
            print("\n🎉 Migration completed successfully!")
            print(f"📊 Total rows migrated: {total_migrated}")
        else:
            print("\n⚠️  Migration completed but no survey data found")
            print(f"📊 Total rows migrated: {total_migrated}")

    except Exception as e:
        print(f"  ❌ Verification error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        pg_conn.close()

if __name__ == '__main__':
    migrate_data()
