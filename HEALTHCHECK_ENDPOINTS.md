# Health Check Endpoints - JJF Survey Analytics

The health check system is now fully integrated into the Flask application as endpoints rather than standalone scripts. This provides real-time health monitoring through web APIs.

## 🌐 Available Endpoints

### Core Health Check Endpoints

| Endpoint | Method | Description | Response Format |
|----------|--------|-------------|-----------------|
| `/health` | GET | Complete health check across all categories | JSON |
| `/health/api` | GET | API keys and authentication validation | JSON |
| `/health/dependencies` | GET | External dependencies (DB, Google API, system) | JSON |
| `/health/e2e` | GET | End-to-end functionality tests | JSON |
| `/health/config` | GET | Configuration validation | JSON |

### Monitoring & Utility Endpoints

| Endpoint | Method | Description | Response Format |
|----------|--------|-------------|-----------------|
| `/health/status` | GET | Quick status for load balancers | JSON |
| `/health/metrics` | GET | Prometheus-style metrics | Text/Plain |
| `/health/dashboard` | GET | Web dashboard interface | HTML |
| `/health/test` | GET | Test endpoint to verify system | JSON |

## 🚀 Usage Examples

### Complete Health Check
```bash
curl http://localhost:5001/health
```

**Response:**
```json
{
  "overall_status": "pass",
  "timestamp": "2025-01-23T10:30:00.000Z",
  "duration_ms": 1234,
  "summary": {
    "total": 15,
    "passed": 13,
    "failed": 0,
    "warnings": 2
  },
  "categories": {
    "api_keys": {"total": 4, "passed": 4, "failed": 0, "warnings": 0},
    "dependencies": {"total": 6, "passed": 5, "failed": 0, "warnings": 1},
    "e2e_tests": {"total": 3, "passed": 2, "failed": 0, "warnings": 1},
    "configuration": {"total": 2, "passed": 2, "failed": 0, "warnings": 0}
  },
  "checks": [...]
}
```

### API Keys Check
```bash
curl http://localhost:5001/health/api
```

### Dependencies Check
```bash
curl http://localhost:5001/health/dependencies
```

### Quick Status (for Load Balancers)
```bash
curl http://localhost:5001/health/status
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-23T10:30:00.000Z"
}
```

### Prometheus Metrics
```bash
curl http://localhost:5001/health/metrics
```

**Response:**
```
health_check_status{overall="true"} 1
health_check_total{category="api_keys"} 4
health_check_passed{category="api_keys"} 4
health_check_failed{category="api_keys"} 0
health_check_warnings{category="api_keys"} 0
health_check_duration_ms 1234
```

## 🎯 Health Check Categories

### 1. API Keys & Authentication (`/health/api`)
- ✅ Google service account credentials
- ✅ OAuth client secrets (if configured)
- ✅ Environment variables validation
- ✅ File permissions and security
- ✅ Authentication test with Google APIs

### 2. External Dependencies (`/health/dependencies`)
- ✅ SQLite database connectivity
- ✅ Database content and integrity
- ✅ Google Sheets API availability
- ✅ System resources (CPU, memory, disk)
- ✅ Network connectivity
- ✅ Flask application status

### 3. End-to-End Tests (`/health/e2e`)
- ✅ Google Sheets data extraction
- ✅ Database pipeline functionality
- ✅ Data transformation
- ✅ Flask endpoint accessibility
- ✅ Data visualization components
- ✅ Complete data flow integration

### 4. Configuration (`/health/config`)
- ✅ Environment files validation
- ✅ Project configuration files
- ✅ Database configuration
- ✅ Security settings

## 🔧 Features

### Caching
- **30-second cache** for all health check results
- Prevents excessive resource usage
- Automatic cache invalidation
- Per-category caching

### Async Support
- Non-blocking health checks
- Concurrent execution of tests
- Proper async/await handling in Flask

### Error Handling
- Graceful degradation on failures
- Detailed error messages
- Proper HTTP status codes
- Exception isolation

### Status Codes
- `200 OK` - All checks passed
- `503 Service Unavailable` - One or more checks failed
- `500 Internal Server Error` - Health check system error

## 🖥️ Web Dashboard

Access the interactive health dashboard at:
```
http://localhost:5001/health/dashboard
```

**Features:**
- Real-time health status
- Category-based overview
- System metrics display
- Auto-refresh every 30 seconds
- Manual refresh capability
- Detailed results with expandable sections

## 🔄 Integration Examples

### Docker Health Check
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5001/health/status || exit 1
```

### Kubernetes Probes
```yaml
livenessProbe:
  httpGet:
    path: /health/status
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

### Load Balancer Health Check
```nginx
upstream survey_analytics {
    server 127.0.0.1:5001;
    # Health check every 10 seconds
    health_check uri=/health/status interval=10s;
}
```

### Monitoring Integration
```bash
# Prometheus scraping
curl http://localhost:5001/health/metrics

# Grafana alerting
curl -s http://localhost:5001/health | jq '.overall_status' | grep -q "pass"
```

### CI/CD Pipeline
```yaml
# GitHub Actions example
- name: Health Check
  run: |
    curl -f http://localhost:5001/health/status
    if [ $? -ne 0 ]; then
      echo "Health check failed"
      exit 1
    fi
```

## 🛠️ Development

### Adding Custom Health Checks

1. **Extend the HealthCheckService class** in `app.py`:
```python
def check_custom_service(self):
    """Add your custom health check."""
    try:
        # Your health check logic here
        result = your_custom_check()
        
        return {
            "category": "custom",
            "timestamp": datetime.now().isoformat(),
            "checks": [{
                "name": "Custom Service",
                "status": "pass" if result else "fail",
                "message": "Custom service is healthy",
                "category": "custom",
                "details": {}
            }],
            "summary": {"total": 1, "passed": 1, "failed": 0, "warnings": 0}
        }
    except Exception as e:
        return {
            "category": "custom",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "checks": [],
            "summary": {"total": 0, "passed": 0, "failed": 1, "warnings": 0}
        }
```

2. **Add endpoint**:
```python
@app.route('/health/custom')
def health_check_custom():
    try:
        results = health_service.check_custom_service()
        failed = results.get("summary", {}).get("failed", 0)
        status_code = 200 if failed == 0 else 503
        return jsonify(results), status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

### Testing Health Checks

```bash
# Test all endpoints
curl http://localhost:5001/health/test

# Test specific category
curl http://localhost:5001/health/api

# Test with verbose output
curl -s http://localhost:5001/health | jq '.'
```

## 🚨 Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure `healthcheck/` directory is in Python path
   - Check all required dependencies are installed

2. **Async Errors**
   - Flask async support requires proper decorator usage
   - Check `@async_route` decorator is applied

3. **Cache Issues**
   - Clear cache by restarting Flask application
   - Adjust cache duration in `HealthCheckService.__init__()`

4. **Permission Errors**
   - Check file permissions for credential files
   - Ensure database files are readable/writable

### Debug Mode

Enable Flask debug mode for detailed error messages:
```bash
export FLASK_DEBUG=1
python app.py
```

## 📊 Monitoring Best Practices

1. **Set up automated monitoring** of `/health/status`
2. **Use `/health/metrics`** for Prometheus/Grafana
3. **Monitor trends** in health check duration
4. **Set up alerts** for consecutive failures
5. **Use caching** to prevent resource exhaustion
6. **Test health checks** in staging environment

The health check system is now fully integrated and ready for production use!
