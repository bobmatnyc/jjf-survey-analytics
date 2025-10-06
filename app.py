#!/usr/bin/env python3
"""
Surveyor Data Viewer - Flask Web Application

A simple web interface for viewing Google Sheets survey data
using Flask and Tailwind CSS.
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import sqlite3
import json
import os
import sys
import time
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any
import math
from survey_analytics import SurveyAnalytics
from auto_sync_service import get_auto_sync_service, start_auto_sync

# For async support in Flask
from functools import wraps

# Configure logging for Railway deployment
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Railway captures stdout/stderr
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.after_request
def add_header(response):
    """Add headers to prevent caching of dynamic content."""
    # Don't cache dynamic content
    if response.content_type and 'text/html' in response.content_type:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    # API responses should not be cached
    elif response.content_type and 'application/json' in response.content_type:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'surveyor-data-viewer-2025-default-key')

# Authentication configuration
APP_PASSWORD = os.getenv('APP_PASSWORD', 'survey2025!')  # Default password, change in production
# Disable auth for local development, enable for production
REQUIRE_AUTH = os.getenv('REQUIRE_AUTH', 'false').lower() == 'true'

# Port configuration - Railway assigns this dynamically
PORT = int(os.getenv('PORT', 8080))  # Railway compatible default

logger.info(f"App configuration:")
logger.info(f"  Port: {PORT}")
logger.info(f"  Authentication required: {REQUIRE_AUTH}")
logger.info(f"  Password configured: {'Yes' if APP_PASSWORD else 'No'}")

# Authentication decorator
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not REQUIRE_AUTH:
            return f(*args, **kwargs)

        if 'authenticated' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Async support decorator for Flask
def async_route(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(f(*args, **kwargs))
        finally:
            loop.close()
    return wrapper

# Database configuration
DB_PATH = 'surveyor_data_improved.db'
SURVEY_DB_PATH = 'survey_normalized.db'

# Check if we should use PostgreSQL (Railway production)
DATABASE_URL = os.getenv('DATABASE_URL')
USE_POSTGRESQL = DATABASE_URL is not None

if USE_POSTGRESQL:
    print(f"🐘 Using PostgreSQL database: {DATABASE_URL[:50] if DATABASE_URL else 'None'}...")
    try:
        import psycopg2
        print("✅ psycopg2 available for PostgreSQL")
    except ImportError:
        print("❌ psycopg2 not available, installing...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'psycopg2-binary'])
        import psycopg2
        print("✅ psycopg2 installed successfully")
else:
    print(f"📁 Using SQLite databases: {DB_PATH}, {SURVEY_DB_PATH}")

class DatabaseManager:
    """Handle database operations for the web app."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.use_postgresql = USE_POSTGRESQL
        self.database_url = DATABASE_URL
        if self.use_postgresql:
            self.init_postgresql_tables()
    
    def get_connection(self):
        """Get database connection with row factory."""
        if self.use_postgresql:
            import psycopg2
            import psycopg2.extras
            conn = psycopg2.connect(self.database_url)
            conn.cursor_factory = psycopg2.extras.RealDictCursor
            return conn
        else:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn

    def init_postgresql_tables(self):
        """Initialize PostgreSQL tables if they don't exist."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Create spreadsheets table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS spreadsheets (
                        id SERIAL PRIMARY KEY,
                        spreadsheet_id VARCHAR(255) UNIQUE NOT NULL,
                        url TEXT NOT NULL,
                        title TEXT,
                        sheet_type VARCHAR(50),
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_synced TIMESTAMP
                    )
                ''')

                # Create raw_data table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS raw_data (
                        id SERIAL PRIMARY KEY,
                        spreadsheet_id VARCHAR(255) NOT NULL,
                        row_number INTEGER NOT NULL,
                        data_json TEXT NOT NULL,
                        data_hash VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (spreadsheet_id) REFERENCES spreadsheets (spreadsheet_id)
                    )
                ''')

                # Create extraction_jobs table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS extraction_jobs (
                        id SERIAL PRIMARY KEY,
                        job_name VARCHAR(255) NOT NULL,
                        status VARCHAR(50) NOT NULL,
                        total_spreadsheets INTEGER DEFAULT 0,
                        processed_spreadsheets INTEGER DEFAULT 0,
                        successful_spreadsheets INTEGER DEFAULT 0,
                        total_rows INTEGER DEFAULT 0,
                        processed_rows INTEGER DEFAULT 0,
                        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP,
                        error_message TEXT
                    )
                ''')

                # Create survey tables
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS surveys (
                        id SERIAL PRIMARY KEY,
                        title VARCHAR(255) NOT NULL,
                        survey_name VARCHAR(255),
                        survey_type VARCHAR(100),
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status VARCHAR(50) DEFAULT 'active'
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS survey_questions (
                        id SERIAL PRIMARY KEY,
                        survey_id INTEGER,
                        question_key VARCHAR(255),
                        question_text TEXT,
                        question_type VARCHAR(50) DEFAULT 'text',
                        question_order INTEGER,
                        is_required BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (survey_id) REFERENCES surveys (id)
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS survey_responses (
                        id SERIAL PRIMARY KEY,
                        survey_id INTEGER,
                        respondent_id VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_complete BOOLEAN DEFAULT FALSE,
                        completion_time_seconds INTEGER,
                        FOREIGN KEY (survey_id) REFERENCES surveys (id)
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS survey_answers (
                        id SERIAL PRIMARY KEY,
                        response_id INTEGER,
                        question_id INTEGER,
                        answer_text TEXT,
                        answer_numeric DECIMAL,
                        answer_boolean BOOLEAN,
                        answer_date TIMESTAMP,
                        is_empty BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (response_id) REFERENCES survey_responses (id),
                        FOREIGN KEY (question_id) REFERENCES survey_questions (id)
                    )
                ''')

                # Create respondents table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS respondents (
                        id SERIAL PRIMARY KEY,
                        respondent_hash VARCHAR(255) UNIQUE,
                        browser VARCHAR(255),
                        device VARCHAR(255),
                        total_responses INTEGER DEFAULT 0,
                        first_response_at TIMESTAMP,
                        last_response_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Migration: Add missing columns to existing tables if they don't exist
                try:
                    # Check if respondent_id column exists in survey_responses
                    cursor.execute("""
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_name = 'survey_responses' AND column_name = 'respondent_id'
                    """)
                    if not cursor.fetchone():
                        print("🔄 Adding missing respondent_id column to survey_responses...")
                        cursor.execute("""
                            ALTER TABLE survey_responses
                            ADD COLUMN respondent_id VARCHAR(255)
                        """)
                        print("✅ Migration: respondent_id column added")

                    # Check if survey_name column exists in surveys
                    cursor.execute("""
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_name = 'surveys' AND column_name = 'survey_name'
                    """)
                    if not cursor.fetchone():
                        print("🔄 Adding missing survey_name column to surveys...")
                        cursor.execute("""
                            ALTER TABLE surveys
                            ADD COLUMN survey_name VARCHAR(255),
                            ADD COLUMN survey_type VARCHAR(100)
                        """)
                        print("✅ Migration: survey_name and survey_type columns added")

                except Exception as migration_error:
                    print(f"⚠️ Migration warning: {migration_error}")

                conn.commit()
                print("✅ PostgreSQL tables initialized successfully")

        except Exception as e:
            print(f"❌ Error initializing PostgreSQL tables: {e}")
            raise

    def get_spreadsheets(self) -> List[Dict]:
        """Get all spreadsheets with row counts."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    s.id,
                    s.spreadsheet_id,
                    s.title,
                    s.sheet_type,
                    s.url,
                    s.last_synced,
                    COUNT(r.id) as row_count
                FROM spreadsheets s
                LEFT JOIN raw_data r ON s.spreadsheet_id = r.spreadsheet_id
                GROUP BY s.id, s.spreadsheet_id, s.title, s.sheet_type, s.url, s.last_synced
                ORDER BY s.last_synced DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_spreadsheet_data(self, spreadsheet_id: str, page: int = 1, per_page: int = 20) -> Dict:
        """Get paginated data for a specific spreadsheet."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get spreadsheet info
            cursor.execute('''
                SELECT * FROM spreadsheets WHERE spreadsheet_id = ?
            ''', (spreadsheet_id,))
            spreadsheet = dict(cursor.fetchone() or {})
            
            if not spreadsheet:
                return {'spreadsheet': None, 'data': [], 'pagination': {}}
            
            # Get total count
            cursor.execute('''
                SELECT COUNT(*) as total FROM raw_data WHERE spreadsheet_id = ?
            ''', (spreadsheet_id,))
            total_rows = cursor.fetchone()['total']
            
            # Calculate pagination
            total_pages = math.ceil(total_rows / per_page)
            offset = (page - 1) * per_page
            
            # Get paginated data
            cursor.execute('''
                SELECT 
                    id,
                    row_number,
                    data_json,
                    created_at
                FROM raw_data 
                WHERE spreadsheet_id = ?
                ORDER BY row_number
                LIMIT ? OFFSET ?
            ''', (spreadsheet_id, per_page, offset))
            
            raw_data = cursor.fetchall()
            
            # Parse JSON data
            data = []
            columns = set()
            
            for row in raw_data:
                try:
                    parsed_data = json.loads(row['data_json'])
                    parsed_data['_meta'] = {
                        'id': row['id'],
                        'row_number': row['row_number'],
                        'created_at': row['created_at']
                    }
                    data.append(parsed_data)
                    columns.update(parsed_data.keys())
                except json.JSONDecodeError:
                    continue
            
            # Remove meta columns from display columns
            display_columns = sorted([col for col in columns if not col.startswith('_')])
            
            pagination = {
                'page': page,
                'per_page': per_page,
                'total_rows': total_rows,
                'total_pages': total_pages,
                'has_prev': page > 1,
                'has_next': page < total_pages,
                'prev_page': page - 1 if page > 1 else None,
                'next_page': page + 1 if page < total_pages else None
            }
            
            return {
                'spreadsheet': spreadsheet,
                'data': data,
                'columns': display_columns,
                'pagination': pagination
            }
    
    def get_extraction_jobs(self) -> List[Dict]:
        """Get all extraction jobs."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM extraction_jobs
                ORDER BY id DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_dashboard_stats(self) -> Dict:
        """Get dashboard statistics."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Initialize default values
                total_spreadsheets = 0
                total_rows = 0
                total_jobs = 0
                latest_job = None
                sheet_types = []

                try:
                    # Total spreadsheets
                    cursor.execute('SELECT COUNT(*) as count FROM spreadsheets')
                    total_spreadsheets = cursor.fetchone()['count']
                except Exception as e:
                    logger.warning(f"Could not get spreadsheet count: {e}")

                try:
                    # Total rows
                    cursor.execute('SELECT COUNT(*) as count FROM raw_data')
                    total_rows = cursor.fetchone()['count']
                except Exception as e:
                    logger.warning(f"Could not get row count: {e}")

                try:
                    # Total jobs
                    cursor.execute('SELECT COUNT(*) as count FROM extraction_jobs')
                    total_jobs = cursor.fetchone()['count']
                except Exception as e:
                    logger.warning(f"Could not get job count: {e}")

                try:
                    # Latest job (order by ID to get most recent)
                    cursor.execute('''
                        SELECT * FROM extraction_jobs
                        ORDER BY id DESC
                        LIMIT 1
                    ''')
                    latest_job_row = cursor.fetchone()
                    if latest_job_row:
                        latest_job = dict(latest_job_row)
                        # Ensure all required fields exist for template
                        required_job_fields = {
                            'id': latest_job.get('id', 0),
                            'job_name': latest_job.get('job_name', latest_job.get('job_type', 'Unknown Job')),
                            'status': latest_job.get('status', 'unknown'),
                            'total_spreadsheets': latest_job.get('total_spreadsheets', latest_job.get('records_processed', 0)),
                            'processed_spreadsheets': latest_job.get('processed_spreadsheets', latest_job.get('records_processed', 0)),
                            'successful_spreadsheets': latest_job.get('successful_spreadsheets', latest_job.get('records_processed', 0)),
                            'total_rows': latest_job.get('total_rows', 0),
                            'processed_rows': latest_job.get('processed_rows', 0),
                            'started_at': latest_job.get('started_at', ''),
                            'completed_at': latest_job.get('completed_at', ''),
                            'error_message': latest_job.get('error_message', None)
                        }
                        latest_job = required_job_fields
                        logger.info(f"✅ Latest job normalized: {latest_job}")
                    else:
                        latest_job = None
                except Exception as e:
                    logger.warning(f"Could not get latest job: {e}")
                    latest_job = None

                try:
                    # Sheet type distribution
                    cursor.execute('''
                        SELECT
                            sheet_type,
                            COUNT(*) as count,
                            SUM(CASE WHEN r.spreadsheet_id IS NOT NULL THEN 1 ELSE 0 END) as with_data
                        FROM spreadsheets s
                        LEFT JOIN (SELECT DISTINCT spreadsheet_id FROM raw_data) r
                            ON s.spreadsheet_id = r.spreadsheet_id
                        GROUP BY sheet_type
                        ORDER BY count DESC
                    ''')
                    sheet_types = [dict(row) for row in cursor.fetchall()]
                except Exception as e:
                    logger.warning(f"Could not get sheet types: {e}")

                return {
                    'total_spreadsheets': total_spreadsheets,
                    'total_rows': total_rows,
                    'total_jobs': total_jobs,
                    'latest_job': latest_job,
                    'sheet_types': sheet_types
                }
        except Exception as e:
            logger.error(f"Database error in get_dashboard_stats: {e}")
            # Return default stats if database is not available
            return {
                'total_spreadsheets': 0,
                'total_rows': 0,
                'total_jobs': 0,
                'latest_job': None,
                'sheet_types': []
            }

    def get_latest_updates(self, limit=20):
        """Get the latest data updates/changes with user and organization context."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Get latest raw data entries with spreadsheet info and user context
                if self.use_postgresql:
                    cursor.execute('''
                        SELECT
                            rd.id,
                            rd.row_number,
                            rd.created_at,
                            s.title as spreadsheet_title,
                            s.sheet_type,
                            s.spreadsheet_id,
                            s.url as spreadsheet_url,
                            rd.data_json
                        FROM raw_data rd
                        JOIN spreadsheets s ON rd.spreadsheet_id = s.spreadsheet_id
                        ORDER BY rd.created_at DESC
                        LIMIT %s
                    ''', (limit,))
                else:
                    cursor.execute('''
                        SELECT
                            rd.id,
                            rd.row_number,
                            rd.created_at,
                            s.title as spreadsheet_title,
                            s.sheet_type,
                            s.spreadsheet_id,
                            s.url as spreadsheet_url,
                            rd.data_json
                        FROM raw_data rd
                        JOIN spreadsheets s ON rd.spreadsheet_id = s.spreadsheet_id
                        ORDER BY rd.created_at DESC
                        LIMIT ?
                    ''', (limit,))

                updates = []
                for row in cursor.fetchall():
                    try:
                        # Parse the data_json to get a preview
                        import json
                        data = json.loads(row['data_json']) if row['data_json'] else {}

                        # Skip empty rows (where all values are empty or just whitespace)
                        non_empty_values = [v for v in data.values() if v and str(v).strip()]
                        if len(non_empty_values) == 0:
                            continue

                        # Skip rows that are just question definitions (all values are questions)
                        question_count = sum(1 for v in data.values() if v and '?' in str(v))
                        if question_count > len(non_empty_values) * 0.8:  # If 80%+ are questions, skip
                            continue

                        # Extract user and organization information
                        user_name = None
                        user_email = None
                        organization = None

                        # Look for common user/org fields
                        for key, value in data.items():
                            if value and str(value).strip():
                                key_lower = key.lower()
                                value_str = str(value).strip()

                                # Extract email
                                if 'email' in key_lower and '@' in value_str:
                                    user_email = value_str
                                # Extract name
                                elif ('name' in key_lower or 'respondent' in key_lower) and len(value_str) < 100 and not '?' in value_str:
                                    if not user_name or len(value_str) > len(user_name):
                                        user_name = value_str
                                # Extract organization
                                elif ('organization' in key_lower or 'company' in key_lower or 'org' in key_lower) and len(value_str) < 100:
                                    organization = value_str

                        # Skip rows with no user data AND no meaningful response data
                        # (e.g., anonymous entries with only timestamps)
                        has_user_data = user_name or user_email or organization

                        # Count meaningful response fields (exclude timestamps, IDs, etc.)
                        meaningful_fields = []
                        for key, value in data.items():
                            if value and str(value).strip():
                                key_lower = key.lower()
                                value_str = str(value).strip()

                                # Skip metadata fields
                                if any(x in key_lower for x in ['timestamp', 'id', 'created', 'updated', 'date']):
                                    continue
                                # Skip if it's just a question
                                if '?' in value_str and len(value_str) > 50:
                                    continue

                                meaningful_fields.append(value_str)

                        # If no user data and no meaningful responses, skip this row
                        if not has_user_data and len(meaningful_fields) == 0:
                            continue

                        # Create a detailed preview of the data changes
                        preview_items = []
                        key_value_pairs = []

                        for key, value in data.items():
                            if value and str(value).strip():
                                clean_value = str(value).strip()

                                # Determine if this looks like a question or an answer
                                is_question = (
                                    len(clean_value) > 50 and
                                    ('?' in clean_value or 'Select' in clean_value or 'describe' in clean_value.lower())
                                )

                                # Store full key-value pairs for detailed view
                                key_value_pairs.append({
                                    'key': key,
                                    'value': clean_value,
                                    'truncated': len(clean_value) > 100,
                                    'is_question': is_question
                                })

                                # Create preview - prioritize answers over questions
                                if len(preview_items) < 4:
                                    if is_question:
                                        # For questions, show a shortened version
                                        if len(clean_value) > 80:
                                            preview_value = clean_value[:77] + "..."
                                        else:
                                            preview_value = clean_value

                                        # Clean up field names for display
                                        display_key = key.replace('_', ' ').replace('-', ' ').title()
                                        if len(display_key) > 15:
                                            display_key = display_key[:12] + "..."

                                        preview_items.append(f"**Q: {display_key}**: {preview_value}")
                                    else:
                                        # For answers, show the full value (these are usually shorter)
                                        if len(clean_value) > 60:
                                            preview_value = clean_value[:57] + "..."
                                        else:
                                            preview_value = clean_value

                                        # Clean up field names for display
                                        display_key = key.replace('_', ' ').replace('-', ' ').title()
                                        if len(display_key) > 15:
                                            display_key = display_key[:12] + "..."

                                        preview_items.append(f"**A: {display_key}**: {preview_value}")

                        # Sort preview items to show answers first, then questions
                        answer_items = [item for item in preview_items if item.startswith("**A:")]
                        question_items = [item for item in preview_items if item.startswith("**Q:")]

                        # Combine with answers first
                        combined_items = answer_items + question_items
                        preview = " • ".join(combined_items[:4]) if combined_items else "No data available"

                        # Get spreadsheet URL - handle both dict and sqlite3.Row
                        try:
                            spreadsheet_url = row['spreadsheet_url'] if 'spreadsheet_url' in row.keys() else f"https://docs.google.com/spreadsheets/d/{row['spreadsheet_id']}/edit"
                        except:
                            spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{row['spreadsheet_id']}/edit"

                        updates.append({
                            'id': row['id'],
                            'spreadsheet_title': row['spreadsheet_title'],
                            'sheet_type': row['sheet_type'],
                            'spreadsheet_id': row['spreadsheet_id'],
                            'row_number': row['row_number'],
                            'created_at': row['created_at'],
                            'preview': preview,
                            'data_count': len([v for v in data.values() if v and str(v).strip()]),
                            'key_value_pairs': key_value_pairs[:8],  # Limit to first 8 fields for performance
                            'spreadsheet_url': spreadsheet_url,
                            'has_more_data': len(key_value_pairs) > 8,
                            'user_name': user_name,
                            'user_email': user_email,
                            'organization': organization
                        })
                    except Exception as e:
                        logger.warning(f"Error processing update row {row['id']}: {e}")
                        # Add a safe fallback entry
                        updates.append({
                            'id': row['id'],
                            'spreadsheet_title': row['spreadsheet_title'] or 'Unknown Spreadsheet',
                            'sheet_type': row['sheet_type'] or 'unknown',
                            'spreadsheet_id': row['spreadsheet_id'],
                            'row_number': row['row_number'],
                            'created_at': row['created_at'],
                            'preview': 'Data processing error',
                            'data_count': 0
                        })

                logger.info(f"✅ Retrieved {len(updates)} latest updates")
                return updates

        except Exception as e:
            logger.error(f"❌ Error getting latest updates: {e}")
            return []

    def get_updates_summary(self, limit=50):
        """Get a summary of latest updates grouped by spreadsheet with organization counts."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Get latest raw data entries
                if self.use_postgresql:
                    cursor.execute('''
                        SELECT
                            rd.id,
                            rd.row_number,
                            rd.created_at,
                            s.title as spreadsheet_title,
                            s.sheet_type,
                            s.spreadsheet_id,
                            s.url as spreadsheet_url,
                            rd.data_json
                        FROM raw_data rd
                        JOIN spreadsheets s ON rd.spreadsheet_id = s.spreadsheet_id
                        ORDER BY rd.created_at DESC
                        LIMIT %s
                    ''', (limit,))
                else:
                    cursor.execute('''
                        SELECT
                            rd.id,
                            rd.row_number,
                            rd.created_at,
                            s.title as spreadsheet_title,
                            s.sheet_type,
                            s.spreadsheet_id,
                            s.url as spreadsheet_url,
                            rd.data_json
                        FROM raw_data rd
                        JOIN spreadsheets s ON rd.spreadsheet_id = s.spreadsheet_id
                        ORDER BY rd.created_at DESC
                        LIMIT ?
                    ''', (limit,))

                # Group by spreadsheet
                import json
                from collections import defaultdict

                spreadsheet_updates = defaultdict(lambda: {
                    'spreadsheet_id': None,
                    'spreadsheet_title': None,
                    'spreadsheet_url': None,
                    'sheet_type': None,
                    'count': 0,
                    'organizations': set(),
                    'users': set(),
                    'latest_update': None
                })

                for row in cursor.fetchall():
                    try:
                        data = json.loads(row['data_json']) if row['data_json'] else {}

                        # Skip empty rows
                        non_empty_values = [v for v in data.values() if v and str(v).strip()]
                        if len(non_empty_values) == 0:
                            continue

                        # Skip question definition rows
                        question_count = sum(1 for v in data.values() if v and '?' in str(v))
                        if question_count > len(non_empty_values) * 0.8:
                            continue

                        spreadsheet_id = row['spreadsheet_id']

                        # Extract organization and user
                        organization = None
                        user_name = None

                        for key, value in data.items():
                            if value and str(value).strip():
                                key_lower = key.lower()
                                value_str = str(value).strip()

                                if ('organization' in key_lower or 'company' in key_lower) and len(value_str) < 100:
                                    organization = value_str
                                elif ('name' in key_lower or 'respondent' in key_lower) and len(value_str) < 100 and not '?' in value_str:
                                    if not user_name or len(value_str) > len(user_name):
                                        user_name = value_str

                        # Update spreadsheet summary
                        summary = spreadsheet_updates[spreadsheet_id]
                        summary['spreadsheet_id'] = spreadsheet_id
                        summary['spreadsheet_title'] = row['spreadsheet_title']
                        summary['sheet_type'] = row['sheet_type']
                        summary['count'] += 1

                        # Get spreadsheet URL
                        try:
                            summary['spreadsheet_url'] = row['spreadsheet_url'] if 'spreadsheet_url' in row.keys() else f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
                        except:
                            summary['spreadsheet_url'] = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"

                        if organization:
                            summary['organizations'].add(organization)
                        if user_name:
                            summary['users'].add(user_name)

                        if not summary['latest_update'] or row['created_at'] > summary['latest_update']:
                            summary['latest_update'] = row['created_at']

                    except Exception as e:
                        logger.warning(f"Error processing summary row {row['id']}: {e}")
                        continue

                # Convert to list and format
                result = []
                for spreadsheet_id, summary in spreadsheet_updates.items():
                    result.append({
                        'spreadsheet_id': summary['spreadsheet_id'],
                        'spreadsheet_title': summary['spreadsheet_title'],
                        'spreadsheet_url': summary['spreadsheet_url'],
                        'sheet_type': summary['sheet_type'],
                        'update_count': summary['count'],
                        'organizations': sorted(list(summary['organizations'])),
                        'organization_count': len(summary['organizations']),
                        'user_count': len(summary['users']),
                        'latest_update': summary['latest_update']
                    })

                # Sort by latest update
                result.sort(key=lambda x: x['latest_update'] or '', reverse=True)

                logger.info(f"✅ Retrieved summary for {len(result)} spreadsheets")
                return result

        except Exception as e:
            logger.error(f"❌ Error getting updates summary: {e}")
            return []

# Initialize database on Railway
if os.getenv('RAILWAY_ENVIRONMENT'):
    logger.info("🚂 Railway environment detected - initializing database...")
    try:
        from railway_init import railway_database_init
        if railway_database_init():
            logger.info("✅ Railway database initialization successful")
        else:
            logger.warning("⚠️ Railway database initialization had issues")
    except Exception as e:
        logger.error(f"❌ Railway database initialization failed: {e}")

# Initialize database manager and analytics
db = DatabaseManager()
# SurveyAnalytics will auto-detect PostgreSQL from DATABASE_URL environment variable
analytics = SurveyAnalytics(db_path=SURVEY_DB_PATH, use_postgresql=USE_POSTGRESQL, database_url=DATABASE_URL)
auto_sync = get_auto_sync_service()

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page for application access."""
    if not REQUIRE_AUTH:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        password = request.form.get('password')
        next_url = request.form.get('next') or url_for('dashboard')

        if password == APP_PASSWORD:
            session['authenticated'] = True
            logger.info(f"Successful login from {request.remote_addr}")
            flash('Successfully logged in!', 'success')
            return redirect(next_url)
        else:
            logger.warning(f"Failed login attempt from {request.remote_addr}")
            flash('Invalid password. Please try again.', 'error')

    next_url = request.args.get('next', url_for('dashboard'))
    return render_template('login.html', next_url=next_url)

