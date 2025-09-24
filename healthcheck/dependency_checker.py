#!/usr/bin/env python3
"""
External Dependency Checker

This module provides comprehensive checks for all external dependencies
including databases, APIs, system resources, and network connectivity.
"""

import asyncio
import logging
import os
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import json
import subprocess
import socket

# Optional imports with fallbacks
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# Project-specific imports
try:
    from src.surveyor.config.settings import load_config
    MAIN_PROJECT_AVAILABLE = True
except ImportError:
    MAIN_PROJECT_AVAILABLE = False

try:
    from hybrid_surveyor.config.settings import load_settings
    from hybrid_surveyor.utils.health_checker import HealthChecker
    HYBRID_PROJECT_AVAILABLE = True
except ImportError:
    HYBRID_PROJECT_AVAILABLE = False

logger = logging.getLogger(__name__)


class DatabaseChecker:
    """Check database connectivity and health."""
    
    @staticmethod
    def check_sqlite_databases() -> Tuple[str, str, Dict[str, Any]]:
        """Check SQLite database files and connectivity."""
        details = {
            "databases_found": {},
            "total_databases": 0,
            "healthy_databases": 0,
            "database_sizes": {},
            "table_counts": {}
        }
        
        # Known database files in the project
        db_files = [
            "surveyor_data_improved.db",
            "survey_normalized.db", 
            "surveyor_data.db",
            "hybrid_surveyor/hybrid_surveyor.db"
        ]
        
        issues = []
        healthy_count = 0
        
        for db_file in db_files:
            db_info = {
                "exists": False,
                "readable": False,
                "writable": False,
                "size_bytes": 0,
                "table_count": 0,
                "connection_test": False,
                "last_modified": None
            }
            
            if os.path.exists(db_file):
                db_info["exists"] = True
                details["total_databases"] += 1
                
                try:
                    # Get file stats
                    stat = os.stat(db_file)
                    db_info["size_bytes"] = stat.st_size
                    db_info["last_modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
                    details["database_sizes"][db_file] = f"{stat.st_size / 1024:.1f} KB"
                    
                    # Test readability
                    with open(db_file, 'rb') as f:
                        f.read(1)
                    db_info["readable"] = True
                    
                    # Test database connection
                    conn = sqlite3.connect(db_file, timeout=5.0)
                    cursor = conn.cursor()
                    
                    # Get table count
                    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
                    table_count = cursor.fetchone()[0]
                    db_info["table_count"] = table_count
                    details["table_counts"][db_file] = table_count
                    
                    # Test a simple query
                    cursor.execute("SELECT sqlite_version();")
                    version = cursor.fetchone()[0]
                    db_info["sqlite_version"] = version
                    
                    conn.close()
                    db_info["connection_test"] = True
                    healthy_count += 1
                    
                except sqlite3.Error as e:
                    db_info["error"] = f"SQLite error: {e}"
                    issues.append(f"{db_file}: SQLite error - {e}")
                except PermissionError:
                    db_info["error"] = "Permission denied"
                    issues.append(f"{db_file}: Permission denied")
                except Exception as e:
                    db_info["error"] = f"Unexpected error: {e}"
                    issues.append(f"{db_file}: {e}")
            
            details["databases_found"][db_file] = db_info
        
        details["healthy_databases"] = healthy_count
        
        if details["total_databases"] == 0:
            return "fail", "No database files found", details
        elif healthy_count == 0:
            return "fail", f"No healthy databases found. Issues: {'; '.join(issues)}", details
        elif healthy_count < details["total_databases"]:
            return "warning", f"{healthy_count}/{details['total_databases']} databases healthy", details
        else:
            return "pass", f"All {healthy_count} databases healthy", details
    
    @staticmethod
    def check_database_content() -> Tuple[str, str, Dict[str, Any]]:
        """Check database content and data integrity."""
        details = {
            "content_analysis": {},
            "data_freshness": {},
            "integrity_checks": {}
        }
        
        db_files = [
            "surveyor_data_improved.db",
            "survey_normalized.db"
        ]
        
        has_data = False
        issues = []
        
        for db_file in db_files:
            if not os.path.exists(db_file):
                continue
                
            try:
                conn = sqlite3.connect(db_file, timeout=5.0)
                cursor = conn.cursor()
                
                # Get all tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]
                
                content_info = {
                    "tables": tables,
                    "table_row_counts": {},
                    "total_rows": 0
                }
                
                # Count rows in each table
                for table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM `{table}`;")
                        row_count = cursor.fetchone()[0]
                        content_info["table_row_counts"][table] = row_count
                        content_info["total_rows"] += row_count
                        
                        if row_count > 0:
                            has_data = True
                            
                            # Check data freshness (if there's a timestamp column)
                            cursor.execute(f"PRAGMA table_info(`{table}`);")
                            columns = [col[1] for col in cursor.fetchall()]
                            
                            timestamp_cols = [col for col in columns if 
                                            'timestamp' in col.lower() or 
                                            'created' in col.lower() or 
                                            'updated' in col.lower()]
                            
                            if timestamp_cols:
                                try:
                                    cursor.execute(f"SELECT MAX(`{timestamp_cols[0]}`) FROM `{table}`;")
                                    latest = cursor.fetchone()[0]
                                    if latest:
                                        content_info[f"latest_{timestamp_cols[0]}"] = latest
                                except:
                                    pass  # Ignore timestamp parsing errors
                                    
                    except sqlite3.Error as e:
                        content_info["table_row_counts"][table] = f"Error: {e}"
                        issues.append(f"{db_file}.{table}: {e}")
                
                details["content_analysis"][db_file] = content_info
                conn.close()
                
            except Exception as e:
                details["content_analysis"][db_file] = {"error": str(e)}
                issues.append(f"{db_file}: {e}")
        
        if not has_data:
            return "warning", "Databases exist but contain no data", details
        elif issues:
            return "warning", f"Data found but some issues: {'; '.join(issues[:3])}", details
        else:
            return "pass", "Databases contain data and are accessible", details


class GoogleSheetsAPIChecker:
    """Check Google Sheets API connectivity and functionality."""
    
    @staticmethod
    async def check_api_connectivity() -> Tuple[str, str, Dict[str, Any]]:
        """Check Google Sheets API connectivity."""
        details = {
            "credentials_available": False,
            "api_libraries_available": False,
            "authentication_test": False,
            "api_quota_check": False
        }
        
        # Check if Google API libraries are available
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            from googleapiclient.errors import HttpError
            details["api_libraries_available"] = True
        except ImportError as e:
            return "fail", f"Google API libraries not available: {e}", details
        
        # Check credentials
        creds_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
        if not os.path.exists(creds_file):
            return "fail", f"Credentials file not found: {creds_file}", details
        
        details["credentials_available"] = True
        details["credentials_file"] = creds_file
        
        try:
            # Load credentials
            credentials = service_account.Credentials.from_service_account_file(
                creds_file,
                scopes=[
                    'https://www.googleapis.com/auth/spreadsheets.readonly',
                    'https://www.googleapis.com/auth/drive.readonly'
                ]
            )
            
            # Build service
            service = build('sheets', 'v4', credentials=credentials)
            details["authentication_test"] = True
            
            # Test API call with a non-existent spreadsheet to verify auth
            try:
                start_time = time.time()
                service.spreadsheets().get(spreadsheetId='nonexistent_test_id').execute()
            except HttpError as e:
                response_time = (time.time() - start_time) * 1000
                details["api_response_time_ms"] = response_time
                
                if e.resp.status == 404:
                    # 404 means auth worked but spreadsheet not found
                    details["api_quota_check"] = True
                    return "pass", f"Google Sheets API accessible (response: {response_time:.0f}ms)", details
                elif e.resp.status == 403:
                    if "quota" in str(e).lower():
                        return "warning", f"API accessible but quota exceeded: {e}", details
                    else:
                        return "fail", f"API access denied: {e}", details
                else:
                    return "warning", f"API accessible but got unexpected error: {e}", details
            
            # If we get here without an HttpError, something unexpected happened
            return "pass", "Google Sheets API accessible", details
            
        except Exception as e:
            return "fail", f"API connectivity test failed: {e}", details
    
    @staticmethod
    def check_configured_sheets() -> Tuple[str, str, Dict[str, Any]]:
        """Check configured Google Sheets URLs."""
        details = {
            "configured_urls": [],
            "url_validation": {},
            "total_urls": 0,
            "valid_urls": 0
        }
        
        # Get configured URLs from environment
        sheet_urls_env = os.getenv("SHEET_URLS", "")
        if sheet_urls_env:
            urls = [url.strip() for url in sheet_urls_env.split(',') if url.strip()]
            details["configured_urls"] = urls
            details["total_urls"] = len(urls)
        
        # Get URLs from project configurations
        if MAIN_PROJECT_AVAILABLE:
            try:
                config = load_config()
                if hasattr(config, 'sheet_urls') and config.sheet_urls:
                    details["configured_urls"].extend(config.sheet_urls)
                    details["total_urls"] = len(details["configured_urls"])
            except Exception as e:
                details["main_config_error"] = str(e)
        
        if HYBRID_PROJECT_AVAILABLE:
            try:
                settings = load_settings()
                if hasattr(settings, 'sheet_urls') and settings.sheet_urls:
                    details["configured_urls"].extend(settings.sheet_urls)
                    details["total_urls"] = len(set(details["configured_urls"]))  # Remove duplicates
            except Exception as e:
                details["hybrid_config_error"] = str(e)
        
        # Validate URL formats
        valid_count = 0
        for url in details["configured_urls"]:
            if "docs.google.com/spreadsheets" in url and "/d/" in url:
                details["url_validation"][url] = "valid_format"
                valid_count += 1
            else:
                details["url_validation"][url] = "invalid_format"
        
        details["valid_urls"] = valid_count
        
        if details["total_urls"] == 0:
            return "warning", "No Google Sheets URLs configured", details
        elif valid_count == 0:
            return "fail", "No valid Google Sheets URLs found", details
        elif valid_count < details["total_urls"]:
            return "warning", f"{valid_count}/{details['total_urls']} URLs have valid format", details
        else:
            return "pass", f"All {valid_count} configured URLs have valid format", details


class SystemResourceChecker:
    """Check system resources and performance."""
    
    @staticmethod
    def check_system_resources() -> Tuple[str, str, Dict[str, Any]]:
        """Check CPU, memory, and disk usage."""
        details = {
            "psutil_available": PSUTIL_AVAILABLE,
            "metrics": {},
            "warnings": [],
            "thresholds": {
                "cpu_warning": 80,
                "memory_warning": 80,
                "disk_warning": 80
            }
        }
        
        if not PSUTIL_AVAILABLE:
            return "warning", "psutil not available - cannot check system resources", details
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            details["metrics"]["cpu_percent"] = cpu_percent
            details["metrics"]["cpu_count"] = psutil.cpu_count()
            
            if cpu_percent > details["thresholds"]["cpu_warning"]:
                details["warnings"].append(f"High CPU usage: {cpu_percent:.1f}%")
            
            # Memory usage
            memory = psutil.virtual_memory()
            details["metrics"]["memory_percent"] = memory.percent
            details["metrics"]["memory_total_gb"] = round(memory.total / (1024**3), 2)
            details["metrics"]["memory_available_gb"] = round(memory.available / (1024**3), 2)
            details["metrics"]["memory_used_gb"] = round(memory.used / (1024**3), 2)
            
            if memory.percent > details["thresholds"]["memory_warning"]:
                details["warnings"].append(f"High memory usage: {memory.percent:.1f}%")
            
            # Disk usage
            disk = psutil.disk_usage('/')
            details["metrics"]["disk_percent"] = disk.percent
            details["metrics"]["disk_total_gb"] = round(disk.total / (1024**3), 2)
            details["metrics"]["disk_free_gb"] = round(disk.free / (1024**3), 2)
            details["metrics"]["disk_used_gb"] = round(disk.used / (1024**3), 2)
            
            if disk.percent > details["thresholds"]["disk_warning"]:
                details["warnings"].append(f"High disk usage: {disk.percent:.1f}%")
            
            # Process information
            try:
                process = psutil.Process()
                details["metrics"]["process_memory_mb"] = round(process.memory_info().rss / (1024**2), 2)
                details["metrics"]["process_cpu_percent"] = process.cpu_percent()
            except:
                pass  # Ignore process-specific errors
            
            if details["warnings"]:
                return "warning", f"Resource warnings: {'; '.join(details['warnings'])}", details
            else:
                return "pass", "System resources healthy", details
                
        except Exception as e:
            return "fail", f"System resource check failed: {e}", details
    
    @staticmethod
    def check_network_connectivity() -> Tuple[str, str, Dict[str, Any]]:
        """Check network connectivity to external services."""
        details = {
            "connectivity_tests": {},
            "dns_resolution": {},
            "response_times": {}
        }
        
        # Test connectivity to key services
        test_hosts = [
            ("sheets.googleapis.com", 443, "Google Sheets API"),
            ("www.googleapis.com", 443, "Google APIs"),
            ("accounts.google.com", 443, "Google Auth"),
            ("8.8.8.8", 53, "DNS (Google)")
        ]
        
        successful_tests = 0
        
        for host, port, description in test_hosts:
            try:
                start_time = time.time()
                
                # Test socket connection
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                sock.close()
                
                response_time = (time.time() - start_time) * 1000
                details["response_times"][host] = f"{response_time:.0f}ms"
                
                if result == 0:
                    details["connectivity_tests"][host] = f"✓ Connected ({description})"
                    successful_tests += 1
                else:
                    details["connectivity_tests"][host] = f"✗ Failed to connect ({description})"
                    
            except Exception as e:
                details["connectivity_tests"][host] = f"✗ Error: {e}"
        
        # Test DNS resolution
        dns_hosts = ["sheets.googleapis.com", "www.googleapis.com"]
        for host in dns_hosts:
            try:
                import socket
                ip = socket.gethostbyname(host)
                details["dns_resolution"][host] = f"✓ Resolved to {ip}"
            except Exception as e:
                details["dns_resolution"][host] = f"✗ DNS failed: {e}"
        
        if successful_tests == 0:
            return "fail", "No network connectivity to external services", details
        elif successful_tests < len(test_hosts):
            return "warning", f"{successful_tests}/{len(test_hosts)} connectivity tests passed", details
        else:
            return "pass", f"All {successful_tests} connectivity tests passed", details


class ProcessChecker:
    """Check running processes and services."""
    
    @staticmethod
    def check_flask_application() -> Tuple[str, str, Dict[str, Any]]:
        """Check if Flask application is running."""
        details = {
            "port_check": {},
            "process_check": {},
            "endpoint_test": {}
        }
        
        # Check if Flask is running on common ports
        flask_ports = [5000, 5001, 8000, 8080]
        running_ports = []
        
        for port in flask_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                
                if result == 0:
                    running_ports.append(port)
                    details["port_check"][port] = "✓ Port open"
                else:
                    details["port_check"][port] = "○ Port closed"
            except Exception as e:
                details["port_check"][port] = f"✗ Error: {e}"
        
        # Test HTTP endpoints if requests is available
        if REQUESTS_AVAILABLE and running_ports:
            for port in running_ports:
                try:
                    response = requests.get(f"http://localhost:{port}/", timeout=3)
                    details["endpoint_test"][port] = f"✓ HTTP {response.status_code}"
                    if response.status_code == 200:
                        details["flask_running"] = True
                except Exception as e:
                    details["endpoint_test"][port] = f"✗ HTTP error: {e}"
        
        if running_ports:
            return "pass", f"Flask application running on port(s): {running_ports}", details
        else:
            return "warning", "Flask application not detected (not running or different port)", details


async def run_all_dependency_checks() -> List[Tuple[str, str, str, Dict[str, Any]]]:
    """Run all dependency checks."""
    results = []
    
    # Database checks
    status, message, details = DatabaseChecker.check_sqlite_databases()
    results.append(("SQLite Databases", status, message, details))
    
    status, message, details = DatabaseChecker.check_database_content()
    results.append(("Database Content", status, message, details))
    
    # Google Sheets API checks
    status, message, details = await GoogleSheetsAPIChecker.check_api_connectivity()
    results.append(("Google Sheets API", status, message, details))
    
    status, message, details = GoogleSheetsAPIChecker.check_configured_sheets()
    results.append(("Configured Sheets", status, message, details))
    
    # System resource checks
    status, message, details = SystemResourceChecker.check_system_resources()
    results.append(("System Resources", status, message, details))
    
    status, message, details = SystemResourceChecker.check_network_connectivity()
    results.append(("Network Connectivity", status, message, details))
    
    # Process checks
    status, message, details = ProcessChecker.check_flask_application()
    results.append(("Flask Application", status, message, details))
    
    return results


if __name__ == "__main__":
    """Run dependency checks as standalone script."""
    print("🔗 External Dependency Health Check")
    print("=" * 50)
    
    async def main():
        results = await run_all_dependency_checks()
        
        for name, status, message, details in results:
            status_emoji = {"pass": "✅", "fail": "❌", "warning": "⚠️"}
            print(f"{status_emoji.get(status, '❓')} {name}: {message}")
        
        # Summary
        passed = sum(1 for _, status, _, _ in results if status == "pass")
        failed = sum(1 for _, status, _, _ in results if status == "fail")
        warnings = sum(1 for _, status, _, _ in results if status == "warning")
        
        print(f"\nSummary: {passed} passed, {failed} failed, {warnings} warnings")
    
    asyncio.run(main())
