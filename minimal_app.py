#!/usr/bin/env python3
"""
Minimal Flask app for Railway deployment
This is the simplest possible version to get the app working
"""

import os
import sys
from datetime import datetime

print("🚀 Starting minimal Flask app for Railway")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print(f"Files in directory: {os.listdir('.')}")

try:
    from flask import Flask, jsonify, render_template_string
    print("✅ Flask imported successfully")
except ImportError as e:
    print(f"❌ Flask import failed: {e}")
    sys.exit(1)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'simple-key-for-railway'

# Get port from environment - Railway sets this automatically
# Railway typically assigns ports like 8080, 3000, etc.
PORT = int(os.getenv('PORT', 8080))  # Changed default from 5001 to 8080
print(f"🔧 Port configured: {PORT}")
print(f"🔧 Railway PORT env var: {os.getenv('PORT', 'not set')}")
print(f"🔧 All environment variables with PORT:")
for key, value in os.environ.items():
    if 'PORT' in key.upper():
        print(f"   {key}={value}")

# Simple HTML template
SIMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>JJF Survey Analytics</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .status { padding: 20px; margin: 20px 0; border-radius: 4px; }
        .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        h1 { color: #333; }
        .endpoint { background: #f8f9fa; padding: 10px; margin: 10px 0; border-left: 4px solid #007bff; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚂 JJF Survey Analytics</h1>
        
        <div class="status success">
            <strong>✅ Application is running successfully on Railway!</strong>
        </div>
        
        <div class="status info">
            <strong>📊 System Information:</strong><br>
            Timestamp: {{ timestamp }}<br>
            Environment: {{ environment }}<br>
            Port: {{ port }}
        </div>
        
        <h2>🔗 Available Endpoints:</h2>
        <div class="endpoint"><strong>GET /</strong> - This dashboard</div>
        <div class="endpoint"><strong>GET /health</strong> - Health check (JSON)</div>
        <div class="endpoint"><strong>GET /test</strong> - System test (JSON)</div>
        
        <h2>🎯 Next Steps:</h2>
        <ul>
            <li>✅ Basic Flask app is working</li>
            <li>🔧 Add authentication if needed</li>
            <li>📊 Add survey analytics features</li>
            <li>🔗 Connect to Google Sheets API</li>
        </ul>
    </div>
</body>
</html>
"""

@app.route('/')
def dashboard():
    """Main dashboard."""
    return render_template_string(SIMPLE_HTML, 
                                timestamp=datetime.now().isoformat(),
                                environment=os.getenv('RAILWAY_ENVIRONMENT', 'unknown'),
                                port=PORT)

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "message": "JJF Survey Analytics is running on Railway",
        "railway_info": {
            "environment": os.getenv("RAILWAY_ENVIRONMENT", "unknown"),
            "service_name": os.getenv("RAILWAY_SERVICE_NAME", "unknown"),
            "deployment_id": os.getenv("RAILWAY_DEPLOYMENT_ID", "unknown")
        },
        "system_info": {
            "python_version": sys.version,
            "port": PORT,
            "working_directory": os.getcwd()
        }
    })

@app.route('/test')
def test():
    """Test endpoint with detailed system information."""
    return jsonify({
        "message": "System test successful",
        "timestamp": datetime.now().isoformat(),
        "system": {
            "python_version": sys.version,
            "working_directory": os.getcwd(),
            "files_in_directory": os.listdir('.'),
            "port": PORT
        },
        "environment_variables": {
            "PORT": os.getenv("PORT"),
            "RAILWAY_ENVIRONMENT": os.getenv("RAILWAY_ENVIRONMENT"),
            "RAILWAY_SERVICE_NAME": os.getenv("RAILWAY_SERVICE_NAME"),
            "RAILWAY_DEPLOYMENT_ID": os.getenv("RAILWAY_DEPLOYMENT_ID")
        },
        "flask_info": {
            "version": getattr(Flask, '__version__', 'unknown'),
            "debug": app.debug,
            "secret_key_set": bool(app.config.get('SECRET_KEY'))
        }
    })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        "error": "Not Found",
        "message": "The requested endpoint was not found",
        "available_endpoints": ["/", "/health", "/test"],
        "timestamp": datetime.now().isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({
        "error": "Internal Server Error",
        "message": "An internal server error occurred",
        "timestamp": datetime.now().isoformat()
    }), 500

if __name__ == '__main__':
    print("🌐 Starting Flask server")
    print(f"🔧 Host: 0.0.0.0")
    print(f"🔧 Port: {PORT}")
    print(f"🔧 Debug: False")
    
    try:
        app.run(
            host='0.0.0.0',
            port=PORT,
            debug=False,
            use_reloader=False
        )
    except Exception as e:
        print(f"❌ Failed to start Flask app: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