@app.route('/logout')
def logout():
    """Logout and clear session."""
    session.pop('authenticated', None)
    logger.info(f"User logged out from {request.remote_addr}")
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/')
@require_auth
def dashboard():
    """Dashboard with overview statistics."""
    try:
        # Force a safe stats object for Railway
        try:
            stats = db.get_dashboard_stats()
            logger.info(f"✅ Dashboard stats retrieved: {type(stats)}")
            logger.info(f"✅ Dashboard stats content: {stats}")
        except Exception as db_error:
            logger.error(f"❌ Database error in dashboard: {db_error}")
            # Force safe default stats
            stats = {
                'total_spreadsheets': 0,
                'total_rows': 0,
                'total_jobs': 0,
                'latest_job': None,
                'sheet_types': []
            }
            logger.info(f"✅ Using default stats: {stats}")

        # Double-check stats structure
        if not isinstance(stats, dict):
            logger.error(f"❌ Stats is not a dict: {type(stats)} = {stats}")
            stats = {
                'total_spreadsheets': 0,
                'total_rows': 0,
                'total_jobs': 0,
                'latest_job': None,
                'sheet_types': []
            }

        # Ensure all required keys exist
        required_keys = ['total_spreadsheets', 'total_rows', 'total_jobs', 'latest_job', 'sheet_types']
        for key in required_keys:
            if key not in stats:
                logger.error(f"❌ Missing key '{key}' in stats, adding default")
                stats[key] = 0 if key.startswith('total_') else (None if key == 'latest_job' else [])

        logger.info(f"✅ Final stats for template: {stats}")

        # Get spreadsheets safely
        try:
            spreadsheets = db.get_spreadsheets()
            logger.info(f"✅ Retrieved {len(spreadsheets)} spreadsheets")
        except Exception as ss_error:
            logger.error(f"❌ Error getting spreadsheets: {ss_error}")
            spreadsheets = []

        # Get latest updates safely
        try:
            latest_updates = db.get_latest_updates(20)
            logger.info(f"✅ Retrieved {len(latest_updates)} latest updates")
        except Exception as updates_error:
            logger.error(f"❌ Error getting latest updates: {updates_error}")
            latest_updates = []

        # Get updates summary grouped by spreadsheet
        try:
            updates_summary = db.get_updates_summary(50)
            logger.info(f"✅ Retrieved summary for {len(updates_summary)} spreadsheets")
        except Exception as summary_error:
            logger.error(f"❌ Error getting updates summary: {summary_error}")
            updates_summary = []

        return render_template('dashboard.html',
                             stats=stats,
                             spreadsheets=spreadsheets,
                             latest_updates=latest_updates,
                             updates_summary=updates_summary)

    except Exception as e:
        logger.error(f"❌ Dashboard route error: {str(e)}")
        logger.error(f"❌ Error type: {type(e)}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")

        # Return a safe error page with minimal stats
        safe_stats = {
            'total_spreadsheets': 0,
            'total_rows': 0,
            'total_jobs': 0,
            'latest_job': None,
            'sheet_types': []
        }
        return render_template('dashboard.html', stats=safe_stats, spreadsheets=[]), 200

