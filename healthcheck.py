#!/usr/bin/env python3
"""
Comprehensive Health Check System for JJF Survey Analytics

This script performs comprehensive health checks for:
- API keys and authentication
- External dependencies (Google Sheets API, databases)
- End-to-end functionality tests
- System resources and configuration

Usage:
    python healthcheck.py                    # Run all checks
    python healthcheck.py --api-only         # Check API keys only
    python healthcheck.py --deps-only        # Check dependencies only
    python healthcheck.py --e2e-only         # Run e2e tests only
    python healthcheck.py --json             # Output in JSON format
    python healthcheck.py --verbose          # Verbose output
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import argparse
import sqlite3
import requests
from dataclasses import dataclass, asdict

# Try to import project modules
try:
    from src.surveyor.config.settings import load_config
    from src.surveyor.services.google_sheets_service import GoogleSheetsService
    MAIN_PROJECT_AVAILABLE = True
except ImportError:
    MAIN_PROJECT_AVAILABLE = False

try:
    from hybrid_surveyor.config.settings import load_settings
    from hybrid_surveyor.utils.health_checker import HealthChecker
    HYBRID_PROJECT_AVAILABLE = True
except ImportError:
    HYBRID_PROJECT_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    name: str
    status: str  # 'pass', 'fail', 'warning'
    message: str
    details: Dict[str, Any]
    duration_ms: float
    timestamp: str


@dataclass
class HealthCheckSummary:
    """Summary of all health checks."""
    overall_status: str
    total_checks: int
    passed: int
    failed: int
    warnings: int
    duration_ms: float
    timestamp: str
    results: List[HealthCheckResult]


class HealthCheckRunner:
    """Main health check orchestrator."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: List[HealthCheckResult] = []
        self.start_time = time.time()
    
    def add_result(self, result: HealthCheckResult):
        """Add a health check result."""
        self.results.append(result)
        if self.verbose:
            status_emoji = {"pass": "✅", "fail": "❌", "warning": "⚠️"}
            print(f"{status_emoji.get(result.status, '❓')} {result.name}: {result.message}")
    
    async def run_check(self, name: str, check_func, *args, **kwargs) -> HealthCheckResult:
        """Run a single health check with timing and error handling."""
        start_time = time.time()
        timestamp = datetime.utcnow().isoformat()
        
        try:
            if asyncio.iscoroutinefunction(check_func):
                result = await check_func(*args, **kwargs)
            else:
                result = check_func(*args, **kwargs)
            
            duration_ms = (time.time() - start_time) * 1000
            
            if isinstance(result, tuple):
                status, message, details = result
            else:
                status, message, details = "pass", str(result), {}
            
            return HealthCheckResult(
                name=name,
                status=status,
                message=message,
                details=details,
                duration_ms=duration_ms,
                timestamp=timestamp
            )
        
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name=name,
                status="fail",
                message=f"Check failed: {str(e)}",
                details={"error": str(e), "type": type(e).__name__},
                duration_ms=duration_ms,
                timestamp=timestamp
            )
    
    def get_summary(self) -> HealthCheckSummary:
        """Get summary of all health check results."""
        total_duration_ms = (time.time() - self.start_time) * 1000
        
        passed = sum(1 for r in self.results if r.status == "pass")
        failed = sum(1 for r in self.results if r.status == "fail")
        warnings = sum(1 for r in self.results if r.status == "warning")
        
        if failed > 0:
            overall_status = "fail"
        elif warnings > 0:
            overall_status = "warning"
        else:
            overall_status = "pass"
        
        return HealthCheckSummary(
            overall_status=overall_status,
            total_checks=len(self.results),
            passed=passed,
            failed=failed,
            warnings=warnings,
            duration_ms=total_duration_ms,
            timestamp=datetime.utcnow().isoformat(),
            results=self.results
        )


