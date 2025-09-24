# JJF Survey Analytics - Health Check System

A comprehensive health check system for monitoring API keys, external dependencies, and end-to-end functionality of the JJF Survey Analytics project.

## 🏥 Overview

The health check system provides:

- **API Key Validation** - Verify Google Sheets API credentials and authentication
- **External Dependencies** - Monitor database connectivity, Google Sheets API, and system resources
- **End-to-End Tests** - Validate complete data flow from Google Sheets to web interface
- **Configuration Validation** - Check environment variables, config files, and project structure
- **Continuous Monitoring** - Scheduled health checks with alerting and history tracking
- **Web Dashboard** - Real-time health monitoring interface

## 🚀 Quick Start

### Basic Health Check

Run a comprehensive health check:

```bash
python healthcheck.py
```

### Specific Check Types

```bash
# API keys and authentication only
python healthcheck.py --api-only

# External dependencies only
python healthcheck.py --deps-only

# End-to-end tests only
python healthcheck.py --e2e-only

# JSON output for automation
python healthcheck.py --json

# Verbose output
python healthcheck.py --verbose
```

### Web Interface

Access the health dashboard at: `http://localhost:5001/health/dashboard`

API endpoints:
- `GET /health` - Complete health check
- `GET /health/api` - API keys validation
- `GET /health/dependencies` - External dependencies
- `GET /health/e2e` - End-to-end tests

## 📋 Health Check Categories

### 1. API Keys & Authentication

**Checks:**
- Google service account credentials file
- OAuth client secrets (if configured)
- Environment variables
- File permissions and security
- Authentication test with Google APIs

**Requirements:**
- `GOOGLE_CREDENTIALS_FILE` environment variable
- Valid `credentials.json` file
- Proper file permissions (600 or 640)

### 2. External Dependencies

**Checks:**
- SQLite database connectivity
- Database content and integrity
- Google Sheets API availability
- System resources (CPU, memory, disk)
- Network connectivity to Google services
- Flask application status

**Monitored Services:**
- Google Sheets API (`sheets.googleapis.com`)
- Google APIs (`www.googleapis.com`)
- Local databases (`*.db` files)
- Flask web application (ports 5000, 5001)

### 3. End-to-End Tests

**Tests:**
- Google Sheets data extraction
- Database pipeline functionality
- Data transformation and normalization
- Flask endpoint accessibility
- Data visualization components
- Complete data flow integration

### 4. Configuration Validation

**Validates:**
- Environment files (`.env`, `.env.example`)
- Project configuration (`pyproject.toml`, `requirements.txt`)
- Database configuration and permissions
- Security settings and credential safety

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with required variables:

```bash
# Required
GOOGLE_CREDENTIALS_FILE=credentials.json

# Optional
DATABASE_URL=sqlite:///surveyor.db
LOG_LEVEL=INFO
SHEET_URLS=https://docs.google.com/spreadsheets/d/your-sheet-id/edit

# Monitoring (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_FROM_EMAIL=alerts@yourcompany.com
ALERT_TO_EMAILS=admin@yourcompany.com,ops@yourcompany.com
ALERT_WEBHOOK_URL=https://hooks.slack.com/services/your/webhook/url
```

### Google Sheets API Setup

1. **Create a Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one

2. **Enable APIs**
   - Enable Google Sheets API
   - Enable Google Drive API

3. **Create Service Account**
   - Go to IAM & Admin > Service Accounts
   - Create a new service account
   - Download the JSON key file
   - Save as `credentials.json` in project root

4. **Share Spreadsheets**
   - Share your Google Sheets with the service account email
   - Grant "Viewer" or "Editor" permissions as needed

## 🔄 Continuous Monitoring

### Start Monitoring Service

```bash
# Start continuous monitoring
python healthcheck/monitoring.py --daemon

# With custom configuration
python healthcheck/monitoring.py --config monitoring_config.json --daemon
```

### Monitoring Configuration

Create `monitoring_config.json`:

```json
{
  "api_check_interval": 15,
  "dependency_check_interval": 5,
  "e2e_test_interval": 30,
  "config_check_interval": 60,
  "alerts": {
    "cooldown_minutes": 30,
    "critical_failure_count": 2,
    "warning_threshold": 3,
    "consecutive_failures": 3,
    "email_enabled": true,
    "webhook_enabled": true,
    "log_enabled": true
  },
  "history": {
    "retention_days": 30,
    "max_file_size_mb": 10
  }
}
```