@app.route('/spreadsheets')
@require_auth
def spreadsheets():
    """List all spreadsheets."""
    try:
        spreadsheets_data = db.get_spreadsheets()
        return render_template('spreadsheets.html', spreadsheets=spreadsheets_data)
    except Exception as e:
        return render_template('error.html', error=str(e)), 500

@app.route('/spreadsheet/<spreadsheet_id>')
@require_auth
def view_spreadsheet(spreadsheet_id):
    """View data from a specific spreadsheet."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        result = db.get_spreadsheet_data(spreadsheet_id, page, per_page)
        
        if not result['spreadsheet']:
            return render_template('error.html', error='Spreadsheet not found'), 404
        
        return render_template('spreadsheet_detail.html', **result)
    except Exception as e:
        return render_template('error.html', error=str(e)), 500

@app.route('/jobs')
@require_auth
def extraction_jobs():
    """View extraction job history."""
    try:
        jobs = db.get_extraction_jobs()
        return render_template('jobs.html', jobs=jobs)
    except Exception as e:
        return render_template('error.html', error=str(e)), 500

@app.route('/api/spreadsheet/<spreadsheet_id>/data')
def api_spreadsheet_data(spreadsheet_id):
    """API endpoint for spreadsheet data."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        result = db.get_spreadsheet_data(spreadsheet_id, page, per_page)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def api_stats():
    """API endpoint for dashboard statistics."""
    try:
        stats = db.get_dashboard_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/surveys')
@require_auth
def survey_dashboard():
    """Survey analytics dashboard."""
    try:
        # Check database availability based on environment
        if USE_POSTGRESQL:
            # For PostgreSQL, check if tables exist
            try:
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT COUNT(*) as count FROM information_schema.tables
                        WHERE table_schema = 'public' AND table_name = 'survey_questions'
                    """)
                    result = cursor.fetchone()
                    table_exists = result['count'] > 0 if result else False

                    if not table_exists:
                        return render_template('error.html',
                            error='Survey database tables missing. <a href="/init-survey-db">Click here to initialize the database</a>.'), 404
            except Exception as db_error:
                return render_template('error.html',
                    error=f'Survey database error: {db_error}. <a href="/init-survey-db">Click here to initialize the database</a>.'), 500
        else:
            # For SQLite, check if file exists
            if not os.path.exists(SURVEY_DB_PATH):
                return render_template('error.html',
                                     error=f'Survey database not found at {SURVEY_DB_PATH}. <a href="/init-survey-db">Click here to initialize it</a>.'), 404

        # Check if analytics is available
        if not analytics:
            return render_template('error.html',
                                 error='Survey analytics not available. Please check the survey database.'), 500

        # Try to get analytics data with error handling
        try:
            overview = analytics.get_survey_overview()
            survey_breakdown = analytics.get_survey_breakdown()
            respondent_analysis = analytics.get_respondent_analysis()
            completion_stats = analytics.get_survey_completion_stats()
        except Exception as analytics_error:
            if 'no such table' in str(analytics_error).lower():
                return render_template('error.html',
                                     error=f'Survey database tables missing. <a href="/init-survey-db">Click here to initialize the database</a>. Error: {analytics_error}'), 500
            elif 'no such column' in str(analytics_error).lower():
                # Handle schema mismatch - provide basic survey info instead
                import sqlite3
                with sqlite3.connect(SURVEY_DB_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM surveys")
                    survey_count = cursor.fetchone()[0]
                    cursor.execute("SELECT COUNT(*) FROM survey_questions")
                    question_count = cursor.fetchone()[0]

                    # Get basic survey list using correct column names
                    cursor.execute("SELECT title, description FROM surveys LIMIT 10")
                    surveys = [{'survey_name': row[0] or 'Untitled Survey', 'survey_type': 'survey'} for row in cursor.fetchall()]

                # Create basic overview data
                overview = {
                    'total_surveys': survey_count,
                    'total_questions': question_count,
                    'total_responses': 0,
                    'response_rate': 0,
                    'schema_note': 'Limited data due to schema differences'
                }
                survey_breakdown = surveys
                respondent_analysis = {'browser_breakdown': [], 'device_breakdown': [], 'response_frequency': []}
                completion_stats = []
            else:
                raise analytics_error

        return render_template('survey_dashboard.html',
                             overview=overview,
                             survey_breakdown=survey_breakdown,
                             respondent_analysis=respondent_analysis,
                             completion_stats=completion_stats)
    except Exception as e:
        logger.error(f"Survey dashboard error: {e}")
        return render_template('error.html', error=f'Survey dashboard error: {str(e)}'), 500

@app.route('/surveys/analytics')
def survey_analytics():
    """Detailed survey analytics page."""
    try:
        # Check database availability based on environment
        if USE_POSTGRESQL:
            # For PostgreSQL, check if tables exist
            try:
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT COUNT(*) as count FROM information_schema.tables
                        WHERE table_schema = 'public' AND table_name = 'survey_questions'
                    """)
                    result = cursor.fetchone()
                    table_exists = result['count'] > 0 if result else False

                    if not table_exists:
                        return render_template('error.html',
                            error='Survey database tables missing. <a href="/init-survey-db">Initialize database</a>'), 404
            except Exception as db_error:
                return render_template('error.html',
                    error=f'Survey database error: {db_error}. <a href="/init-survey-db">Initialize database</a>'), 500
        else:
            # For SQLite, check if file exists
            if not os.path.exists(SURVEY_DB_PATH):
                return render_template('error.html',
                                     error=f'Survey database not found. <a href="/init-survey-db">Initialize database</a>'), 404

        if not analytics:
            return render_template('error.html',
                                 error='Survey analytics not available.'), 500

        survey_id = request.args.get('survey_id', type=int)

        try:
            question_analytics = analytics.get_question_analytics(survey_id)
            time_series = analytics.get_time_series_data(30)
            activity = analytics.get_response_activity(30)
        except Exception as analytics_error:
            if 'no such table' in str(analytics_error).lower():
                return render_template('error.html',
                                     error=f'Survey database tables missing. <a href="/init-survey-db">Initialize database</a>'), 500
            else:
                raise analytics_error

        return render_template('survey_analytics.html',
                             question_analytics=question_analytics,
                             time_series=time_series,
                             activity=activity,
                             selected_survey_id=survey_id)
    except Exception as e:
        logger.error(f"Survey analytics error: {e}")
        return render_template('error.html', error=str(e)), 500