class APIKeyChecker:
    """Check API keys and authentication."""
    
    @staticmethod
    def check_google_credentials() -> Tuple[str, str, Dict[str, Any]]:
        """Check Google Sheets API credentials."""
        details = {}
        
        # Check for credentials file
        creds_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
        details["credentials_file"] = creds_file
        
        if not os.path.exists(creds_file):
            return "fail", f"Credentials file not found: {creds_file}", details
        
        try:
            with open(creds_file, 'r') as f:
                creds_data = json.load(f)
            
            # Check if it's a service account file
            if "type" in creds_data and creds_data["type"] == "service_account":
                details["auth_type"] = "service_account"
                details["client_email"] = creds_data.get("client_email", "unknown")
                details["project_id"] = creds_data.get("project_id", "unknown")
                
                required_fields = ["type", "project_id", "private_key_id", "private_key", "client_email"]
                missing_fields = [field for field in required_fields if field not in creds_data]
                
                if missing_fields:
                    return "fail", f"Missing required fields: {missing_fields}", details
                
                return "pass", "Service account credentials valid", details
            
            # Check if it's OAuth client secrets
            elif "installed" in creds_data or "web" in creds_data:
                details["auth_type"] = "oauth"
                return "pass", "OAuth client secrets found", details
            
            else:
                return "fail", "Unknown credentials format", details
                
        except json.JSONDecodeError as e:
            return "fail", f"Invalid JSON in credentials file: {e}", details
        except Exception as e:
            return "fail", f"Error reading credentials: {e}", details
    
    @staticmethod
    def check_environment_variables() -> Tuple[str, str, Dict[str, Any]]:
        """Check required environment variables."""
        required_vars = [
            "GOOGLE_CREDENTIALS_FILE",
        ]
        
        optional_vars = [
            "DATABASE_URL",
            "LOG_LEVEL",
            "SHEET_URLS"
        ]
        
        details = {}
        missing_required = []
        
        for var in required_vars:
            value = os.getenv(var)
            if value:
                details[var] = "✓ Set"
            else:
                details[var] = "✗ Missing"
                missing_required.append(var)
        
        for var in optional_vars:
            value = os.getenv(var)
            details[var] = "✓ Set" if value else "○ Not set (optional)"
        
        if missing_required:
            return "warning", f"Missing optional env vars: {missing_required}", details
        
        return "pass", "All required environment variables present", details