### Alert Channels

**Email Alerts:**
- Configure SMTP settings in environment variables
- Supports Gmail, Outlook, and custom SMTP servers
- Automatic cooldown to prevent spam

**Webhook Alerts:**
- Slack, Discord, Microsoft Teams compatible
- Custom webhook endpoints supported
- JSON payload with detailed information

**Log Alerts:**
- Structured logging to console and files
- Different severity levels (INFO, WARNING, ERROR, CRITICAL)
- Integration with log aggregation systems

## 📊 Web Dashboard

### Features

- **Real-time Status** - Live health check results
- **Category Overview** - API, Dependencies, E2E tests summary
- **Detailed Results** - Expandable check details
- **System Metrics** - CPU, memory, disk usage
- **Auto-refresh** - Updates every 30 seconds
- **Manual Refresh** - On-demand health checks

### Access

1. Start Flask application: `python app.py`
2. Open browser: `http://localhost:5001/health/dashboard`
3. View real-time health status

## 🔧 Troubleshooting

### Common Issues

**1. Credentials File Not Found**
```
❌ Google Service Account: Credentials file not found: credentials.json
```
**Solution:** Download credentials from Google Cloud Console and save as `credentials.json`

**2. Permission Denied**
```
❌ Google Sheets API: Authentication failed: Permission denied
```
**Solution:** Share your Google Sheets with the service account email

**3. Database Not Found**
```
❌ SQLite Databases: No database files found
```
**Solution:** Run data extraction first: `python main.py extract --use-default-urls`

**4. Flask Not Running**
```
⚠️ Flask Application: Flask application not detected
```
**Solution:** Start Flask app: `python app.py`

### Debug Mode

Run with verbose output for detailed debugging:

```bash
python healthcheck.py --verbose
```

### Log Files

Check logs for detailed error information:
- Application logs: Check Flask console output
- Health check logs: `healthcheck_history/` directory
- System logs: `/var/log/` (Linux) or Event Viewer (Windows)

### Manual Testing

Test individual components:

```bash
# Test API validators only
python healthcheck/api_validators.py

# Test dependency checker only
python healthcheck/dependency_checker.py

# Test E2E tests only
python healthcheck/e2e_tests.py

# Test configuration validator only
python healthcheck/config_validator.py
```

## 📈 Monitoring Best Practices

### 1. Regular Monitoring
- Run health checks every 5-15 minutes
- Monitor critical paths more frequently
- Set up alerts for immediate notification

### 2. Alert Configuration
- Use appropriate cooldown periods (15-30 minutes)
- Set escalation thresholds for consecutive failures
- Configure multiple notification channels

### 3. Historical Analysis
- Keep 30+ days of health check history
- Analyze trends and patterns
- Use data for capacity planning

### 4. Security
- Protect credential files (chmod 600)
- Use environment variables for sensitive data
- Regularly rotate API keys and passwords
- Monitor for security-related failures

## 🔗 Integration

### CI/CD Pipeline

Add to your CI/CD pipeline:

```yaml
# GitHub Actions example
- name: Health Check
  run: |
    python healthcheck.py --json > health_results.json
    if [ $? -ne 0 ]; then
      echo "Health check failed"
      exit 1
    fi
```

### Monitoring Systems

Integrate with monitoring platforms:
- **Prometheus**: Export metrics via `/health` endpoint
- **Grafana**: Create dashboards from health check data
- **Datadog**: Send custom metrics via webhook
- **New Relic**: Use API to report health status

### Load Balancers

Use health endpoints for load balancer health checks:
- Primary: `GET /health`
- Lightweight: `GET /health/api`

## 📚 API Reference

### Health Check Endpoints

#### `GET /health`
Complete health check across all categories.

**Response:**
```json
{
  "overall_status": "pass|warning|fail",
  "timestamp": "2025-01-23T10:30:00Z",
  "summary": {
    "total": 15,
    "passed": 12,
    "failed": 1,
    "warnings": 2
  },
  "checks": [...]
}
```

#### `GET /health/api`
API keys and authentication validation.

#### `GET /health/dependencies`
External dependencies health check.

#### `GET /health/e2e`
End-to-end functionality tests.