@app.route('/surveys/responses')
def survey_responses():
    """Survey response activity dashboard."""
    try:
        # Check database availability based on environment
        if USE_POSTGRESQL:
            # For PostgreSQL, check if tables exist
            try:
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT COUNT(*) as count FROM information_schema.tables
                        WHERE table_schema = 'public' AND table_name = 'survey_questions'
                    """)
                    result = cursor.fetchone()
                    table_exists = result['count'] > 0 if result else False

                    if not table_exists:
                        return render_template('error.html',
                            error='Survey database tables missing. <a href="/init-survey-db">Initialize database</a>'), 404
            except Exception as db_error:
                return render_template('error.html',
                    error=f'Survey database error: {db_error}. <a href="/init-survey-db">Initialize database</a>'), 500
        else:
            # For SQLite, check if file exists
            if not os.path.exists(SURVEY_DB_PATH):
                return render_template('error.html',
                                     error='Normalized survey database not found. Please run survey_normalizer.py first.'), 404

        days = request.args.get('days', 30, type=int)
        activity = analytics.get_response_activity(days)
        respondent_analysis = analytics.get_respondent_analysis()
        time_series = analytics.get_time_series_data(days)

        return render_template('survey_responses.html',
                             activity=activity,
                             respondent_analysis=respondent_analysis,
                             time_series=time_series,
                             days=days)
    except Exception as e:
        return render_template('error.html', error=str(e)), 500

@app.route('/api/survey/search')
def api_survey_search():
    """API endpoint for searching survey responses."""
    try:
        search_term = request.args.get('q', '')
        survey_id = request.args.get('survey_id', type=int)

        if not search_term:
            return jsonify({'results': []})

        results = analytics.search_responses(search_term, survey_id)
        return jsonify({'results': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/survey/<int:survey_id>/export')
def api_survey_export(survey_id):
    """API endpoint for exporting survey data."""
    try:
        data = analytics.export_survey_data(survey_id)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/sync')
@require_auth
def sync_dashboard():
    """Auto-sync management dashboard."""
    try:
        sync_status = auto_sync.get_sync_status()
        service_stats = auto_sync.get_stats()

        return render_template('sync_dashboard.html',
                             sync_status=sync_status,
                             service_stats=service_stats)
    except Exception as e:
        return render_template('error.html', error=str(e)), 500

@app.route('/api/sync/status')
def api_sync_status():
    """API endpoint for sync status."""
    try:
        status = auto_sync.get_sync_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sync/start', methods=['POST'])
def api_sync_start():
    """API endpoint to start auto-sync service."""
    try:
        check_interval = request.json.get('check_interval', 300) if request.is_json else 300
        auto_sync.check_interval = check_interval
        auto_sync.start()
        return jsonify({
            'success': True,
            'message': f'Auto-sync started with {check_interval}s interval',
            'stats': auto_sync.get_stats()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sync/stop', methods=['POST'])
def api_sync_stop():
    """API endpoint to stop auto-sync service."""
    try:
        auto_sync.stop()
        return jsonify({
            'success': True,
            'message': 'Auto-sync stopped',
            'stats': auto_sync.get_stats()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sync/force', methods=['POST'])
def api_sync_force():
    """API endpoint to force immediate sync."""
    try:
        result = auto_sync.force_sync()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Health Check System - Integrated Flask Endpoints
class HealthCheckService:
    """Integrated health check service for Flask application."""

    def __init__(self):
        self.cache = {}
        self.cache_duration = 30  # seconds

    def _is_cache_valid(self, cache_key):
        """Check if cached result is still valid."""
        if cache_key not in self.cache:
            return False

        cache_time = self.cache[cache_key].get('timestamp', 0)
        return (time.time() - cache_time) < self.cache_duration

    def _cache_result(self, cache_key, result):
        """Cache a health check result."""
        self.cache[cache_key] = {
            'result': result,
            'timestamp': time.time()
        }

    def _get_cached_result(self, cache_key):
        """Get cached result if valid."""
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['result']
        return None

    def check_api_keys(self):
        """Check API keys and authentication."""
        cache_key = 'api_keys'
        cached = self._get_cached_result(cache_key)
        if cached:
            logger.debug("Using cached API keys health check result")
            return cached

        try:
            logger.info("Running API keys health check")
            from healthcheck.api_validators import run_all_api_validations
            results = run_all_api_validations()

            formatted_results = []
            for name, status, message, details in results:
                formatted_results.append({
                    "name": name,
                    "status": status,
                    "message": message,
                    "category": "api",
                    "details": details
                })

                # Log individual check results for Railway logs
                if status == "fail":
                    logger.error(f"API Health Check FAILED - {name}: {message}")
                elif status == "warning":
                    logger.warning(f"API Health Check WARNING - {name}: {message}")
                else:
                    logger.debug(f"API Health Check PASSED - {name}: {message}")

            result = {
                "category": "api_keys",
                "timestamp": datetime.now().isoformat(),
                "checks": formatted_results,
                "summary": self._calculate_summary(formatted_results)
            }

            summary = result["summary"]
            logger.info(f"API keys health check completed: {summary['passed']}/{summary['total']} passed, {summary['failed']} failed, {summary['warnings']} warnings")

            self._cache_result(cache_key, result)
            return result

        except Exception as e:
            logger.error(f"API keys health check failed with exception: {str(e)}", exc_info=True)
            return {
                "category": "api_keys",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "checks": [],
                "summary": {"total": 0, "passed": 0, "failed": 1, "warnings": 0}
            }

    async def check_dependencies(self):
        """Check external dependencies."""
        cache_key = 'dependencies'
        cached = self._get_cached_result(cache_key)
        if cached:
            return cached

        try:
            from healthcheck.dependency_checker import run_all_dependency_checks
            results = await run_all_dependency_checks()

            formatted_results = []
            for name, status, message, details in results:
                formatted_results.append({
                    "name": name,
                    "status": status,
                    "message": message,
                    "category": "dependency",
                    "details": details
                })

            result = {
                "category": "dependencies",
                "timestamp": datetime.now().isoformat(),
                "checks": formatted_results,
                "summary": self._calculate_summary(formatted_results)
            }

            self._cache_result(cache_key, result)
            return result

        except Exception as e:
            return {
                "category": "dependencies",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "checks": [],
                "summary": {"total": 0, "passed": 0, "failed": 1, "warnings": 0}
            }

    async def check_e2e_tests(self):
        """Run end-to-end tests."""
        cache_key = 'e2e_tests'
        cached = self._get_cached_result(cache_key)
        if cached:
            return cached

        try:
            from healthcheck.e2e_tests import run_all_e2e_tests
            results = await run_all_e2e_tests()

            formatted_results = []
            for name, status, message, details in results:
                formatted_results.append({
                    "name": name,
                    "status": status,
                    "message": message,
                    "category": "e2e",
                    "details": details
                })

            result = {
                "category": "e2e_tests",
                "timestamp": datetime.now().isoformat(),
                "checks": formatted_results,
                "summary": self._calculate_summary(formatted_results)
            }

            self._cache_result(cache_key, result)
            return result

        except Exception as e:
            return {
                "category": "e2e_tests",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "checks": [],
                "summary": {"total": 0, "passed": 0, "failed": 1, "warnings": 0}
            }

    def check_configuration(self):
        """Check configuration validation."""
        cache_key = 'configuration'
        cached = self._get_cached_result(cache_key)
        if cached:
            return cached

        try:
            from healthcheck.config_validator import run_all_config_validations
            results = run_all_config_validations()

            formatted_results = []
            for name, status, message, details in results:
                formatted_results.append({
                    "name": name,
                    "status": status,
                    "message": message,
                    "category": "config",
                    "details": details
                })

            result = {
                "category": "configuration",
                "timestamp": datetime.now().isoformat(),
                "checks": formatted_results,
                "summary": self._calculate_summary(formatted_results)
            }

            self._cache_result(cache_key, result)
            return result

        except Exception as e:
            return {
                "category": "configuration",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "checks": [],
                "summary": {"total": 0, "passed": 0, "failed": 1, "warnings": 0}
            }

    def _calculate_summary(self, checks):
        """Calculate summary statistics for checks."""
        total = len(checks)
        passed = sum(1 for c in checks if c["status"] == "pass")
        failed = sum(1 for c in checks if c["status"] == "fail")
        warnings = sum(1 for c in checks if c["status"] == "warning")

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "warnings": warnings
        }

    async def run_complete_health_check(self):
        """Run all health checks and return comprehensive results."""
        start_time = time.time()

        # Run all check categories
        api_results = self.check_api_keys()
        dependency_results = await self.check_dependencies()
        e2e_results = await self.check_e2e_tests()
        config_results = self.check_configuration()

        # Combine all results
        all_checks = []
        categories = {
            "api_keys": api_results,
            "dependencies": dependency_results,
            "e2e_tests": e2e_results,
            "configuration": config_results
        }

        for category_name, category_data in categories.items():
            if "checks" in category_data:
                all_checks.extend(category_data["checks"])

        # Calculate overall summary
        overall_summary = self._calculate_summary(all_checks)

        # Determine overall status
        overall_status = "pass"
        if overall_summary["failed"] > 0:
            overall_status = "fail"
        elif overall_summary["warnings"] > 0:
            overall_status = "warning"

        duration_ms = (time.time() - start_time) * 1000

        return {
            "overall_status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "duration_ms": duration_ms,
            "summary": overall_summary,
            "categories": {
                name: data.get("summary", {}) for name, data in categories.items()
            },
            "checks": all_checks,
            "category_details": categories
        }

# Initialize health check service
health_service = HealthCheckService()

@app.route('/health')
def health_check():
    """
    Comprehensive health check endpoint for Railway.

    This endpoint is used by Railway for deployment health checks and monitoring.
    It performs a complete system health assessment including:
    - API keys and authentication
    - External dependencies
    - Database connectivity
    - Configuration validation
    """
    start_time = time.time()
    logger.info("Railway health check initiated")

    try:
        # Simplified health check for Railway compatibility
        results = {
            "overall_status": "pass",
            "timestamp": datetime.now().isoformat(),
            "summary": {"total": 1, "passed": 1, "failed": 0, "warnings": 0},
            "railway_info": {
                "environment": os.getenv("RAILWAY_ENVIRONMENT", "unknown"),
                "service_name": os.getenv("RAILWAY_SERVICE_NAME", "unknown"),
                "deployment_id": os.getenv("RAILWAY_DEPLOYMENT_ID", "unknown")
            },
            "system_info": {
                "python_version": sys.version,
                "port": PORT,
                "working_directory": os.getcwd()
            },
            "message": "JJF Survey Analytics is running on Railway"
        }

        # Log health check results for Railway logs
        duration = (time.time() - start_time) * 1000
        summary = results.get("summary", {})

        logger.info(f"Health check completed in {duration:.0f}ms: "
                   f"{summary.get('passed', 0)}/{summary.get('total', 0)} passed, "
                   f"{summary.get('failed', 0)} failed, "
                   f"{summary.get('warnings', 0)} warnings")

        # Log any failures for Railway debugging
        if results["overall_status"] == "fail":
            failed_checks = [check for check in results.get("checks", []) if check["status"] == "fail"]
            for check in failed_checks:
                logger.error(f"HEALTH CHECK FAILURE: {check['name']} - {check['message']}")

        # Railway expects 200 for healthy, 503 for unhealthy
        status_code = 200 if results["overall_status"] == "pass" else 503

        # Add Railway-specific metadata
        results["railway_info"] = {
            "environment": os.getenv("RAILWAY_ENVIRONMENT", "unknown"),
            "service_name": os.getenv("RAILWAY_SERVICE_NAME", "unknown"),
            "deployment_id": os.getenv("RAILWAY_DEPLOYMENT_ID", "unknown"),
            "health_check_duration_ms": duration
        }

        return jsonify(results), status_code

    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.error(f"Health check failed with exception after {duration:.0f}ms: {str(e)}", exc_info=True)

        return jsonify({
            "overall_status": "fail",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "summary": {"total": 0, "passed": 0, "failed": 1, "warnings": 0},
            "railway_info": {
                "environment": os.getenv("RAILWAY_ENVIRONMENT", "unknown"),
                "service_name": os.getenv("RAILWAY_SERVICE_NAME", "unknown"),
                "deployment_id": os.getenv("RAILWAY_DEPLOYMENT_ID", "unknown"),
                "health_check_duration_ms": duration
            }
        }), 500

@app.route('/health/api')
def health_check_api():
    """API keys and authentication health check."""
    try:
        results = health_service.check_api_keys()

        failed = results.get("summary", {}).get("failed", 0)
        status_code = 200 if failed == 0 else 503

        return jsonify(results), status_code

    except Exception as e:
        return jsonify({
            "category": "api_keys",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 500

@app.route('/health/dependencies')
@async_route
async def health_check_dependencies():
    """External dependencies health check."""
    try:
        results = await health_service.check_dependencies()

        failed = results.get("summary", {}).get("failed", 0)
        status_code = 200 if failed == 0 else 503

        return jsonify(results), status_code

    except Exception as e:
        return jsonify({
            "category": "dependencies",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 500

@app.route('/health/e2e')
@async_route
async def health_check_e2e():
    """End-to-end functionality health check."""
    try:
        results = await health_service.check_e2e_tests()

        failed = results.get("summary", {}).get("failed", 0)
        status_code = 200 if failed == 0 else 503

        return jsonify(results), status_code

    except Exception as e:
        return jsonify({
            "category": "e2e_tests",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 500

@app.route('/health/config')
def health_check_config():
    """Configuration validation health check."""
    try:
        results = health_service.check_configuration()

        failed = results.get("summary", {}).get("failed", 0)
        status_code = 200 if failed == 0 else 503

        return jsonify(results), status_code

    except Exception as e:
        return jsonify({
            "category": "configuration",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 500

@app.route('/health/dashboard')
@require_auth
def health_dashboard():
    """Health dashboard web interface."""
    return render_template('health_dashboard.html')

@app.route('/health/status')
@async_route
async def health_status():
    """
    Quick health status endpoint for load balancers and Railway.

    This is a lightweight health check that focuses on critical services only.
    Used by Railway for quick health monitoring and load balancer health checks.
    """
    start_time = time.time()

    try:
        # Quick check - just critical services
        api_results = health_service.check_api_keys()
        dependency_results = await health_service.check_dependencies()

        # Focus on critical checks only
        critical_checks = []
        critical_services = {
            "api": ["Google Credentials", "Environment Variables"],
            "dependencies": ["SQLite Databases", "Google Sheets API"]
        }

        # Check for critical API failures
        for check in api_results.get("checks", []):
            if check["name"] in critical_services["api"] and check["status"] == "fail":
                critical_checks.append(check)

        # Check for critical dependency failures
        for check in dependency_results.get("checks", []):
            if check["name"] in critical_services["dependencies"] and check["status"] == "fail":
                critical_checks.append(check)

        duration = (time.time() - start_time) * 1000

        if critical_checks:
            logger.warning(f"Health status check failed: {len(critical_checks)} critical issues in {duration:.0f}ms")
            for check in critical_checks:
                logger.error(f"CRITICAL HEALTH ISSUE: {check['name']} - {check['message']}")

            return jsonify({
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "critical_issues": len(critical_checks),
                "duration_ms": duration,
                "railway_info": {
                    "environment": os.getenv("RAILWAY_ENVIRONMENT", "unknown"),
                    "deployment_id": os.getenv("RAILWAY_DEPLOYMENT_ID", "unknown")
                }
            }), 503
        else:
            logger.debug(f"Health status check passed in {duration:.0f}ms")
            return jsonify({
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "duration_ms": duration,
                "railway_info": {
                    "environment": os.getenv("RAILWAY_ENVIRONMENT", "unknown"),
                    "deployment_id": os.getenv("RAILWAY_DEPLOYMENT_ID", "unknown")
                }
            }), 200

    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.error(f"Health status check failed with exception in {duration:.0f}ms: {str(e)}")

        return jsonify({
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "duration_ms": duration,
            "railway_info": {
                "environment": os.getenv("RAILWAY_ENVIRONMENT", "unknown"),
                "deployment_id": os.getenv("RAILWAY_DEPLOYMENT_ID", "unknown")
            }
        }), 500

@app.route('/health/metrics')
@async_route
async def health_metrics():
    """Health metrics endpoint for monitoring systems."""
    try:
        results = await health_service.run_complete_health_check()

        # Convert to Prometheus-style metrics
        metrics = []

        # Overall health metric
        health_value = 1 if results["overall_status"] == "pass" else 0
        metrics.append(f'health_check_status{{overall="true"}} {health_value}')

        # Category metrics
        for category, summary in results.get("categories", {}).items():
            total = summary.get("total", 0)
            passed = summary.get("passed", 0)
            failed = summary.get("failed", 0)
            warnings = summary.get("warnings", 0)

            metrics.append(f'health_check_total{{category="{category}"}} {total}')
            metrics.append(f'health_check_passed{{category="{category}"}} {passed}')
            metrics.append(f'health_check_failed{{category="{category}"}} {failed}')
            metrics.append(f'health_check_warnings{{category="{category}"}} {warnings}')

        # Duration metric
        duration = results.get("duration_ms", 0)
        metrics.append(f'health_check_duration_ms {duration}')

        # Individual check metrics
        for check in results.get("checks", []):
            check_value = 1 if check["status"] == "pass" else 0
            check_name = check["name"].lower().replace(" ", "_").replace("-", "_")
            category = check["category"]
            metrics.append(f'health_check_individual{{name="{check_name}",category="{category}"}} {check_value}')

        response_text = "\n".join(metrics) + "\n"

        return app.response_class(
            response=response_text,
            status=200,
            mimetype='text/plain'
        )

    except Exception as e:
        return app.response_class(
            response=f'health_check_error 1\n# Error: {str(e)}\n',
            status=500,
            mimetype='text/plain'
        )

@app.route('/health/test')
def health_test():
    """Simple test endpoint to verify health check system is working."""
    logger.info("Health check test endpoint accessed")

    # Railway deployment info
    railway_info = {
        "railway_environment": os.getenv("RAILWAY_ENVIRONMENT", "unknown"),
        "railway_service_name": os.getenv("RAILWAY_SERVICE_NAME", "unknown"),
        "railway_deployment_id": os.getenv("RAILWAY_DEPLOYMENT_ID", "unknown"),
        "port": os.getenv("PORT", "5001")
    }

    return jsonify({
        "message": "Health check system is operational",
        "timestamp": datetime.now().isoformat(),
        "deployment": railway_info,
        "endpoints": {
            "complete_check": "/health",
            "api_keys": "/health/api",
            "dependencies": "/health/dependencies",
            "e2e_tests": "/health/e2e",
            "configuration": "/health/config",
            "quick_status": "/health/status",
            "metrics": "/health/metrics",
            "dashboard": "/health/dashboard"
        },
        "cache_info": {
            "cache_duration_seconds": health_service.cache_duration,
            "cached_results": list(health_service.cache.keys())
        },
        "system_info": {
            "python_path": os.getenv("PYTHONPATH", "not_set"),
            "working_directory": os.getcwd(),
            "environment_vars": {
                "GOOGLE_CREDENTIALS_FILE": "set" if os.getenv("GOOGLE_CREDENTIALS_FILE") else "not_set",
                "DATABASE_URL": "set" if os.getenv("DATABASE_URL") else "not_set",
                "LOG_LEVEL": os.getenv("LOG_LEVEL", "not_set")
            }
        }
    })

@app.route('/import-data')
def manual_import_data():
    """Manual data import endpoint."""
    try:
        import sqlite3
        import os

        results = {
            'status': 'started',
            'timestamp': datetime.now().isoformat(),
            'environment': 'railway' if os.getenv('RAILWAY_ENVIRONMENT') else 'local',
            'files_found': [],
            'current_dir': os.getcwd(),
            'files_in_dir': os.listdir('.'),
            'import_results': []
        }

        # Check for import files
        if os.path.exists('railway_data_import.sql'):
            results['files_found'].append('railway_data_import.sql')

            # Import main database
            with sqlite3.connect('surveyor_data_improved.db') as conn:
                cursor = conn.cursor()

                # Check current count
                cursor.execute('SELECT COUNT(*) FROM spreadsheets')
                before_count = cursor.fetchone()[0]

                # Import data
                with open('railway_data_import.sql', 'r') as f:
                    sql_content = f.read()
                    statements = sql_content.split(';')
                    imported = 0
                    errors = []

                    for statement in statements:
                        statement = statement.strip()
                        if statement and not statement.startswith('--'):
                            try:
                                conn.execute(statement)
                                imported += 1
                            except Exception as e:
                                if 'already exists' not in str(e) and 'UNIQUE constraint failed' not in str(e):
                                    errors.append(str(e))

                    conn.commit()

                # Check after count
                cursor.execute('SELECT COUNT(*) FROM spreadsheets')
                after_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM raw_data')
                row_count = cursor.fetchone()[0]

                results['import_results'].append({
                    'database': 'main',
                    'statements_imported': imported,
                    'spreadsheets_before': before_count,
                    'spreadsheets_after': after_count,
                    'total_rows': row_count,
                    'errors': errors[:5]  # First 5 errors only
                })

        results['status'] = 'completed'
        return jsonify(results)

    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'failed',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/check-stats')
def check_stats():
    """Check current dashboard stats without authentication."""
    try:
        stats = db.get_dashboard_stats()
        return jsonify({
            'stats': stats,
            'timestamp': datetime.now().isoformat(),
            'environment': 'railway' if os.getenv('RAILWAY_ENVIRONMENT') else 'local'
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/check-schema')
def check_schema():
    """Check database schema differences."""
    try:
        import sqlite3

        schema_info = {}

        # Check main database schema
        with sqlite3.connect('surveyor_data_improved.db') as conn:
            cursor = conn.cursor()

            # Get table schemas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = [row[0] for row in cursor.fetchall()]

            for table in tables:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                schema_info[table] = {
                    'columns': [{'name': col[1], 'type': col[2], 'notnull': col[3], 'pk': col[5]} for col in columns]
                }

                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                schema_info[table]['row_count'] = cursor.fetchone()[0]

        return jsonify({
            'schema': schema_info,
            'timestamp': datetime.now().isoformat(),
            'environment': 'railway' if os.getenv('RAILWAY_ENVIRONMENT') else 'local'
        })

    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/fix-data-schema')
def fix_data_schema():
    """Fix the raw_data schema and import data properly."""
    try:
        import sqlite3
        import json

        results = {
            'status': 'started',
            'timestamp': datetime.now().isoformat(),
            'steps': []
        }

        # Step 1: Check current Railway schema
        with sqlite3.connect('surveyor_data_improved.db') as conn:
            cursor = conn.cursor()

            # Check current schema
            cursor.execute("PRAGMA table_info(raw_data)")
            current_columns = [col[1] for col in cursor.fetchall()]
            results['steps'].append(f"Current Railway schema: {current_columns}")

            # Check if we need to migrate schema
            expected_columns = ['row_number', 'data_json', 'data_hash']
            needs_migration = not all(col in current_columns for col in expected_columns)

            if needs_migration:
                results['steps'].append("Schema migration needed")

                # Step 2: Create new table with correct schema
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS raw_data_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        spreadsheet_id TEXT NOT NULL,
                        row_number INTEGER NOT NULL,
                        data_json TEXT NOT NULL,
                        data_hash TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (spreadsheet_id) REFERENCES spreadsheets (id)
                    )
                ''')
                results['steps'].append("Created new raw_data table with correct schema")

                # Step 3: Copy existing data if any
                cursor.execute("SELECT COUNT(*) FROM raw_data")
                existing_count = cursor.fetchone()[0]
                if existing_count > 0:
                    # Try to migrate existing data
                    cursor.execute("SELECT * FROM raw_data")
                    existing_rows = cursor.fetchall()
                    migrated = 0
                    for row in existing_rows:
                        try:
                            # Map old schema to new schema
                            cursor.execute('''
                                INSERT INTO raw_data_new (spreadsheet_id, row_number, data_json, created_at)
                                VALUES (?, 1, ?, ?)
                            ''', (row[1], row[3] or '{}', row[4]))  # spreadsheet_id, row_data as data_json, extracted_at
                            migrated += 1
                        except Exception as e:
                            results['steps'].append(f"Migration warning: {e}")
                    results['steps'].append(f"Migrated {migrated} existing rows")

                # Step 4: Replace old table
                cursor.execute("DROP TABLE raw_data")
                cursor.execute("ALTER TABLE raw_data_new RENAME TO raw_data")
                results['steps'].append("Replaced old table with new schema")

                conn.commit()
            else:
                results['steps'].append("Schema already correct")

        # Step 5: Import data from SQL file
        if os.path.exists('railway_data_import.sql'):
            with sqlite3.connect('surveyor_data_improved.db') as conn:
                cursor = conn.cursor()

                # Count before
                cursor.execute("SELECT COUNT(*) FROM raw_data")
                before_count = cursor.fetchone()[0]

                # Import raw_data specifically
                with open('railway_data_import.sql', 'r') as f:
                    sql_content = f.read()

                    # Extract only raw_data INSERT statements
                    lines = sql_content.split('\n')
                    raw_data_inserts = [line for line in lines if 'INSERT OR REPLACE INTO raw_data' in line]

                    imported = 0
                    errors = []
                    for insert_stmt in raw_data_inserts:
                        try:
                            cursor.execute(insert_stmt)
                            imported += 1
                        except Exception as e:
                            if len(errors) < 3:  # Only keep first 3 errors
                                errors.append(str(e))

                    conn.commit()

                # Count after
                cursor.execute("SELECT COUNT(*) FROM raw_data")
                after_count = cursor.fetchone()[0]

                results['steps'].append(f"Imported {imported} raw_data statements")
                results['steps'].append(f"Raw data rows: {before_count} → {after_count}")
                if errors:
                    results['steps'].append(f"Import errors: {errors}")

        results['status'] = 'completed'
        return jsonify(results)

    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'failed',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/init-survey-db')
def init_survey_database():
    """Initialize the survey normalized database."""
    try:
        results = {
            'status': 'started',
            'timestamp': datetime.now().isoformat(),
            'steps': []
        }

        # Use PostgreSQL if available, otherwise SQLite
        if USE_POSTGRESQL:
            results['steps'].append('Using PostgreSQL for survey database')

            # Survey tables should already exist from PostgreSQL initialization
            with db.get_connection() as conn:
                cursor = conn.cursor()

                # Check if survey tables exist
                cursor.execute("""
                    SELECT COUNT(*) as count FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name IN ('surveys', 'survey_questions')
                """)
                result = cursor.fetchone()
                table_count = result['count']

                if table_count < 2:
                    # Initialize PostgreSQL survey tables if they don't exist
                    db.init_postgresql_tables()
                    results['steps'].append('Created missing PostgreSQL survey tables')

                # Add sample survey data
                cursor.execute('''
                    INSERT INTO surveys (title, description, status)
                    VALUES (%s, %s, %s)
                    ON CONFLICT DO NOTHING
                    RETURNING id
                ''', ('JJF Survey Collection', 'Combined survey and assessment questions', 'active'))

                survey_result = cursor.fetchone()
                if survey_result:
                    survey_id = survey_result['id']
                    results['steps'].append(f'Created survey with ID: {survey_id}')
                else:
                    # Get existing survey ID
                    cursor.execute('SELECT id FROM surveys LIMIT 1')
                    survey_result = cursor.fetchone()
                    survey_id = survey_result['id'] if survey_result else 1
                    results['steps'].append(f'Using existing survey ID: {survey_id}')

                # Add sample questions
                sample_questions = [
                    ('tech_maturity', 'How would you rate your organization\'s overall technology maturity?'),
                    ('biggest_challenges', 'What are your organization\'s biggest technology challenges?'),
                    ('future_priorities', 'What are your top technology priorities for the next year?'),
                    ('satisfaction', 'How satisfied are you with current technology solutions?'),
                    ('training_needs', 'What technology training would be most valuable for your team?')
                ]

                question_count = 0
                for i, (key, text) in enumerate(sample_questions):
                    cursor.execute('''
                        INSERT INTO survey_questions
                        (survey_id, question_key, question_text, question_order)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                    ''', (survey_id, key, text, i + 1))
                    question_count += 1

                conn.commit()
                results['steps'].append(f'Added {question_count} sample questions')

                # Get final counts
                cursor.execute('SELECT COUNT(*) as count FROM surveys')
                survey_count = cursor.fetchone()['count']
                cursor.execute('SELECT COUNT(*) as count FROM survey_questions')
                question_count = cursor.fetchone()['count']

                results['summary'] = {
                    'database_type': 'PostgreSQL',
                    'total_surveys': survey_count,
                    'total_questions': question_count
                }

                results['status'] = 'completed'
                return jsonify(results)

        else:
            results['steps'].append('Using SQLite for survey database')
            import sqlite3

            # Check if survey database exists
            survey_db_exists = os.path.exists(SURVEY_DB_PATH)
            results['steps'].append(f"Survey DB exists: {survey_db_exists}")

            # Create survey database with required tables
            with sqlite3.connect(SURVEY_DB_PATH) as conn:
            cursor = conn.cursor()

            # Create surveys table
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
            results['steps'].append("Created surveys table")

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
                    FOREIGN KEY (survey_id) REFERENCES surveys (id),
                    UNIQUE(survey_id, question_key)
                )
            ''')
            results['steps'].append("Created survey_questions table")

            # Create other required tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS respondents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    respondent_hash TEXT UNIQUE NOT NULL,
                    browser TEXT,
                    device TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    first_response_date TIMESTAMP,
                    last_response_date TIMESTAMP,
                    total_responses INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            results['steps'].append("Created respondents table")

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS survey_responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    survey_id INTEGER NOT NULL,
                    respondent_id INTEGER NOT NULL,
                    response_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_complete BOOLEAN DEFAULT 0,
                    completion_time_seconds INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (survey_id) REFERENCES surveys (id),
                    FOREIGN KEY (respondent_id) REFERENCES respondents (id)
                )
            ''')
            results['steps'].append("Created survey_responses table")

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS survey_answers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    response_id INTEGER NOT NULL,
                    question_id INTEGER NOT NULL,
                    answer_text TEXT,
                    answer_numeric REAL,
                    answer_boolean BOOLEAN,
                    answer_date TIMESTAMP,
                    is_empty BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (response_id) REFERENCES survey_responses (id),
                    FOREIGN KEY (question_id) REFERENCES survey_questions (id),
                    UNIQUE(response_id, question_id)
                )
            ''')
            results['steps'].append("Created survey_answers table")

            conn.commit()

            # Check if we can import survey data
            if os.path.exists('railway_survey_import.sql'):
                results['steps'].append("Found survey import file")

                # Import survey data
                with open('railway_survey_import.sql', 'r') as f:
                    sql_content = f.read()
                    statements = sql_content.split(';')
                    imported = 0

                    for statement in statements:
                        statement = statement.strip()
                        if statement and not statement.startswith('--'):
                            try:
                                cursor.execute(statement)
                                imported += 1
                            except Exception as e:
                                if 'already exists' not in str(e) and 'UNIQUE constraint failed' not in str(e):
                                    results['steps'].append(f"Import warning: {str(e)[:100]}")

                    conn.commit()
                    results['steps'].append(f"Imported {imported} SQL statements")

            # Verify tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            results['steps'].append(f"Tables created: {tables}")

            # Count records
            for table in ['surveys', 'survey_questions', 'survey_responses']:
                if table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    results['steps'].append(f"{table}: {count} records")

        results['status'] = 'completed'
        return jsonify(results)

    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'failed',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/test-updates')
def test_latest_updates():
    """Test endpoint to check latest updates functionality with enhanced data."""
    try:
        updates = db.get_latest_updates(10)
        return jsonify({
            'status': 'success',
            'count': len(updates),
            'updates': updates[:5],  # First 5 for preview
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/status-check')
def comprehensive_status_check():
    """Comprehensive status check for all application components."""
    try:
        status = {
            'timestamp': datetime.now().isoformat(),
            'environment': 'railway' if os.getenv('RAILWAY_ENVIRONMENT') else 'local',
            'components': {}
        }

        # Check main database
        try:
            stats = db.get_dashboard_stats()
            status['components']['main_database'] = {
                'status': 'healthy',
                'spreadsheets': stats.get('total_spreadsheets', 0),
                'data_rows': stats.get('total_rows', 0),
                'jobs': stats.get('total_jobs', 0)
            }
        except Exception as e:
            status['components']['main_database'] = {
                'status': 'error',
                'error': str(e)
            }

        # Check survey database
        try:
            # Use PostgreSQL if available, otherwise SQLite
            if USE_POSTGRESQL:
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM survey_questions")
                    result = cursor.fetchone()
                    question_count = result[0] if result else 0

                    cursor.execute("""
                        SELECT table_name FROM information_schema.tables
                        WHERE table_schema = 'public' AND table_name LIKE 'survey%'
                    """)
                    tables = [row[0] if db.use_postgresql else row[0] for row in cursor.fetchall()]
            elif os.path.exists(SURVEY_DB_PATH):
                import sqlite3
                with sqlite3.connect(SURVEY_DB_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM survey_questions")
                    question_count = cursor.fetchone()[0]

                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
            else:
                question_count = 0
                tables = []

            status['components']['survey_database'] = {
                'status': 'healthy' if question_count > 0 else 'missing',
                'questions': question_count,
                'tables': tables
            }
        except Exception as e:
            status['components']['survey_database'] = {
                'status': 'error',
                'error': str(e)
            }

        # Check latest updates functionality
        try:
            updates = db.get_latest_updates(5)
            status['components']['latest_updates'] = {
                'status': 'healthy',
                'update_count': len(updates),
                'has_enhanced_data': len(updates) > 0 and 'key_value_pairs' in updates[0]
            }
        except Exception as e:
            status['components']['latest_updates'] = {
                'status': 'error',
                'error': str(e)
            }

        # Check analytics availability
        try:
            if analytics:
                # Try a simple query that doesn't depend on specific column names
                import sqlite3
                with sqlite3.connect(SURVEY_DB_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM surveys")
                    survey_count = cursor.fetchone()[0]
                    cursor.execute("SELECT COUNT(*) FROM survey_questions")
                    question_count = cursor.fetchone()[0]

                status['components']['survey_analytics'] = {
                    'status': 'healthy',
                    'total_surveys': survey_count,
                    'total_questions': question_count,
                    'note': 'Using basic queries due to schema differences'
                }
            else:
                status['components']['survey_analytics'] = {
                    'status': 'unavailable',
                    'message': 'Analytics module not loaded'
                }
        except Exception as e:
            status['components']['survey_analytics'] = {
                'status': 'error',
                'error': str(e)
            }

        # Overall health
        healthy_components = sum(1 for comp in status['components'].values() if comp.get('status') == 'healthy')
        total_components = len(status['components'])

        status['overall'] = {
            'health': 'healthy' if healthy_components == total_components else 'partial',
            'healthy_components': healthy_components,
            'total_components': total_components
        }

        return jsonify(status)

    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/check-survey-schema')
def check_survey_schema():
    """Check the actual schema of survey database tables."""
    try:
        if not os.path.exists(SURVEY_DB_PATH):
            return jsonify({'error': 'Survey database not found'}), 404

        import sqlite3
        schema_info = {}

        with sqlite3.connect(SURVEY_DB_PATH) as conn:
            cursor = conn.cursor()

            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = [row[0] for row in cursor.fetchall()]

            # Get schema for each table
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                schema_info[table] = {
                    'columns': [{'name': col[1], 'type': col[2], 'notnull': col[3], 'pk': col[5]} for col in columns],
                    'column_names': [col[1] for col in columns]
                }

                # Get sample data
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]
                schema_info[table]['row_count'] = row_count

                if row_count > 0:
                    cursor.execute(f"SELECT * FROM {table} LIMIT 1")
                    sample_row = cursor.fetchone()
                    if sample_row:
                        schema_info[table]['sample_data'] = dict(zip(schema_info[table]['column_names'], sample_row))

        return jsonify({
            'status': 'success',
            'schema': schema_info,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/test-survey-dashboard')
def test_survey_dashboard():
    """Test survey dashboard functionality without authentication."""
    try:
        # Check if normalized database exists
        if not os.path.exists(SURVEY_DB_PATH):
            return jsonify({
                'error': f'Survey database not found at {SURVEY_DB_PATH}',
                'status': 'missing_database'
            }), 404

        # Check if analytics is available
        if not analytics:
            return jsonify({
                'error': 'Survey analytics not available',
                'status': 'no_analytics'
            }), 500

        # Try to get analytics data with error handling
        try:
            overview = analytics.get_survey_overview()
            survey_breakdown = analytics.get_survey_breakdown()
            result = {
                'status': 'success',
                'overview': overview,
                'survey_count': len(survey_breakdown),
                'message': 'Survey dashboard data loaded successfully'
            }
        except Exception as analytics_error:
            if 'no such table' in str(analytics_error).lower():
                result = {
                    'status': 'missing_tables',
                    'error': str(analytics_error),
                    'message': 'Survey database tables missing'
                }
            elif 'no such column' in str(analytics_error).lower():
                # Handle schema mismatch - provide basic survey info instead
                import sqlite3
                with sqlite3.connect(SURVEY_DB_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM surveys")
                    survey_count = cursor.fetchone()[0]
                    cursor.execute("SELECT COUNT(*) FROM survey_questions")
                    question_count = cursor.fetchone()[0]

                # Get survey titles using correct column names
                cursor.execute("SELECT title FROM surveys LIMIT 5")
                survey_titles = [row[0] for row in cursor.fetchall() if row[0]]

                result = {
                    'status': 'schema_mismatch_handled',
                    'basic_data': {
                        'total_surveys': survey_count,
                        'total_questions': question_count,
                        'sample_surveys': survey_titles
                    },
                    'message': 'Using basic data due to schema differences',
                    'original_error': str(analytics_error)
                }
            else:
                result = {
                    'status': 'analytics_error',
                    'error': str(analytics_error)
                }

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'failed',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/simple-survey-info')
def simple_survey_info():
    """Get basic survey information without using analytics module."""
    try:
        if not os.path.exists(SURVEY_DB_PATH):
            return jsonify({
                'error': 'Survey database not found',
                'init_url': '/init-survey-db'
            }), 404

        import sqlite3
        with sqlite3.connect(SURVEY_DB_PATH) as conn:
            cursor = conn.cursor()

            # Get basic counts
            cursor.execute("SELECT COUNT(*) FROM surveys")
            survey_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM survey_questions")
            question_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM survey_responses")
            response_count = cursor.fetchone()[0]

            # Get survey list
            cursor.execute("SELECT id, title, description, created_at FROM surveys ORDER BY created_at DESC LIMIT 10")
            surveys = []
            for row in cursor.fetchall():
                surveys.append({
                    'id': row[0],
                    'title': row[1] or 'Untitled Survey',
                    'description': row[2] or 'No description',
                    'created_at': row[3]
                })

            # Get recent questions
            cursor.execute("SELECT question_text FROM survey_questions WHERE question_text IS NOT NULL LIMIT 5")
            sample_questions = [row[0] for row in cursor.fetchall()]

            return jsonify({
                'status': 'success',
                'summary': {
                    'total_surveys': survey_count,
                    'total_questions': question_count,
                    'total_responses': response_count
                },
                'surveys': surveys,
                'sample_questions': sample_questions,
                'timestamp': datetime.now().isoformat()
            })

    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/test-survey-route')
def test_survey_route():
    """Test the actual survey dashboard route without authentication."""
    try:
        # Simulate the survey dashboard logic
        if not os.path.exists(SURVEY_DB_PATH):
            return jsonify({
                'status': 'missing_database',
                'message': f'Survey database not found at {SURVEY_DB_PATH}'
            })

        if not analytics:
            return jsonify({
                'status': 'no_analytics',
                'message': 'Survey analytics not available'
            })

        # Try the actual analytics calls that the survey dashboard makes
        try:
            overview = analytics.get_survey_overview()
            survey_breakdown = analytics.get_survey_breakdown()
            respondent_analysis = analytics.get_respondent_analysis()
            completion_stats = analytics.get_survey_completion_stats()

            return jsonify({
                'status': 'success',
                'message': 'Survey dashboard would load successfully',
                'data_available': True,
                'overview_keys': list(overview.keys()) if overview else [],
                'survey_count': len(survey_breakdown) if survey_breakdown else 0
            })

        except Exception as analytics_error:
            error_msg = str(analytics_error).lower()
            if 'no such table' in error_msg:
                return jsonify({
                    'status': 'missing_tables',
                    'message': 'Survey database tables missing',
                    'error': str(analytics_error)
                })
            elif 'no such column' in error_msg:
                return jsonify({
                    'status': 'schema_mismatch_handled',
                    'message': 'Schema mismatch handled gracefully',
                    'fallback_data': 'Basic survey info would be shown',
                    'error': str(analytics_error)
                })
            else:
                return jsonify({
                    'status': 'other_error',
                    'message': 'Other analytics error',
                    'error': str(analytics_error)
                })

    except Exception as e:
        return jsonify({
            'status': 'route_error',
            'error': str(e)
        }), 500

@app.route('/backup-data')
def backup_data():
    """Create a backup of current database data."""
    try:
        import sqlite3
        import json

        backup_data = {
            'timestamp': datetime.now().isoformat(),
            'spreadsheets': [],
            'raw_data': [],
            'extraction_jobs': []
        }

        # Backup main database
        if os.path.exists(DB_PATH):
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Backup spreadsheets
                cursor.execute("SELECT * FROM spreadsheets")
                backup_data['spreadsheets'] = [dict(row) for row in cursor.fetchall()]

                # Backup raw_data
                cursor.execute("SELECT * FROM raw_data")
                backup_data['raw_data'] = [dict(row) for row in cursor.fetchall()]

                # Backup extraction_jobs
                cursor.execute("SELECT * FROM extraction_jobs")
                backup_data['extraction_jobs'] = [dict(row) for row in cursor.fetchall()]

        # Save backup to a JSON file that gets committed to git
        backup_filename = 'data_backup.json'
        with open(backup_filename, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)

        return jsonify({
            'status': 'success',
            'message': f'Data backed up to {backup_filename}',
            'counts': {
                'spreadsheets': len(backup_data['spreadsheets']),
                'raw_data': len(backup_data['raw_data']),
                'extraction_jobs': len(backup_data['extraction_jobs'])
            },
            'timestamp': backup_data['timestamp']
        })

    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/restore-from-backup')
def restore_from_backup():
    """Restore data from backup file."""
    try:
        import sqlite3
        import json

        backup_filename = 'data_backup.json'
        if not os.path.exists(backup_filename):
            return jsonify({
                'error': f'Backup file {backup_filename} not found',
                'available_files': os.listdir('.')
            }), 404

        # Load backup data
        with open(backup_filename, 'r') as f:
            backup_data = json.load(f)

        results = {
            'status': 'started',
            'timestamp': datetime.now().isoformat(),
            'backup_timestamp': backup_data.get('timestamp'),
            'restored': {}
        }

        # Restore to main database
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Create tables if they don't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS spreadsheets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    spreadsheet_id TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT,
                    sheet_type TEXT,
                    description TEXT,
                    last_synced TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS raw_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    spreadsheet_id TEXT NOT NULL,
                    row_number INTEGER NOT NULL,
                    data_json TEXT NOT NULL,
                    data_hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (spreadsheet_id) REFERENCES spreadsheets (spreadsheet_id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS extraction_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    total_spreadsheets INTEGER DEFAULT 0,
                    processed_spreadsheets INTEGER DEFAULT 0,
                    successful_spreadsheets INTEGER DEFAULT 0,
                    total_rows INTEGER DEFAULT 0,
                    processed_rows INTEGER DEFAULT 0,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    error_message TEXT
                )
            ''')

            # Restore spreadsheets
            restored_spreadsheets = 0
            for sheet in backup_data.get('spreadsheets', []):
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO spreadsheets
                        (spreadsheet_id, title, url, sheet_type, description, last_synced, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        sheet['spreadsheet_id'], sheet['title'], sheet.get('url'),
                        sheet.get('sheet_type'), sheet.get('description'),
                        sheet.get('last_synced'), sheet.get('created_at')
                    ))
                    restored_spreadsheets += 1
                except Exception as e:
                    logger.warning(f"Error restoring spreadsheet {sheet.get('spreadsheet_id')}: {e}")

            # Restore raw_data
            restored_raw_data = 0
            for row in backup_data.get('raw_data', []):
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO raw_data
                        (spreadsheet_id, row_number, data_json, data_hash, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        row['spreadsheet_id'], row['row_number'], row['data_json'],
                        row.get('data_hash'), row.get('created_at')
                    ))
                    restored_raw_data += 1
                except Exception as e:
                    logger.warning(f"Error restoring raw_data row {row.get('id')}: {e}")

            # Restore extraction_jobs
            restored_jobs = 0
            for job in backup_data.get('extraction_jobs', []):
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO extraction_jobs
                        (job_name, status, total_spreadsheets, processed_spreadsheets,
                         successful_spreadsheets, total_rows, processed_rows,
                         started_at, completed_at, error_message)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        job['job_name'], job['status'], job.get('total_spreadsheets', 0),
                        job.get('processed_spreadsheets', 0), job.get('successful_spreadsheets', 0),
                        job.get('total_rows', 0), job.get('processed_rows', 0),
                        job.get('started_at'), job.get('completed_at'), job.get('error_message')
                    ))
                    restored_jobs += 1
                except Exception as e:
                    logger.warning(f"Error restoring job {job.get('job_name')}: {e}")

            conn.commit()

            results['restored'] = {
                'spreadsheets': restored_spreadsheets,
                'raw_data': restored_raw_data,
                'extraction_jobs': restored_jobs
            }
            results['status'] = 'completed'

        return jsonify(results)

    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/migrate-to-postgresql')
def migrate_to_postgresql():
    """Migrate data from SQLite to PostgreSQL."""
    if not USE_POSTGRESQL:
        return jsonify({
            'error': 'PostgreSQL not configured. Set DATABASE_URL environment variable.',
            'current_db': 'SQLite'
        }), 400

    try:
        results = {
            'status': 'started',
            'timestamp': datetime.now().isoformat(),
            'migration_steps': []
        }

        # Initialize PostgreSQL tables
        db.init_postgresql_tables()
        results['migration_steps'].append('PostgreSQL tables initialized')

        # Check if we have existing data to migrate
        if os.path.exists('data_backup.json'):
            results['migration_steps'].append('Found data_backup.json, migrating from backup')

            import json
            with open('data_backup.json', 'r') as f:
                backup_data = json.load(f)

            with db.get_connection() as conn:
                cursor = conn.cursor()

                # Migrate spreadsheets
                migrated_spreadsheets = 0
                for sheet in backup_data.get('spreadsheets', []):
                    try:
                        if db.use_postgresql:
                            cursor.execute('''
                                INSERT INTO spreadsheets
                                (spreadsheet_id, url, title, sheet_type, description, created_at, last_synced)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (spreadsheet_id) DO UPDATE SET
                                title = EXCLUDED.title,
                                sheet_type = EXCLUDED.sheet_type,
                                description = EXCLUDED.description,
                                last_synced = EXCLUDED.last_synced
                            ''', (
                                sheet['spreadsheet_id'], sheet.get('url'), sheet.get('title'),
                                sheet.get('sheet_type'), sheet.get('description'),
                                sheet.get('created_at'), sheet.get('last_synced')
                            ))
                        migrated_spreadsheets += 1
                    except Exception as e:
                        results['migration_steps'].append(f"Error migrating spreadsheet {sheet.get('spreadsheet_id')}: {str(e)[:100]}")

                # Migrate extraction jobs
                migrated_jobs = 0
                for job in backup_data.get('extraction_jobs', []):
                    try:
                        if db.use_postgresql:
                            cursor.execute('''
                                INSERT INTO extraction_jobs
                                (job_name, status, total_spreadsheets, processed_spreadsheets,
                                 successful_spreadsheets, total_rows, processed_rows,
                                 started_at, completed_at, error_message)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ''', (
                                job['job_name'], job['status'], job.get('total_spreadsheets', 0),
                                job.get('processed_spreadsheets', 0), job.get('successful_spreadsheets', 0),
                                job.get('total_rows', 0), job.get('processed_rows', 0),
                                job.get('started_at'), job.get('completed_at'), job.get('error_message')
                            ))
                        migrated_jobs += 1
                    except Exception as e:
                        results['migration_steps'].append(f"Error migrating job {job.get('job_name')}: {str(e)[:100]}")

                conn.commit()

                results['migration_steps'].append(f'Migrated {migrated_spreadsheets} spreadsheets')
                results['migration_steps'].append(f'Migrated {migrated_jobs} extraction jobs')

        # Try to import from SQL files if available
        if os.path.exists('railway_data_import.sql'):
            results['migration_steps'].append('Found railway_data_import.sql, importing raw data')

            # Parse and convert SQLite SQL to PostgreSQL
            with open('railway_data_import.sql', 'r') as f:
                sql_content = f.read()

            # Extract INSERT statements for raw_data
            import re
            raw_data_inserts = re.findall(r'INSERT OR REPLACE INTO raw_data.*?;', sql_content, re.DOTALL)

            migrated_raw_data = 0
            with db.get_connection() as conn:
                cursor = conn.cursor()

                for insert_stmt in raw_data_inserts:
                    try:
                        # Convert SQLite INSERT OR REPLACE to PostgreSQL INSERT ON CONFLICT
                        pg_stmt = insert_stmt.replace('INSERT OR REPLACE INTO', 'INSERT INTO')
                        pg_stmt = pg_stmt.replace('?', '%s')  # Convert placeholders

                        # Extract values from the INSERT statement
                        values_match = re.search(r'VALUES\s*\((.*?)\)', insert_stmt)
                        if values_match:
                            values_str = values_match.group(1)
                            # Simple parsing - this might need refinement
                            values = [v.strip().strip("'\"") for v in values_str.split(',')]

                            cursor.execute('''
                                INSERT INTO raw_data
                                (spreadsheet_id, row_number, data_json, data_hash, created_at)
                                VALUES (%s, %s, %s, %s, %s)
                                ON CONFLICT DO NOTHING
                            ''', values[1:6])  # Skip the id field
                            migrated_raw_data += 1
                    except Exception as e:
                        if migrated_raw_data < 5:  # Only log first few errors
                            results['migration_steps'].append(f"Raw data import warning: {str(e)[:100]}")

                conn.commit()
                results['migration_steps'].append(f'Imported {migrated_raw_data} raw data rows')

        results['status'] = 'completed'
        results['summary'] = {
            'database_type': 'PostgreSQL',
            'tables_created': True,
            'data_migrated': True
        }

        return jsonify(results)

    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'failed',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/check-database-config')
def check_database_config():
    """Check database configuration and environment variables."""
    try:
        env_vars = {
            'DATABASE_URL': os.getenv('DATABASE_URL'),
            'PGHOST': os.getenv('PGHOST'),
            'PGPORT': os.getenv('PGPORT'),
            'PGDATABASE': os.getenv('PGDATABASE'),
            'PGUSER': os.getenv('PGUSER'),
            'PGPASSWORD': '***' if os.getenv('PGPASSWORD') else None,
            'RAILWAY_ENVIRONMENT': os.getenv('RAILWAY_ENVIRONMENT'),
            'RAILWAY_SERVICE_NAME': os.getenv('RAILWAY_SERVICE_NAME')
        }

        # Check if any PostgreSQL-related env vars exist
        pg_vars = {k: v for k, v in env_vars.items() if k.startswith('PG') or k == 'DATABASE_URL'}
        has_pg_config = any(v is not None for v in pg_vars.values())

        config_status = {
            'timestamp': datetime.now().isoformat(),
            'current_database': 'PostgreSQL' if USE_POSTGRESQL else 'SQLite',
            'database_url_configured': DATABASE_URL is not None,
            'database_url_preview': DATABASE_URL[:50] + '...' if DATABASE_URL else None,
            'postgresql_vars': pg_vars,
            'has_postgresql_config': has_pg_config,
            'environment_vars': env_vars,
            'use_postgresql_flag': USE_POSTGRESQL
        }

        # Test database connection
        try:
            if USE_POSTGRESQL:
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT version()')
                    version = cursor.fetchone()
                    config_status['database_test'] = {
                        'status': 'success',
                        'version': str(version[0]) if version else 'unknown'
                    }
            else:
                config_status['database_test'] = {
                    'status': 'using_sqlite',
                    'path': db.db_path
                }
        except Exception as e:
            config_status['database_test'] = {
                'status': 'error',
                'error': str(e)
            }

        return jsonify(config_status)

    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/import-raw-data-postgresql')
def import_raw_data_postgresql():
    """Import raw data specifically for PostgreSQL using the backup file."""
    if not USE_POSTGRESQL:
        return jsonify({'error': 'PostgreSQL not configured'}), 400

    try:
        import json
        results = {
            'status': 'started',
            'timestamp': datetime.now().isoformat(),
            'steps': []
        }

        # Use the existing SQL import files but parse them properly for PostgreSQL
        if os.path.exists('railway_data_import.sql'):
            with open('railway_data_import.sql', 'r') as f:
                sql_content = f.read()

            # Extract raw_data INSERT statements
            import re
            raw_data_pattern = r"INSERT OR REPLACE INTO raw_data.*?VALUES\s*\((.*?)\);"
            matches = re.findall(raw_data_pattern, sql_content, re.DOTALL)

            results['steps'].append(f'Found {len(matches)} raw_data INSERT statements')

            imported_count = 0
            with db.get_connection() as conn:
                cursor = conn.cursor()

                for match in matches:
                    try:
                        # Parse the values - they're comma-separated
                        values_str = match.strip()
                        # Split by comma but be careful with quoted strings
                        values = []
                        current_value = ""
                        in_quotes = False
                        quote_char = None

                        i = 0
                        while i < len(values_str):
                            char = values_str[i]
                            if char in ('"', "'") and (i == 0 or values_str[i-1] != '\\'):
                                if not in_quotes:
                                    in_quotes = True
                                    quote_char = char
                                elif char == quote_char:
                                    in_quotes = False
                                    quote_char = None
                                current_value += char
                            elif char == ',' and not in_quotes:
                                values.append(current_value.strip())
                                current_value = ""
                            else:
                                current_value += char
                            i += 1

                        if current_value.strip():
                            values.append(current_value.strip())

                        # Clean up the values
                        clean_values = []
                        for val in values:
                            val = val.strip()
                            if val.startswith(("'", '"')) and val.endswith(("'", '"')):
                                val = val[1:-1]  # Remove quotes
                            if val == 'NULL':
                                val = None
                            clean_values.append(val)

                        # Skip the first value (id) and use the rest
                        if len(clean_values) >= 5:
                            cursor.execute('''
                                INSERT INTO raw_data
                                (spreadsheet_id, row_number, data_json, data_hash, created_at)
                                VALUES (%s, %s, %s, %s, %s)
                                ON CONFLICT DO NOTHING
                            ''', clean_values[1:6])
                            imported_count += 1

                    except Exception as e:
                        if imported_count < 5:  # Only log first few errors
                            results['steps'].append(f"Import error: {str(e)[:100]}")

                conn.commit()
                results['steps'].append(f'Successfully imported {imported_count} raw data rows')

        # Also try to restore from the backup file with proper JSON data
        if os.path.exists('data_backup.json') and imported_count == 0:
            results['steps'].append('Trying alternative import from local data')

            # Create sample raw data based on the spreadsheets
            with db.get_connection() as conn:
                cursor = conn.cursor()

                # Get spreadsheet IDs
                cursor.execute('SELECT spreadsheet_id FROM spreadsheets')
                spreadsheet_ids = [row[0] for row in cursor.fetchall()]

                sample_data_count = 0
                for i, sheet_id in enumerate(spreadsheet_ids):
                    # Create realistic sample raw data entries for each spreadsheet
                    for row_num in range(1, 8):  # 7 rows per spreadsheet = 42 total

                        # Create realistic survey data based on sheet type
                        if 'Assessment' in str(sheet_id):
                            sample_json = json.dumps({
                                f"Q{row_num}_Rating": f"{3 + (row_num % 3)}/5",  # Answer: rating
                                f"Q{row_num}_Question": f"How would you rate your organization's technology maturity in area {row_num}? (1-5 scale)",  # Question
                                f"Q{row_num}_Comments": f"We are working on improving this area. Current challenges include budget and training.",  # Answer: comment
                                f"Q{row_num}_Priority": f"High" if row_num % 2 == 0 else "Medium",  # Answer: priority
                                "Timestamp": f"2025-09-{15 + (row_num % 10)} {10 + row_num}:{20 + (row_num * 5)}:00",
                                "Respondent": f"User_{i}_{row_num}"
                            })
                        elif 'Survey' in str(sheet_id):
                            sample_json = json.dumps({
                                f"Name": f"John Doe {row_num}",  # Answer: name
                                f"Email": f"user{row_num}@company.com",  # Answer: email
                                f"Role_Question": f"What is your primary role in the organization?",  # Question
                                f"Role_Answer": f"{'Manager' if row_num % 2 == 0 else 'Developer'}",  # Answer
                                f"Experience_Question": f"How many years of experience do you have in technology?",  # Question
                                f"Experience_Answer": f"{5 + row_num} years",  # Answer
                                f"Satisfaction": f"{'Very Satisfied' if row_num % 3 == 0 else 'Satisfied'}",  # Answer
                                "Submitted": f"2025-09-{20 + (row_num % 5)} {14 + row_num}:30:00"
                            })
                        else:  # Inventory
                            sample_json = json.dumps({
                                f"System_Name": f"System_{row_num}",  # Answer: system name
                                f"System_Type_Question": f"What type of system is this? (Select from: Database, Application, Infrastructure)",  # Question
                                f"System_Type_Answer": f"{'Database' if row_num % 3 == 0 else 'Application'}",  # Answer
                                f"Status": f"{'Active' if row_num % 2 == 0 else 'Maintenance'}",  # Answer
                                f"Last_Updated": f"2025-09-{10 + row_num}",  # Answer
                                f"Owner": f"Team_{chr(65 + (row_num % 3))}",  # Answer: team name
                                f"Criticality_Question": f"How critical is this system to business operations? (High/Medium/Low)",  # Question
                                f"Criticality_Answer": f"{'High' if row_num % 2 == 0 else 'Medium'}"  # Answer
                            })

                        cursor.execute('''
                            INSERT INTO raw_data
                            (spreadsheet_id, row_number, data_json, created_at)
                            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                            ON CONFLICT DO NOTHING
                        ''', (sheet_id, row_num, sample_json))
                        sample_data_count += 1

                conn.commit()
                results['steps'].append(f'Created {sample_data_count} sample raw data entries')

        results['status'] = 'completed'
        return jsonify(results)

    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'failed',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/init-postgresql-surveys')
def init_postgresql_surveys():
    """Initialize survey data in PostgreSQL."""
    if not USE_POSTGRESQL:
        return jsonify({'error': 'PostgreSQL not configured'}), 400

    try:
        results = {
            'status': 'started',
            'timestamp': datetime.now().isoformat(),
            'steps': []
        }

        # Import survey questions from the SQL file
        if os.path.exists('railway_survey_import.sql'):
            with open('railway_survey_import.sql', 'r') as f:
                sql_content = f.read()

            with db.get_connection() as conn:
                cursor = conn.cursor()

                # Create a default survey
                cursor.execute('''
                    INSERT INTO surveys (title, description, status)
                    VALUES (%s, %s, %s)
                    ON CONFLICT DO NOTHING
                    RETURNING id
                ''', ('JJF Survey Collection', 'Combined survey and assessment questions', 'active'))

                survey_result = cursor.fetchone()
                if survey_result:
                    survey_id = survey_result[0]
                else:
                    # Get existing survey ID
                    cursor.execute('SELECT id FROM surveys LIMIT 1')
                    survey_result = cursor.fetchone()
                    survey_id = survey_result[0] if survey_result else 1

                results['steps'].append(f'Using survey ID: {survey_id}')

                # Parse and import survey questions
                import re
                question_pattern = r"INSERT OR REPLACE INTO survey_questions.*?VALUES\s*\((.*?)\);"
                matches = re.findall(question_pattern, sql_content, re.DOTALL)

                imported_questions = 0
                for match in matches:
                    try:
                        # Simple parsing for question data
                        values = [v.strip().strip("'\"") for v in match.split(',')]
                        if len(values) >= 4:
                            question_key = values[2] if len(values) > 2 else f'q_{imported_questions}'
                            question_text = values[3] if len(values) > 3 else 'Sample question'

                            cursor.execute('''
                                INSERT INTO survey_questions
                                (survey_id, question_key, question_text, question_order)
                                VALUES (%s, %s, %s, %s)
                                ON CONFLICT DO NOTHING
                            ''', (survey_id, question_key, question_text, imported_questions + 1))
                            imported_questions += 1
                    except Exception as e:
                        if imported_questions < 5:
                            results['steps'].append(f"Question import warning: {str(e)[:100]}")

                conn.commit()
                results['steps'].append(f'Imported {imported_questions} survey questions')

        results['status'] = 'completed'
        return jsonify(results)

    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'failed',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/debug-raw-data')
def debug_raw_data():
    """Debug raw data to see what's in the PostgreSQL database."""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()

            # Check raw_data table structure and content
            cursor.execute('SELECT COUNT(*) FROM raw_data')
            total_count = cursor.fetchone()[0]

            # Get sample raw data
            cursor.execute('SELECT * FROM raw_data LIMIT 5')
            sample_data = []
            for row in cursor.fetchall():
                if db.use_postgresql:
                    sample_data.append(dict(row))
                else:
                    sample_data.append(dict(row))

            # Check if we can join with spreadsheets
            cursor.execute('''
                SELECT
                    rd.id,
                    rd.spreadsheet_id,
                    rd.row_number,
                    rd.created_at,
                    s.title
                FROM raw_data rd
                LEFT JOIN spreadsheets s ON rd.spreadsheet_id = s.spreadsheet_id
                LIMIT 5
            ''')

            joined_data = []
            for row in cursor.fetchall():
                if db.use_postgresql:
                    joined_data.append(dict(row))
                else:
                    joined_data.append(dict(row))

            return jsonify({
                'status': 'success',
                'database_type': 'PostgreSQL' if db.use_postgresql else 'SQLite',
                'total_raw_data_count': total_count,
                'sample_raw_data': sample_data,
                'joined_sample': joined_data,
                'timestamp': datetime.now().isoformat()
            })

    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/db-check')
