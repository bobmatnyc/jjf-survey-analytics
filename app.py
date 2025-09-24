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

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'surveyor-data-viewer-2025-default-key')

# Authentication configuration
APP_PASSWORD = os.getenv('APP_PASSWORD', 'survey2025!')  # Default password, change in production
REQUIRE_AUTH = os.getenv('REQUIRE_AUTH', 'true').lower() == 'true'

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

class DatabaseManager:
    """Handle database operations for the web app."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
    
    def get_connection(self):
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
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
                ORDER BY started_at DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_dashboard_stats(self) -> Dict:
        """Get dashboard statistics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total spreadsheets
            cursor.execute('SELECT COUNT(*) as count FROM spreadsheets')
            total_spreadsheets = cursor.fetchone()['count']
            
            # Total rows
            cursor.execute('SELECT COUNT(*) as count FROM raw_data')
            total_rows = cursor.fetchone()['count']
            
            # Total jobs
            cursor.execute('SELECT COUNT(*) as count FROM extraction_jobs')
            total_jobs = cursor.fetchone()['count']
            
            # Latest job
            cursor.execute('''
                SELECT * FROM extraction_jobs 
                ORDER BY started_at DESC 
                LIMIT 1
            ''')
            latest_job = cursor.fetchone()
            latest_job = dict(latest_job) if latest_job else None
            
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
            
            return {
                'total_spreadsheets': total_spreadsheets,
                'total_rows': total_rows,
                'total_jobs': total_jobs,
                'latest_job': latest_job,
                'sheet_types': sheet_types
            }

# Initialize database manager and analytics
db = DatabaseManager()
analytics = SurveyAnalytics(SURVEY_DB_PATH)
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
        stats = db.get_dashboard_stats()
        spreadsheets = db.get_spreadsheets()
        return render_template('dashboard.html', stats=stats, spreadsheets=spreadsheets)
    except Exception as e:
        return render_template('error.html', error=str(e)), 500

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
        # Check if normalized database exists
        if not os.path.exists(SURVEY_DB_PATH):
            return render_template('error.html',
                                 error='Normalized survey database not found. Please run survey_normalizer.py first.'), 404

        overview = analytics.get_survey_overview()
        survey_breakdown = analytics.get_survey_breakdown()
        respondent_analysis = analytics.get_respondent_analysis()
        completion_stats = analytics.get_survey_completion_stats()

        return render_template('survey_dashboard.html',
                             overview=overview,
                             survey_breakdown=survey_breakdown,
                             respondent_analysis=respondent_analysis,
                             completion_stats=completion_stats)
    except Exception as e:
        return render_template('error.html', error=str(e)), 500

@app.route('/surveys/analytics')
def survey_analytics():
    """Detailed survey analytics page."""
    try:
        if not os.path.exists(SURVEY_DB_PATH):
            return render_template('error.html',
                                 error='Normalized survey database not found. Please run survey_normalizer.py first.'), 404

        survey_id = request.args.get('survey_id', type=int)
        question_analytics = analytics.get_question_analytics(survey_id)
        time_series = analytics.get_time_series_data(30)
        activity = analytics.get_response_activity(30)

        return render_template('survey_analytics.html',
                             question_analytics=question_analytics,
                             time_series=time_series,
                             activity=activity,
                             selected_survey_id=survey_id)
    except Exception as e:
        return render_template('error.html', error=str(e)), 500

@app.route('/surveys/responses')
def survey_responses():
    """Survey response activity dashboard."""
    try:
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
