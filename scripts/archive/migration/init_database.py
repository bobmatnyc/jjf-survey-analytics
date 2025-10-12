#!/usr/bin/env python3
"""
Initialize database for Railway deployment
Creates the necessary tables if they don't exist
"""

import sqlite3
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_database_tables():
    """Create the necessary database tables for the application."""
    
    # Database paths
    main_db = 'surveyor_data_improved.db'
    survey_db = 'survey_normalized.db'
    
    logger.info("🗄️ Initializing database tables...")
    
    # Create main database tables
    try:
        with sqlite3.connect(main_db) as conn:
            cursor = conn.cursor()
            
            # Create spreadsheets table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS spreadsheets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    spreadsheet_id TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    sheet_type TEXT,
                    url TEXT,
                    last_synced TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create raw_data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS raw_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    spreadsheet_id TEXT NOT NULL,
                    sheet_name TEXT,
                    row_data TEXT,
                    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (spreadsheet_id) REFERENCES spreadsheets (spreadsheet_id)
                )
            ''')
            
            # Create extraction_jobs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS extraction_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    error_message TEXT,
                    records_processed INTEGER DEFAULT 0
                )
            ''')
            
            conn.commit()
            logger.info(f"✅ Main database tables created: {main_db}")
            
    except Exception as e:
        logger.error(f"❌ Failed to create main database: {e}")
        return False
    
    # Create survey database tables
    try:
        with sqlite3.connect(survey_db) as conn:
            cursor = conn.cursor()
            
            # Create surveys table (matching survey_normalized.db schema)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS surveys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    survey_name TEXT NOT NULL,
                    survey_type TEXT NOT NULL,
                    spreadsheet_id TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(spreadsheet_id)
                )
            ''')

            # Create survey_questions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS survey_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    survey_id INTEGER NOT NULL,
                    question_key TEXT NOT NULL,
                    question_text TEXT,
                    question_type TEXT DEFAULT 'text',
                    question_order INTEGER,
                    is_required BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (survey_id) REFERENCES surveys (id)
                )
            ''')

            # Create respondents table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS respondents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    respondent_id TEXT UNIQUE NOT NULL,
                    email TEXT,
                    name TEXT,
                    organization TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create survey_responses table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS survey_responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    survey_id INTEGER NOT NULL,
                    respondent_id INTEGER NOT NULL,
                    response_date TIMESTAMP NOT NULL,
                    completion_status TEXT DEFAULT 'complete',
                    response_duration_seconds INTEGER,
                    source_row_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (survey_id) REFERENCES surveys (id),
                    FOREIGN KEY (respondent_id) REFERENCES respondents (id)
                )
            ''')

            # Create survey_answers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS survey_answers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    response_id INTEGER NOT NULL,
                    question_id INTEGER NOT NULL,
                    answer_text TEXT,
                    answer_value REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (response_id) REFERENCES survey_responses (id),
                    FOREIGN KEY (question_id) REFERENCES survey_questions (id)
                )
            ''')
            
            conn.commit()
            logger.info(f"✅ Survey database tables created: {survey_db}")
            
    except Exception as e:
        logger.error(f"❌ Failed to create survey database: {e}")
        return False
    
    return True

def add_sample_data():
    """Add some sample data for testing."""
    
    logger.info("📊 Adding sample data...")
    
    try:
        with sqlite3.connect('surveyor_data_improved.db') as conn:
            cursor = conn.cursor()
            
            # Add sample spreadsheet
            cursor.execute('''
                INSERT OR IGNORE INTO spreadsheets 
                (spreadsheet_id, title, sheet_type, url, last_synced)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                'sample_sheet_001',
                'Sample Survey Data',
                'survey',
                'https://docs.google.com/spreadsheets/d/sample',
                datetime.now()
            ))
            
            # Add sample raw data
            cursor.execute('''
                INSERT OR IGNORE INTO raw_data 
                (spreadsheet_id, sheet_name, row_data)
                VALUES (?, ?, ?)
            ''', (
                'sample_sheet_001',
                'Sheet1',
                '{"question": "How satisfied are you?", "answer": "Very satisfied", "timestamp": "2025-01-23"}'
            ))
            
            # Add sample extraction job
            cursor.execute('''
                INSERT OR IGNORE INTO extraction_jobs 
                (job_type, status, records_processed)
                VALUES (?, ?, ?)
            ''', (
                'initial_setup',
                'completed',
                1
            ))
            
            conn.commit()
            logger.info("✅ Sample data added")
            
    except Exception as e:
        logger.error(f"❌ Failed to add sample data: {e}")
        return False
    
    return True

def verify_database():
    """Verify that the database is set up correctly."""
    
    logger.info("🔍 Verifying database setup...")
    
    databases = [
        ('surveyor_data_improved.db', ['spreadsheets', 'raw_data', 'extraction_jobs']),
        ('survey_normalized.db', ['surveys', 'survey_questions', 'respondents', 'survey_responses', 'survey_answers'])
    ]
    
    for db_path, expected_tables in databases:
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Get list of tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                logger.info(f"📋 {db_path} tables: {tables}")
                
                # Check if expected tables exist
                missing_tables = [table for table in expected_tables if table not in tables]
                if missing_tables:
                    logger.warning(f"⚠️ Missing tables in {db_path}: {missing_tables}")
                else:
                    logger.info(f"✅ All expected tables present in {db_path}")
                
                # Count records in each table
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    logger.info(f"   {table}: {count} records")
                    
        except Exception as e:
            logger.error(f"❌ Failed to verify {db_path}: {e}")
            return False
    
    return True

if __name__ == '__main__':
    logger.info("🚀 Database Initialization Script")
    logger.info("=" * 40)
    
    # Create tables
    if create_database_tables():
        logger.info("✅ Database tables created successfully")
    else:
        logger.error("❌ Failed to create database tables")
        exit(1)
    
    # Add sample data
    if add_sample_data():
        logger.info("✅ Sample data added successfully")
    else:
        logger.error("❌ Failed to add sample data")
    
    # Verify setup
    if verify_database():
        logger.info("✅ Database verification completed")
    else:
        logger.error("❌ Database verification failed")
    
    logger.info("")
    logger.info("🎉 Database initialization complete!")
    logger.info("The application should now work without database errors.")
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Deploy to Railway")
    logger.info("2. Test the application")
    logger.info("3. Add real survey data using the data extractors")