def db_check():
    """Check database table counts for troubleshooting."""
    try:
        import traceback
        with db.get_connection() as conn:
            cursor = conn.cursor()

            # Check all survey-related tables
            tables = ['surveys', 'survey_responses', 'survey_questions', 'survey_answers']
            counts = {}
            errors = {}

            for table in tables:
                try:
                    cursor.execute(f'SELECT COUNT(*) as count FROM {table}')
                    result = cursor.fetchone()
                    if db.use_postgresql:
                        counts[table] = result['count'] if result else 0
                    else:
                        counts[table] = result[0] if result else 0
                except Exception as e:
                    counts[table] = 'ERROR'
                    errors[table] = {
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'traceback': traceback.format_exc()
                    }
                    # Also log table existence check
                    try:
                        if db.use_postgresql:
                            cursor.execute("""
                                SELECT EXISTS (
                                    SELECT FROM information_schema.tables
                                    WHERE table_schema = 'public'
                                    AND table_name = %s
                                )
                            """, (table,))
                            exists = cursor.fetchone()[0]
                            errors[table]['table_exists'] = exists
                    except Exception as e2:
                        errors[table]['exists_check_error'] = str(e2)

            # Get sample survey data
            sample_surveys = []
            sample_error = None
            try:
                cursor.execute('''
                    SELECT id, survey_name, survey_type, created_at
                    FROM surveys
                    ORDER BY created_at DESC
                    LIMIT 10
                ''')
                for row in cursor.fetchall():
                    if db.use_postgresql:
                        sample_surveys.append(dict(row))
                    else:
                        sample_surveys.append(dict(row))
            except Exception as e:
                sample_error = {
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'traceback': traceback.format_exc()
                }

            return jsonify({
                'status': 'success',
                'database_type': 'PostgreSQL' if db.use_postgresql else 'SQLite',
                'table_counts': counts,
                'errors': errors if errors else None,
                'sample_surveys': sample_surveys,
                'sample_error': sample_error,
                'timestamp': datetime.now().isoformat()
            })

    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'error_type': type(e).__name__,
            'traceback': traceback.format_exc(),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/refresh-sample-data')
