"""
JJF Survey Analytics Health Check System

A comprehensive health check system for monitoring API keys, external dependencies,
and end-to-end functionality.

This package provides:
- API key and authentication validation
- External dependency monitoring
- End-to-end functionality tests
- Configuration validation
- Continuous monitoring and alerting
- Web dashboard interface

Usage:
    # Basic health check
    python healthcheck.py
    
    # Specific checks
    python healthcheck.py --api-only
    python healthcheck.py --deps-only
    python healthcheck.py --e2e-only
    
    # JSON output
    python healthcheck.py --json
    
    # Start monitoring service
    python healthcheck/monitoring.py --daemon

Web Interface:
    http://localhost:5001/health/dashboard

API Endpoints:
    GET /health - Complete health check
    GET /health/api - API keys validation
    GET /health/dependencies - External dependencies
    GET /health/e2e - End-to-end tests
"""

__version__ = "1.0.0"
__author__ = "JJF Survey Analytics Team"

# Import main classes for easy access
from .api_validators import (
    GoogleCredentialsValidator,
    EnvironmentValidator,
    ConfigurationValidator,
    run_all_api_validations
)

from .dependency_checker import (
    DatabaseChecker,
    GoogleSheetsAPIChecker,
    SystemResourceChecker,
    ProcessChecker,
    run_all_dependency_checks
)

from .e2e_tests import (
    DataExtractionE2ETest,
    WebInterfaceE2ETest,
    IntegrationE2ETest,
    run_all_e2e_tests
)

from .config_validator import (
    EnvironmentConfigValidator,
    ProjectConfigValidator,
    DatabaseConfigValidator,
    SecurityConfigValidator,
    run_all_config_validations
)

from .monitoring import (
    HealthCheckScheduler,
    AlertManager,
    HealthCheckHistory,
    create_monitoring_config
)

# Main health check functions
__all__ = [
    # Validators
    'GoogleCredentialsValidator',
    'EnvironmentValidator', 
    'ConfigurationValidator',
    'run_all_api_validations',
    
    # Dependency checkers
    'DatabaseChecker',
    'GoogleSheetsAPIChecker',
    'SystemResourceChecker',
    'ProcessChecker',
    'run_all_dependency_checks',
    
    # E2E tests
    'DataExtractionE2ETest',
    'WebInterfaceE2ETest',
    'IntegrationE2ETest',
    'run_all_e2e_tests',
    
    # Config validators
    'EnvironmentConfigValidator',
    'ProjectConfigValidator',
    'DatabaseConfigValidator',
    'SecurityConfigValidator',
    'run_all_config_validations',
    
    # Monitoring
    'HealthCheckScheduler',
    'AlertManager',
    'HealthCheckHistory',
    'create_monitoring_config'
]


def get_version():
    """Get the health check system version."""
    return __version__


def get_all_check_categories():
    """Get all available health check categories."""
    return {
        'api_validation': {
            'description': 'API keys and authentication validation',
            'function': run_all_api_validations,
            'checks': [
                'Google Service Account',
                'OAuth Client Secrets',
                'Environment Variables',
                'File Paths',
                'Project Structure',
                'Dependencies'
            ]
        },
        'dependency_checks': {
            'description': 'External dependencies and system resources',
            'function': run_all_dependency_checks,
            'checks': [
                'SQLite Databases',
                'Database Content',
                'Google Sheets API',
                'Configured Sheets',
                'System Resources',
                'Network Connectivity',
                'Flask Application'
            ]
        },
        'e2e_tests': {
            'description': 'End-to-end functionality tests',
            'function': run_all_e2e_tests,
            'checks': [
                'Google Sheets Extraction',
                'Database Pipeline',
                'Data Transformation',
                'Flask Endpoints',
                'Data Visualization',
                'Complete Data Flow'
            ]
        },
        'config_validation': {
            'description': 'Configuration files and settings validation',
            'function': run_all_config_validations,
            'checks': [
                'Environment Files',
                'PyProject TOML',
                'Requirements Files',
                'Database Configuration',
                'Security Configuration'
            ]
        }
    }


