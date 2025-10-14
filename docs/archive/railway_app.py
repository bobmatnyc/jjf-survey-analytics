#!/usr/bin/env python3
"""
Railway-optimized version of JJF Survey Analytics
Simplified startup with better error handling for Railway deployment
"""

import os
import sys
import logging
import traceback
from datetime import datetime

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Log startup
logger.info("🚂 Starting JJF Survey Analytics on Railway")
logger.info(f"Python version: {sys.version}")
logger.info(f"Working directory: {os.getcwd()}")
logger.info(f"Environment: {os.getenv('RAILWAY_ENVIRONMENT', 'unknown')}")

try:
    from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
    logger.info("✅ Flask imported successfully")
except ImportError as e:
    logger.error(f"❌ Failed to import Flask: {e}")
    sys.exit(1)

# Create Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'surveyor-data-viewer-2025-default-key')
APP_PASSWORD = os.getenv('APP_PASSWORD', 'survey2025!')
REQUIRE_AUTH = os.getenv('REQUIRE_AUTH', 'true').lower() == 'true'
PORT = int(os.getenv('PORT', 5001))

logger.info(f"🔧 Configuration:")
logger.info(f"  Port: {PORT}")
logger.info(f"  Authentication: {REQUIRE_AUTH}")
logger.info(f"  Password configured: {'Yes' if APP_PASSWORD else 'No'}")

