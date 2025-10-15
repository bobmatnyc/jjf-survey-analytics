#!/usr/bin/env python3
"""
Railway initialization script

Runs database initialization and data sync when the app starts on Railway.
This ensures PostgreSQL is populated from Google Sheets on every deployment.
"""

import os
import sys
import logging
import subprocess
import time
import sqlite3
from init_database import create_database_tables, add_sample_data, verify_database

# Configure logging for Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def sync_data_from_google_sheets():
    """
    Extract data from Google Sheets and normalize to PostgreSQL.
    This makes PostgreSQL a disposable cache that auto-regenerates.
    """
    logger.info("=" * 60)
    logger.info("📊 AUTOMATIC DATA SYNC FROM GOOGLE SHEETS")
    logger.info("=" * 60)

    # Check if DATABASE_URL is set (indicates PostgreSQL)
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.info("⚠️  No DATABASE_URL found - skipping automatic sync")
        logger.info("   (Local development uses manual extraction)")
        return True

    logger.info("🐘 PostgreSQL detected - running automatic data sync")

    try:
        # Step 1: Extract data from Google Sheets
        logger.info("📥 Step 1/2: Extracting data from Google Sheets...")
        logger.info("   Source: 6 predefined JJF Technology Assessment spreadsheets")

        start_time = time.time()
        result = subprocess.run(
            [sys.executable, 'src/extractors/improved_extractor.py'],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode != 0:
            logger.error(f"❌ Extraction failed with code {result.returncode}")
            if result.stdout:
                logger.error("   === STDOUT ===")
                for line in result.stdout.split('\n'):
                    if line.strip():
                        logger.error(f"   {line}")
            if result.stderr:
                logger.error("   === STDERR ===")
                for line in result.stderr.split('\n'):
                    if line.strip():
                        logger.error(f"   {line}")
            # Continue anyway - app can start with empty or partial data
            return False

        extraction_time = time.time() - start_time
        logger.info(f"✅ Extraction completed in {extraction_time:.1f} seconds")
        if result.stdout:
            # Log last few lines of output
            output_lines = result.stdout.strip().split('\n')
            for line in output_lines[-5:]:
                logger.info(f"   {line}")

        # Step 2: Normalize data to PostgreSQL
        logger.info("🔄 Step 2/2: Normalizing data to PostgreSQL...")

        start_time = time.time()
        result = subprocess.run(
            [sys.executable, 'src/normalizers/survey_normalizer.py', '--auto'],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode != 0:
            logger.error(f"❌ Normalization failed with code {result.returncode}")
            if result.stdout:
                logger.error("   === STDOUT ===")
                for line in result.stdout.split('\n'):
                    if line.strip():
                        logger.error(f"   {line}")
            if result.stderr:
                logger.error("   === STDERR ===")
                for line in result.stderr.split('\n'):
                    if line.strip():
                        logger.error(f"   {line}")
            # Continue anyway - app can start with raw data only
            return False

        normalization_time = time.time() - start_time
        logger.info(f"✅ Normalization completed in {normalization_time:.1f} seconds")
        if result.stdout:
            # Log last few lines of output
            output_lines = result.stdout.strip().split('\n')
            for line in output_lines[-5:]:
                logger.info(f"   {line}")

        total_time = extraction_time + normalization_time
        logger.info("=" * 60)
        logger.info(f"🎉 AUTOMATIC DATA SYNC COMPLETED in {total_time:.1f} seconds")
        logger.info("   PostgreSQL is now populated from Google Sheets")
        logger.info("   Google Sheets remains the single source of truth")
        logger.info("=" * 60)

        return True

    except subprocess.TimeoutExpired:
        logger.error("❌ Data sync timed out after 5 minutes")
        logger.error("   App will start with empty database")
        return False
    except Exception as e:
        logger.error(f"❌ Data sync failed: {e}")
        logger.error("   App will start with empty database")
        return False


def railway_database_init():
    """Initialize database for Railway deployment."""

    logger.info("🚂 Railway Database Initialization")
    logger.info("=" * 40)

    # Check if we're running on Railway
    railway_env = os.getenv('RAILWAY_ENVIRONMENT')
    if railway_env:
        logger.info(f"✅ Running on Railway environment: {railway_env}")
    else:
        logger.info("⚠️ Not detected as Railway environment")
    
    # Check if databases already exist
    main_db = 'surveyor_data_improved.db'
    survey_db = 'survey_normalized.db'
    
    main_exists = os.path.exists(main_db)
    survey_exists = os.path.exists(survey_db)
    
    logger.info(f"📋 Database status:")
    logger.info(f"   {main_db}: {'exists' if main_exists else 'missing'}")
    logger.info(f"   {survey_db}: {'exists' if survey_exists else 'missing'}")
    
    # Initialize databases
    try:
        logger.info("🗄️ Creating database tables...")
        if create_database_tables():
            logger.info("✅ Database tables created")
        else:
            logger.error("❌ Failed to create database tables")
            return False
        
        # Add sample data if databases were empty
        if not main_exists or not survey_exists:
            logger.info("📊 Adding sample data...")
            if add_sample_data():
                logger.info("✅ Sample data added")
            else:
                logger.warning("⚠️ Failed to add sample data")
        
        # Verify setup
        logger.info("🔍 Verifying database setup...")
        if verify_database():
            logger.info("✅ Database verification passed")
        else:
            logger.error("❌ Database verification failed")
            return False
        
        # Auto-import local data if available and needed
        try:
            if os.path.exists('railway_data_import.sql'):
                logger.info("🔄 Checking if data import is needed...")

                # Check current data count
                with sqlite3.connect('surveyor_data_improved.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT COUNT(*) FROM spreadsheets')
                    current_count = cursor.fetchone()[0]

                    if current_count <= 1:  # Only has sample data
                        logger.info("📥 Auto-importing local data to Railway...")

                        # Import main database data
                        with open('railway_data_import.sql', 'r') as f:
                            sql_content = f.read()
                            statements = sql_content.split(';')
                            imported_statements = 0

                            for statement in statements:
                                statement = statement.strip()
                                if statement and not statement.startswith('--'):
                                    try:
                                        conn.execute(statement)
                                        imported_statements += 1
                                    except Exception as e:
                                        if 'already exists' not in str(e) and 'UNIQUE constraint failed' not in str(e):
                                            logger.warning(f"SQL import warning: {e}")

                            conn.commit()
                            logger.info(f"✅ Imported {imported_statements} SQL statements")

                        # Verify import
                        cursor.execute('SELECT COUNT(*) FROM spreadsheets')
                        new_spreadsheet_count = cursor.fetchone()[0]
                        cursor.execute('SELECT COUNT(*) FROM raw_data')
                        new_row_count = cursor.fetchone()[0]

                        logger.info(f"🎉 Data import completed: {new_spreadsheet_count} spreadsheets, {new_row_count} data rows")
                    else:
                        logger.info(f"📊 Railway already has {current_count} spreadsheets - skipping data import")
            else:
                logger.info("📋 No data import file found - using initialized sample data")

        except Exception as e:
            logger.error(f"❌ Data import error: {e}")
            # Continue anyway - the app should still work with sample data

        # NEW: Automatic data sync from Google Sheets (PostgreSQL only)
        logger.info("")
        sync_success = sync_data_from_google_sheets()
        if not sync_success:
            logger.warning("⚠️  Automatic data sync failed or was skipped")
            logger.warning("   App will continue with existing data")

        logger.info("")
        logger.info("🎉 Railway database initialization complete!")
        return True

    except Exception as e:
        logger.error(f"❌ Railway database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = railway_database_init()
    if not success:
        sys.exit(1)