async def run_complete_health_check():
    """
    Run a complete health check across all categories.
    
    Returns:
        Dict containing overall status and detailed results
    """
    import time
    from datetime import datetime
    
    start_time = time.time()
    all_results = []
    
    # Run all check categories
    categories = get_all_check_categories()
    
    for category_name, category_info in categories.items():
        try:
            if category_name == 'dependency_checks':
                # Async function
                results = await category_info['function']()
            else:
                # Sync function
                results = category_info['function']()
            
            # Add category to each result
            for name, status, message, details in results:
                all_results.append({
                    'category': category_name,
                    'name': name,
                    'status': status,
                    'message': message,
                    'details': details
                })
                
        except Exception as e:
            all_results.append({
                'category': category_name,
                'name': f'{category_name} (Error)',
                'status': 'fail',
                'message': f'Category check failed: {str(e)}',
                'details': {'error': str(e)}
            })
    
    # Calculate summary
    total_duration = (time.time() - start_time) * 1000
    passed = sum(1 for r in all_results if r['status'] == 'pass')
    failed = sum(1 for r in all_results if r['status'] == 'fail')
    warnings = sum(1 for r in all_results if r['status'] == 'warning')
    
    # Determine overall status
    overall_status = 'pass'
    if failed > 0:
        overall_status = 'fail'
    elif warnings > 0:
        overall_status = 'warning'
    
    return {
        'overall_status': overall_status,
        'timestamp': datetime.utcnow().isoformat(),
        'duration_ms': total_duration,
        'summary': {
            'total': len(all_results),
            'passed': passed,
            'failed': failed,
            'warnings': warnings
        },
        'results': all_results,
        'categories': {
            category: {
                'total': len([r for r in all_results if r['category'] == category]),
                'passed': len([r for r in all_results if r['category'] == category and r['status'] == 'pass']),
                'failed': len([r for r in all_results if r['category'] == category and r['status'] == 'fail']),
                'warnings': len([r for r in all_results if r['category'] == category and r['status'] == 'warning'])
            }
            for category in categories.keys()
        }
    }


def create_health_check_report(results: dict, format: str = 'text') -> str:
    """
    Create a formatted health check report.
    
    Args:
        results: Results from run_complete_health_check()
        format: 'text', 'json', or 'html'
    
    Returns:
        Formatted report string
    """
    if format == 'json':
        import json
        return json.dumps(results, indent=2)
    
    elif format == 'html':
        # Basic HTML report
        html = f"""
        <html>
        <head><title>Health Check Report</title></head>
        <body>
        <h1>Health Check Report</h1>
        <p><strong>Status:</strong> {results['overall_status'].upper()}</p>
        <p><strong>Timestamp:</strong> {results['timestamp']}</p>
        <p><strong>Duration:</strong> {results['duration_ms']:.0f}ms</p>
        
        <h2>Summary</h2>
        <ul>
        <li>Total: {results['summary']['total']}</li>
        <li>Passed: {results['summary']['passed']}</li>
        <li>Failed: {results['summary']['failed']}</li>
        <li>Warnings: {results['summary']['warnings']}</li>
        </ul>
        
        <h2>Results</h2>
        """
        
        for result in results['results']:
            status_color = {'pass': 'green', 'fail': 'red', 'warning': 'orange'}.get(result['status'], 'gray')
            html += f"""
            <div style="margin: 10px 0; padding: 10px; border-left: 4px solid {status_color};">
            <strong>{result['name']}</strong> ({result['category']})<br>
            <span style="color: {status_color};">{result['status'].upper()}</span>: {result['message']}
            </div>
            """
        
        html += "</body></html>"
        return html
    
    else:  # text format
        status_emoji = {'pass': '✅', 'fail': '❌', 'warning': '⚠️'}
        
        report = f"""
🏥 JJF Survey Analytics Health Check Report
{'=' * 50}

Overall Status: {status_emoji.get(results['overall_status'], '❓')} {results['overall_status'].upper()}
Timestamp: {results['timestamp']}
Duration: {results['duration_ms']:.0f}ms

📊 Summary:
  Total Checks: {results['summary']['total']}
  Passed: {results['summary']['passed']}
  Failed: {results['summary']['failed']}
  Warnings: {results['summary']['warnings']}

📋 Detailed Results:
"""
        
        # Group by category
        categories = {}
        for result in results['results']:
            category = result['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(result)
        
        for category, category_results in categories.items():
            report += f"\n{category.replace('_', ' ').title()}:\n"
            for result in category_results:
                emoji = status_emoji.get(result['status'], '❓')
                report += f"  {emoji} {result['name']}: {result['message']}\n"
        
        return report