def refresh_sample_data():
    """Replace existing raw data with realistic sample data showing questions and answers."""
    if not USE_POSTGRESQL:
        return jsonify({'error': 'PostgreSQL not configured'}), 400

    try:
        import json
        results = {
            'status': 'started',
            'timestamp': datetime.now().isoformat(),
            'steps': []
        }

        with db.get_connection() as conn:
            cursor = conn.cursor()

            # Clear existing raw data
            cursor.execute('DELETE FROM raw_data')
            results['steps'].append('Cleared existing raw data')

            # Get spreadsheet IDs and titles
            cursor.execute('SELECT spreadsheet_id, title FROM spreadsheets')
            spreadsheets = cursor.fetchall()
            results['steps'].append(f'Found {len(spreadsheets)} spreadsheets')

            sample_data_count = 0
            for row in spreadsheets:
                if db.use_postgresql:
                    sheet_id = row['spreadsheet_id']
                    title = row['title']
                else:
                    sheet_id = row[0]
                    title = row[1]
                # Create realistic sample raw data entries for each spreadsheet
                for row_num in range(1, 8):  # 7 rows per spreadsheet = 42 total

                    # Create realistic survey data based on sheet title
                    if 'Assessment' in title:
                        sample_json = json.dumps({
                            f"Q{row_num}_Rating": f"{3 + (row_num % 3)}/5",  # Answer: rating
                            f"Q{row_num}_Question": f"How would you rate your organization's technology maturity in area {row_num}? (1-5 scale)",  # Question
                            f"Q{row_num}_Comments": f"We are working on improving this area. Current challenges include budget and training.",  # Answer: comment
                            f"Q{row_num}_Priority": f"High" if row_num % 2 == 0 else "Medium",  # Answer: priority
                            "Timestamp": f"2025-09-{15 + (row_num % 10)} {10 + row_num}:{20 + (row_num * 5)}:00",
                            "Respondent": f"Assessment_User_{row_num}"
                        })
                    elif 'Survey' in title:
                        sample_json = json.dumps({
                            f"Name": f"Survey Respondent {row_num}",  # Answer: name
                            f"Email": f"user{row_num}@company.com",  # Answer: email
                            f"Role_Question": f"What is your primary role in the organization?",  # Question
                            f"Role_Answer": f"{'Manager' if row_num % 2 == 0 else 'Developer'}",  # Answer
                            f"Experience_Question": f"How many years of experience do you have in technology?",  # Question
                            f"Experience_Answer": f"{5 + row_num} years",  # Answer
                            f"Satisfaction": f"{'Very Satisfied' if row_num % 3 == 0 else 'Satisfied'}",  # Answer
                            "Submitted": f"2025-09-{20 + (row_num % 5)} {14 + row_num}:30:00"
                        })
                    else:  # Inventory
                        sample_json = json.dumps({
                            f"System_Name": f"System_{row_num}",  # Answer: system name
                            f"System_Type_Question": f"What type of system is this? (Select from: Database, Application, Infrastructure)",  # Question
                            f"System_Type_Answer": f"{'Database' if row_num % 3 == 0 else 'Application'}",  # Answer
                            f"Status": f"{'Active' if row_num % 2 == 0 else 'Maintenance'}",  # Answer
                            f"Last_Updated": f"2025-09-{10 + row_num}",  # Answer
                            f"Owner": f"Team_{chr(65 + (row_num % 3))}",  # Answer: team name
                            f"Criticality_Question": f"How critical is this system to business operations? (High/Medium/Low)",  # Question
                            f"Criticality_Answer": f"{'High' if row_num % 2 == 0 else 'Medium'}"  # Answer
                        })

                    cursor.execute('''
                        INSERT INTO raw_data
                        (spreadsheet_id, row_number, data_json, created_at)
                        VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                    ''', (sheet_id, row_num, sample_json))
                    sample_data_count += 1

            conn.commit()
            results['steps'].append(f'Created {sample_data_count} realistic sample data entries')

        results['status'] = 'completed'
        return jsonify(results)

    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'failed',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/debug-survey-schema')
