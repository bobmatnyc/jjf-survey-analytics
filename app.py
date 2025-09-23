#!/usr/bin/env python3
"""
Surveyor Data Viewer - Flask Web Application

A simple web interface for viewing Google Sheets survey data
using Flask and Tailwind CSS.
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any
import math
from survey_analytics import SurveyAnalytics
from auto_sync_service import get_auto_sync_service, start_auto_sync

app = Flask(__name__)
app.config['SECRET_KEY'] = 'surveyor-data-viewer-2025'

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

@app.route('/')
def dashboard():
    """Dashboard with overview statistics."""
    try:
        stats = db.get_dashboard_stats()
        spreadsheets = db.get_spreadsheets()
        return render_template('dashboard.html', stats=stats, spreadsheets=spreadsheets)
    except Exception as e:
        return render_template('error.html', error=str(e)), 500

@app.route('/spreadsheets')
def spreadsheets():
    """List all spreadsheets."""
    try:
        spreadsheets_data = db.get_spreadsheets()
        return render_template('spreadsheets.html', spreadsheets=spreadsheets_data)
    except Exception as e:
        return render_template('error.html', error=str(e)), 500

@app.route('/spreadsheet/<spreadsheet_id>')
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
    # Check if database exists
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        print("Please run the data extractor first to create the database.")
        exit(1)
    
    print("🚀 Starting Surveyor Data Viewer...")
    print(f"📊 Database: {DB_PATH}")
    print("🌐 Open http://localhost:5001 in your browser")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