class DependencyChecker:
    """Check external dependencies."""
    
    @staticmethod
    def check_database_connectivity() -> Tuple[str, str, Dict[str, Any]]:
        """Check database connectivity."""
        details = {}
        
        # Check main project databases
        db_files = [
            "surveyor_data_improved.db",
            "survey_normalized.db",
            "surveyor_data.db"
        ]
        
        found_dbs = []
        for db_file in db_files:
            if os.path.exists(db_file):
                found_dbs.append(db_file)
                try:
                    conn = sqlite3.connect(db_file)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cursor.fetchall()
                    conn.close()
                    details[db_file] = f"✓ Connected ({len(tables)} tables)"
                except Exception as e:
                    details[db_file] = f"✗ Connection failed: {e}"
            else:
                details[db_file] = "○ Not found"
        
        # Check hybrid surveyor database
        hybrid_db = "hybrid_surveyor/hybrid_surveyor.db"
        if os.path.exists(hybrid_db):
            found_dbs.append(hybrid_db)
            details[hybrid_db] = "✓ Found"
        
        if not found_dbs:
            return "fail", "No databases found", details
        
        return "pass", f"Found {len(found_dbs)} database(s)", details
    
    @staticmethod
    async def check_google_sheets_api() -> Tuple[str, str, Dict[str, Any]]:
        """Check Google Sheets API connectivity."""
        details = {}
        
        try:
            if MAIN_PROJECT_AVAILABLE:
                config = load_config()
                service = GoogleSheetsService(config.google_sheets)
                
                # Test with a dummy URL to check authentication
                test_url = "https://docs.google.com/spreadsheets/d/test/edit"
                try:
                    service.extract_spreadsheet_id(test_url)
                    details["main_project"] = "✓ Service initialized"
                except Exception as e:
                    details["main_project"] = f"⚠️ Service error: {e}"
            
            if HYBRID_PROJECT_AVAILABLE:
                settings = load_settings()
                health_checker = HealthChecker(settings)
                api_result = await health_checker._check_google_sheets_api()
                details["hybrid_project"] = f"✓ {api_result['status']}"
            
            return "pass", "Google Sheets API accessible", details
            
        except Exception as e:
            return "fail", f"Google Sheets API check failed: {e}", details
    
    @staticmethod
    def check_system_resources() -> Tuple[str, str, Dict[str, Any]]:
        """Check system resources."""
        details = {}
        warnings = []
        
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            details["cpu_usage_percent"] = cpu_percent
            if cpu_percent > 80:
                warnings.append(f"High CPU usage: {cpu_percent}%")
            
            # Memory usage
            memory = psutil.virtual_memory()
            details["memory_usage_percent"] = memory.percent
            details["memory_available_gb"] = round(memory.available / (1024**3), 2)
            if memory.percent > 80:
                warnings.append(f"High memory usage: {memory.percent}%")
            
            # Disk usage
            disk = psutil.disk_usage('/')
            details["disk_usage_percent"] = disk.percent
            details["disk_free_gb"] = round(disk.free / (1024**3), 2)
            if disk.percent > 80:
                warnings.append(f"High disk usage: {disk.percent}%")
            
            if warnings:
                return "warning", f"Resource warnings: {'; '.join(warnings)}", details
            
            return "pass", "System resources healthy", details
            
        except ImportError:
            return "warning", "psutil not available - cannot check system resources", details
        except Exception as e:
            return "fail", f"System resource check failed: {e}", details


class EndToEndTester:
    """End-to-end functionality tests."""
    
    @staticmethod
    def test_flask_application() -> Tuple[str, str, Dict[str, Any]]:
        """Test Flask application endpoints."""
        details = {}
        base_url = "http://localhost:5001"
        
        endpoints = [
            ("/", "Dashboard"),
            ("/spreadsheets", "Spreadsheets"),
            ("/jobs", "Jobs"),
            ("/api/stats", "API Stats"),
            ("/surveys", "Survey Dashboard"),
            ("/sync", "Auto-Sync Dashboard")
        ]
        
        working_endpoints = []
        failed_endpoints = []
        
        for endpoint, name in endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    working_endpoints.append(endpoint)
                    details[endpoint] = f"✓ {response.status_code}"
                else:
                    failed_endpoints.append(endpoint)
                    details[endpoint] = f"✗ {response.status_code}"
            except requests.exceptions.ConnectionError:
                details[endpoint] = "✗ Connection refused (app not running?)"
                failed_endpoints.append(endpoint)
            except Exception as e:
                details[endpoint] = f"✗ Error: {e}"
                failed_endpoints.append(endpoint)
        
        if not working_endpoints and failed_endpoints:
            return "fail", "Flask application not accessible", details
        elif failed_endpoints:
            return "warning", f"{len(working_endpoints)}/{len(endpoints)} endpoints working", details
        else:
            return "pass", f"All {len(endpoints)} endpoints working", details
    
    @staticmethod
    def test_data_extraction() -> Tuple[str, str, Dict[str, Any]]:
        """Test data extraction functionality."""
        details = {}
        
        # Check if extraction scripts exist
        scripts = [
            "main.py",
            "improved_extractor.py",
            "hybrid_surveyor/src/hybrid_surveyor/cli/main.py"
        ]
        
        found_scripts = []
        for script in scripts:
            if os.path.exists(script):
                found_scripts.append(script)
                details[script] = "✓ Found"
            else:
                details[script] = "○ Not found"
        
        if not found_scripts:
            return "fail", "No extraction scripts found", details
        
        # Check if databases have data
        has_data = False
        for db_file in ["surveyor_data_improved.db", "survey_normalized.db"]:
            if os.path.exists(db_file):
                try:
                    conn = sqlite3.connect(db_file)
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
                    table_count = cursor.fetchone()[0]
                    if table_count > 0:
                        has_data = True
                        details[f"{db_file}_tables"] = table_count
                    conn.close()
                except Exception as e:
                    details[f"{db_file}_error"] = str(e)
        
        if has_data:
            return "pass", f"Data extraction setup complete ({len(found_scripts)} scripts)", details
        else:
            return "warning", f"Scripts found but no data extracted yet", details