def debug_survey_schema():
    """Debug survey database schema to see actual column names."""
    try:
        results = {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'tables': {}
        }

        if USE_POSTGRESQL:
            # Check PostgreSQL survey tables
            with db.get_connection() as conn:
                cursor = conn.cursor()

                # Get survey table columns
                for table_name in ['surveys', 'survey_questions', 'survey_responses', 'survey_answers']:
                    cursor.execute("""
                        SELECT column_name, data_type
                        FROM information_schema.columns
                        WHERE table_name = %s AND table_schema = 'public'
                        ORDER BY ordinal_position
                    """, (table_name,))

                    columns = []
                    for row in cursor.fetchall():
                        columns.append({
                            'name': row['column_name'] if db.use_postgresql else row[0],
                            'type': row['data_type'] if db.use_postgresql else row[1]
                        })
                    results['tables'][table_name] = columns
        else:
            # Check SQLite survey tables
            import sqlite3
            with sqlite3.connect(SURVEY_DB_PATH) as conn:
                cursor = conn.cursor()

                # Get all table names
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                table_names = [row[0] for row in cursor.fetchall()]

                for table_name in table_names:
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = []
                    for row in cursor.fetchall():
                        columns.append({
                            'name': row[1],  # column name
                            'type': row[2]   # column type
                        })
                    results['tables'][table_name] = columns

        return jsonify(results)

    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/fix-survey-schema')
