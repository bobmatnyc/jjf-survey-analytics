#!/usr/bin/env python3
"""
Railway startup script with better port detection
"""

import os
import sys

print("🚂 Railway Startup Script")
print("=" * 30)

# Debug environment
print("🔍 Environment Debug:")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")

# Check all PORT-related environment variables
print("\n🔧 Port Environment Variables:")
port_vars = {k: v for k, v in os.environ.items() if 'PORT' in k.upper()}
if port_vars:
    for key, value in port_vars.items():
        print(f"  {key} = {value}")
else:
    print("  No PORT environment variables found")

# Get the port Railway assigns
railway_port = os.getenv('PORT')
if railway_port:
    print(f"\n✅ Railway assigned PORT: {railway_port}")
    PORT = int(railway_port)
else:
    print("\n⚠️ No PORT environment variable - using default 8080")
    PORT = 8080

print(f"🎯 Final port: {PORT}")

# Start the Flask app
print(f"\n🚀 Starting Flask app on 0.0.0.0:{PORT}")

try:
    from minimal_app import app
    print("✅ Flask app imported successfully")
    
    # Override the port in the app
    app.config['PORT'] = PORT
    
    # Start the app
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