### Status Codes

- `200 OK` - All checks passed
- `503 Service Unavailable` - One or more checks failed
- `500 Internal Server Error` - Health check system error

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new health checks
4. Update documentation
5. Submit a pull request

## 📄 License

This health check system is part of the JJF Survey Analytics project and follows the same license terms.

## 🎯 Health Check Examples

### Example Output - All Healthy

```bash
$ python healthcheck.py

🏥 JJF Survey Analytics Health Check
==================================================

🔑 API Key & Authentication Checks
✅ Google Credentials: Service account credentials valid and authenticated
✅ Environment Variables: All required environment variables are set

🔗 External Dependency Checks
✅ SQLite Databases: All 3 databases healthy
✅ Google Sheets API: Google Sheets API accessible (response: 245ms)
✅ System Resources: System resources healthy

🧪 End-to-End Tests
✅ Flask Endpoints: All 8 endpoints working
✅ Data Extraction: Data extraction pipeline functional
✅ Complete Data Flow: Complete data flow functional (3/3 stages)

📊 Health Check Summary
==================================================
Overall Status: ✅ PASS
Total Checks: 8
Passed: 8
Failed: 0
Warnings: 0
Duration: 2847ms
```

### Example Output - With Issues

```bash
$ python healthcheck.py

🏥 JJF Survey Analytics Health Check
==================================================

🔑 API Key & Authentication Checks
❌ Google Credentials: Credentials file not found: credentials.json
⚠️ Environment Variables: Missing optional env vars: ['DATABASE_URL']

🔗 External Dependency Checks
⚠️ SQLite Databases: 2/3 databases healthy
✅ System Resources: System resources healthy

❌ Failed Checks:
  • Google Credentials: Credentials file not found: credentials.json

⚠️ Warnings:
  • Environment Variables: Missing optional env vars: ['DATABASE_URL']
  • SQLite Databases: 2/3 databases healthy
```

### JSON Output Example

```bash
$ python healthcheck.py --json
```

```json
{
  "overall_status": "warning",
  "total_checks": 8,
  "passed": 5,
  "failed": 1,
  "warnings": 2,
  "duration_ms": 1234,
  "timestamp": "2025-01-23T10:30:00.000Z",
  "results": [
    {
      "name": "Google Credentials",
      "status": "fail",
      "message": "Credentials file not found: credentials.json",
      "details": {
        "file_path": "credentials.json",
        "file_exists": false
      },
      "duration_ms": 12,
      "timestamp": "2025-01-23T10:30:00.000Z"
    }
  ]
}
```

## 🔍 Advanced Usage

### Custom Health Checks

Add custom health checks by extending the system:

```python
# custom_checks.py
from healthcheck.api_validators import GoogleCredentialsValidator

class CustomHealthCheck:
    @staticmethod
    def check_custom_service():
        # Your custom health check logic
        return "pass", "Custom service is healthy", {"detail": "value"}

# Add to healthcheck.py
from custom_checks import CustomHealthCheck

# In main() function:
result = await runner.run_check("Custom Service", CustomHealthCheck.check_custom_service)
runner.add_result(result)
```

### Automated Deployment Health Checks

Use in deployment scripts:

```bash
#!/bin/bash
# deploy.sh

echo "Deploying application..."
# ... deployment steps ...

echo "Running health checks..."
python healthcheck.py --json > /tmp/health.json

if [ $? -eq 0 ]; then
    echo "✅ Deployment successful - all health checks passed"
    # Send success notification
    curl -X POST "$WEBHOOK_URL" -d '{"text":"✅ Deployment successful"}'
else
    echo "❌ Deployment failed - health checks failed"
    # Send failure notification with details
    curl -X POST "$WEBHOOK_URL" -d @/tmp/health.json
    exit 1
fi
```

### Docker Health Checks

Add to Dockerfile:

```dockerfile
# Dockerfile
COPY healthcheck.py /app/
COPY healthcheck/ /app/healthcheck/

# Health check every 30 seconds
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python healthcheck.py --api-only || exit 1
```

### Kubernetes Readiness/Liveness Probes

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
      - name: survey-analytics
        livenessProbe:
          httpGet:
            path: /health/dependencies
            port: 5001
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 5001
          initialDelaySeconds: 5
          periodSeconds: 10
```