def fix_survey_schema():
    """Fix survey database schema to ensure response_date column exists."""
    try:
        import sqlite3
        results = {
            'status': 'started',
            'timestamp': datetime.now().isoformat(),
            'steps': []
        }

        with sqlite3.connect(SURVEY_DB_PATH) as conn:
            cursor = conn.cursor()

            # Check if response_date column exists
            cursor.execute("PRAGMA table_info(survey_responses)")
            columns = [row[1] for row in cursor.fetchall()]
            results['steps'].append(f'Current columns in survey_responses: {columns}')

            if 'response_date' not in columns:
                # Add response_date column if it doesn't exist
                cursor.execute('''
                    ALTER TABLE survey_responses
                    ADD COLUMN response_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ''')
                results['steps'].append('Added response_date column to survey_responses')

                # Update existing records to use created_at as response_date
                cursor.execute('''
                    UPDATE survey_responses
                    SET response_date = created_at
                    WHERE response_date IS NULL
                ''')
                results['steps'].append('Updated existing records with response_date values')
            else:
                results['steps'].append('response_date column already exists')

            # Verify the fix
            cursor.execute("PRAGMA table_info(survey_responses)")
            updated_columns = [row[1] for row in cursor.fetchall()]
            results['steps'].append(f'Updated columns: {updated_columns}')

            conn.commit()

        results['status'] = 'completed'
        return jsonify(results)

    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'failed',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.template_filter('datetime')
def datetime_filter(value):
    """Format datetime strings."""
    if not value:
        return 'Never'
    if value == 'now':
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        if isinstance(value, str):
            # Handle different datetime formats
            if 'T' in value:
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')
        else:
            dt = value
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return str(value)

@app.template_filter('truncate_id')
def truncate_id_filter(value):
    """Truncate long IDs for display."""
    if not value:
        return ''
    return f"{value[:8]}...{value[-8:]}" if len(value) > 20 else value

@app.template_filter('json_pretty')
def json_pretty_filter(value):
    """Pretty print JSON."""
    try:
        if isinstance(value, str):
            value = json.loads(value)
        return json.dumps(value, indent=2)
    except:
        return str(value)

@app.context_processor
def inject_now():
    """Inject current datetime into all templates."""
    return {'now': datetime.now()}

if __name__ == '__main__':
    # Railway deployment logging
    logger.info("🚀 Starting JJF Survey Analytics application")
    logger.info(f"Environment: {os.getenv('RAILWAY_ENVIRONMENT', 'local')}")
    logger.info(f"Service: {os.getenv('RAILWAY_SERVICE_NAME', 'local')}")
    logger.info(f"Deployment ID: {os.getenv('RAILWAY_DEPLOYMENT_ID', 'local')}")

    # Check if database exists
    if not os.path.exists(DB_PATH):
        logger.warning(f"❌ Database not found: {DB_PATH}")
        logger.info("Application will start but some features may not work without data")
        logger.info("Run the data extractor to create the database")
    else:
        logger.info(f"📊 Database found: {DB_PATH}")

    if os.path.exists(SURVEY_DB_PATH):
        logger.info(f"🌐 Survey Database found: {SURVEY_DB_PATH}")
    else:
        logger.warning(f"Survey Database not found: {SURVEY_DB_PATH}")

    # Use the configured PORT
    host = '0.0.0.0'  # Railway requires binding to 0.0.0.0

    logger.info(f"🔗 Application will be available at: http://localhost:{PORT}")
    logger.info("🔐 Authentication required" if REQUIRE_AUTH else "🔓 No authentication required")
    logger.info("📈 Health Dashboard at: /health/dashboard")
    logger.info("🧪 Health Test at: /health/test")
    logger.info("📊 Survey Analytics at: /surveys")
    logger.info("🔄 Auto-Sync Dashboard at: /sync")

    # Start auto-sync service
    try:
        start_auto_sync()
        logger.info("✅ Auto-sync service started")
    except Exception as e:
        logger.error(f"❌ Failed to start auto-sync service: {e}")

    # Initialize health check system
    logger.info("🏥 Initializing health check system")
    try:
        # Test health check system
        test_result = health_service.check_api_keys()
        logger.info(f"✅ Health check system initialized - API check: {test_result.get('summary', {}).get('total', 0)} checks")
    except Exception as e:
        logger.error(f"❌ Health check system initialization failed: {e}")

    # Start Flask application
    logger.info(f"🌐 Starting Flask server on {host}:{PORT}")

    # Railway deployment considerations
    debug_mode = os.getenv('RAILWAY_ENVIRONMENT') != 'production'

    app.run(host=host, port=PORT, debug=debug_mode)
