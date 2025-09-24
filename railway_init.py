#!/usr/bin/env python3
"""
Railway initialization script
Runs database initialization when the app starts on Railway
"""

import os
import sys
import logging
from init_database import create_database_tables, add_sample_data, verify_database

# Configure logging for Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

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