# Authentication decorator
def require_auth(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not REQUIRE_AUTH:
            return f(*args, **kwargs)
        if 'authenticated' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Basic routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if not REQUIRE_AUTH:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        next_url = request.form.get('next') or url_for('dashboard')
        
        if password == APP_PASSWORD:
            session['authenticated'] = True
            logger.info(f"✅ Successful login from {request.remote_addr}")
            flash('Successfully logged in!', 'success')
            return redirect(next_url)
        else:
            logger.warning(f"❌ Failed login attempt from {request.remote_addr}")
            flash('Invalid password. Please try again.', 'error')
    
    next_url = request.args.get('next', url_for('dashboard'))
    return render_template('login.html', next_url=next_url)

@app.route('/logout')
def logout():
    """Logout."""
    session.pop('authenticated', None)
    logger.info(f"👋 User logged out from {request.remote_addr}")
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/')
@require_auth
def dashboard():
    """Main dashboard."""
    try:
        # Try to load main functionality
        import sqlite3
        
        # Check for databases
        db_files = ['surveyor_data_improved.db', 'survey_normalized.db', 'surveyor_data.db']
        found_dbs = [db for db in db_files if os.path.exists(db)]
        
        return render_template('dashboard.html', 
                             databases=found_dbs,
                             timestamp=datetime.now().isoformat())
    except Exception as e:
        logger.error(f"❌ Dashboard error: {e}")
        return render_template('error.html', error=str(e)), 500

@app.route('/health')
def health_check():
    """Health check for Railway."""
    try:
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "railway_info": {
                "environment": os.getenv("RAILWAY_ENVIRONMENT", "unknown"),
                "service_name": os.getenv("RAILWAY_SERVICE_NAME", "unknown"),
                "deployment_id": os.getenv("RAILWAY_DEPLOYMENT_ID", "unknown")
            },
            "system_info": {
                "python_version": sys.version,
                "working_directory": os.getcwd(),
                "port": PORT,
                "auth_required": REQUIRE_AUTH
            }
        }
        
        # Check basic functionality
        import sqlite3
        health_data["sqlite_available"] = True
        
        # Check for database files
        db_files = ['surveyor_data_improved.db', 'survey_normalized.db', 'surveyor_data.db']
        found_dbs = [db for db in db_files if os.path.exists(db)]
        health_data["databases_found"] = len(found_dbs)
        health_data["database_files"] = found_dbs
        
        logger.info(f"✅ Health check passed: {len(found_dbs)} databases found")
        return jsonify(health_data), 200
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@app.route('/health/status')
def health_status():
    """Quick health status for Railway monitoring."""
    try:
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "port": PORT
        }), 200
    except Exception as e:
        logger.error(f"❌ Health status failed: {e}")
        return jsonify({
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 500

@app.route('/health/test')
def health_test():
    """Test endpoint for Railway deployment verification."""
    return jsonify({
        "message": "JJF Survey Analytics is running on Railway",
        "timestamp": datetime.now().isoformat(),
        "railway_info": {
            "environment": os.getenv("RAILWAY_ENVIRONMENT", "unknown"),
            "service_name": os.getenv("RAILWAY_SERVICE_NAME", "unknown"),
            "deployment_id": os.getenv("RAILWAY_DEPLOYMENT_ID", "unknown"),
            "port": os.getenv("PORT", "unknown")
        },
        "system_info": {
            "python_version": sys.version,
            "working_directory": os.getcwd(),
            "files_in_directory": os.listdir('.'),
            "environment_vars": {
                "PORT": os.getenv("PORT"),
                "RAILWAY_ENVIRONMENT": os.getenv("RAILWAY_ENVIRONMENT"),
                "REQUIRE_AUTH": os.getenv("REQUIRE_AUTH"),
                "APP_PASSWORD": "set" if os.getenv("APP_PASSWORD") else "not_set",
                "GOOGLE_CREDENTIALS_FILE": os.getenv("GOOGLE_CREDENTIALS_FILE")
            }
        }
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', 
                         error="Page not found", 
                         error_code=404), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"❌ Internal server error: {error}")
    return render_template('error.html', 
                         error="Internal server error", 
                         error_code=500), 500

# Try to import and initialize advanced features
try:
    logger.info("🔄 Attempting to load advanced features...")
    
    # Try to import survey analytics
    try:
        from survey_analytics import SurveyAnalytics
        SURVEY_DB_PATH = 'survey_normalized.db'
        if os.path.exists(SURVEY_DB_PATH):
            analytics = SurveyAnalytics(SURVEY_DB_PATH)
            logger.info("✅ Survey analytics loaded")
        else:
            logger.warning(f"⚠️ Survey database not found: {SURVEY_DB_PATH}")
            analytics = None
    except ImportError as e:
        logger.warning(f"⚠️ Survey analytics not available: {e}")
        analytics = None
    
    # Try to import auto-sync
    try:
        from auto_sync_service import get_auto_sync_service, start_auto_sync
        auto_sync = get_auto_sync_service()
        logger.info("✅ Auto-sync service loaded")
    except ImportError as e:
        logger.warning(f"⚠️ Auto-sync service not available: {e}")
        auto_sync = None
    
    # Add advanced routes if available
    if analytics:
        @app.route('/surveys')
        @require_auth
        def survey_dashboard():
            """Survey analytics dashboard."""
            try:
                return render_template('survey_dashboard.html', analytics=analytics)
            except Exception as e:
                logger.error(f"❌ Survey dashboard error: {e}")
                return render_template('error.html', error=str(e)), 500
    
    logger.info("✅ Advanced features loaded successfully")
    
except Exception as e:
    logger.warning(f"⚠️ Some advanced features unavailable: {e}")

if __name__ == '__main__':
    logger.info("🚀 Starting Flask application")
    logger.info(f"🌐 Server will bind to 0.0.0.0:{PORT}")
    
    try:
        # Railway deployment considerations
        debug_mode = os.getenv('RAILWAY_ENVIRONMENT') != 'production'
        
        logger.info(f"🔧 Debug mode: {debug_mode}")
        logger.info(f"🔐 Authentication: {'enabled' if REQUIRE_AUTH else 'disabled'}")
        
        # Start the application
        app.run(
            host='0.0.0.0',  # Railway requires binding to 0.0.0.0
            port=PORT,
            debug=debug_mode,
            use_reloader=False  # Disable reloader in production
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to start Flask application: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)