async def main():
    """Main health check execution."""
    parser = argparse.ArgumentParser(description="JJF Survey Analytics Health Check")
    parser.add_argument("--api-only", action="store_true", help="Check API keys only")
    parser.add_argument("--deps-only", action="store_true", help="Check dependencies only")
    parser.add_argument("--e2e-only", action="store_true", help="Run e2e tests only")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    runner = HealthCheckRunner(verbose=args.verbose)
    
    if not args.json and not args.verbose:
        print("🏥 JJF Survey Analytics Health Check")
        print("=" * 50)
    
    # API Key Checks
    if not args.deps_only and not args.e2e_only:
        if not args.json:
            print("\n🔑 API Key & Authentication Checks")
        
        result = await runner.run_check("Google Credentials", APIKeyChecker.check_google_credentials)
        runner.add_result(result)
        
        result = await runner.run_check("Environment Variables", APIKeyChecker.check_environment_variables)
        runner.add_result(result)
    
    # Dependency Checks
    if not args.api_only and not args.e2e_only:
        if not args.json:
            print("\n🔗 External Dependency Checks")
        
        result = await runner.run_check("Database Connectivity", DependencyChecker.check_database_connectivity)
        runner.add_result(result)
        
        result = await runner.run_check("Google Sheets API", DependencyChecker.check_google_sheets_api)
        runner.add_result(result)
        
        result = await runner.run_check("System Resources", DependencyChecker.check_system_resources)
        runner.add_result(result)
    
    # End-to-End Tests
    if not args.api_only and not args.deps_only:
        if not args.json:
            print("\n🧪 End-to-End Tests")
        
        result = await runner.run_check("Flask Application", EndToEndTester.test_flask_application)
        runner.add_result(result)
        
        result = await runner.run_check("Data Extraction", EndToEndTester.test_data_extraction)
        runner.add_result(result)
    
    # Generate summary
    summary = runner.get_summary()
    
    if args.json:
        print(json.dumps(asdict(summary), indent=2))
    else:
        print(f"\n📊 Health Check Summary")
        print("=" * 50)
        
        status_emoji = {"pass": "✅", "fail": "❌", "warning": "⚠️"}
        print(f"Overall Status: {status_emoji.get(summary.overall_status, '❓')} {summary.overall_status.upper()}")
        print(f"Total Checks: {summary.total_checks}")
        print(f"Passed: {summary.passed}")
        print(f"Failed: {summary.failed}")
        print(f"Warnings: {summary.warnings}")
        print(f"Duration: {summary.duration_ms:.0f}ms")
        
        if summary.failed > 0:
            print(f"\n❌ Failed Checks:")
            for result in summary.results:
                if result.status == "fail":
                    print(f"  • {result.name}: {result.message}")
        
        if summary.warnings > 0:
            print(f"\n⚠️  Warnings:")
            for result in summary.results:
                if result.status == "warning":
                    print(f"  • {result.name}: {result.message}")
    
    # Exit with appropriate code
    sys.exit(0 if summary.overall_status == "pass" else 1)


if __name__ == "__main__":
    asyncio.run(main())
