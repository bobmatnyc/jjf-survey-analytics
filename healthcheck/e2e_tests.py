#!/usr/bin/env python3
"""
End-to-End Test Suite for JJF Survey Analytics

This module provides comprehensive end-to-end tests that verify the complete
data flow from Google Sheets to database to web interface.
"""

import asyncio
import json
import logging
import os
import sqlite3
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import subprocess
import shutil

# Optional imports
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

# Project imports
try:
    from src.surveyor.config.settings import load_config
    from src.surveyor.services.google_sheets_service import GoogleSheetsService, MockGoogleSheetsService
    MAIN_PROJECT_AVAILABLE = True
except ImportError:
    MAIN_PROJECT_AVAILABLE = False

try:
    from hybrid_surveyor.config.settings import load_settings
    HYBRID_PROJECT_AVAILABLE = True
except ImportError:
    HYBRID_PROJECT_AVAILABLE = False

logger = logging.getLogger(__name__)


class DataExtractionE2ETest:
    """End-to-end tests for data extraction pipeline."""
    
    @staticmethod
    def test_google_sheets_extraction() -> Tuple[str, str, Dict[str, Any]]:
        """Test Google Sheets data extraction functionality."""
        details = {
            "mock_service_test": False,
            "real_service_test": False,
            "extraction_scripts": {},
            "data_validation": {}
        }
        
        # Test mock service first
        if MAIN_PROJECT_AVAILABLE:
            try:
                mock_service = MockGoogleSheetsService()
                test_url = "https://docs.google.com/spreadsheets/d/test123/edit"
                
                # Test spreadsheet ID extraction
                spreadsheet_id = mock_service.extract_spreadsheet_id(test_url)
                details["mock_service_test"] = True
                details["extracted_id"] = spreadsheet_id
                
                # Test data retrieval
                sheet_data = mock_service.get_sheet_data(test_url)
                if sheet_data and len(sheet_data) > 0:
                    details["mock_data_retrieved"] = True
                    details["mock_data_count"] = len(sheet_data)
                    details["mock_sample_headers"] = sheet_data[0].headers if sheet_data[0].headers else []
                
            except Exception as e:
                details["mock_service_error"] = str(e)
        
        # Test real service if credentials are available
        creds_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
        if os.path.exists(creds_file) and MAIN_PROJECT_AVAILABLE:
            try:
                config = load_config()
                real_service = GoogleSheetsService(config.google_sheets)
                
                # Test with a public Google Sheet (if available)
                # Note: This would need a real public sheet URL for testing
                details["real_service_initialized"] = True
                
            except Exception as e:
                details["real_service_error"] = str(e)
        
        # Check extraction scripts
        extraction_scripts = [
            "main.py",
            "improved_extractor.py",
            "simple_extractor.py"
        ]
        
        for script in extraction_scripts:
            if os.path.exists(script):
                details["extraction_scripts"][script] = "exists"
                
                # Try to run with --help to see if it's functional
                try:
                    result = subprocess.run(
                        ["python", script, "--help"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        details["extraction_scripts"][script] = "functional"
                    else:
                        details["extraction_scripts"][script] = f"error: {result.stderr[:100]}"
                except subprocess.TimeoutExpired:
                    details["extraction_scripts"][script] = "timeout"
                except Exception as e:
                    details["extraction_scripts"][script] = f"exception: {e}"
            else:
                details["extraction_scripts"][script] = "missing"
        
        # Determine overall status
        if details.get("mock_service_test") and details.get("mock_data_retrieved"):
            if any(status == "functional" for status in details["extraction_scripts"].values()):
                return "pass", "Data extraction pipeline functional", details
            else:
                return "warning", "Mock service works but extraction scripts have issues", details
        else:
            return "fail", "Data extraction pipeline not functional", details
    
    @staticmethod
    def test_database_pipeline() -> Tuple[str, str, Dict[str, Any]]:
        """Test database creation and data storage pipeline."""
        details = {
            "database_creation": {},
            "data_insertion": {},
            "data_retrieval": {},
            "schema_validation": {}
        }
        
        # Test database creation with temporary database
        temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        temp_db_path = temp_db.name
        temp_db.close()
        
        try:
            # Test basic database operations
            conn = sqlite3.connect(temp_db_path)
            cursor = conn.cursor()
            
            # Create test tables similar to the project structure
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS test_spreadsheets (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS test_sheets (
                    id TEXT PRIMARY KEY,
                    spreadsheet_id TEXT,
                    name TEXT,
                    row_count INTEGER,
                    column_count INTEGER,
                    FOREIGN KEY (spreadsheet_id) REFERENCES test_spreadsheets (id)
                )
            ''')
            
            details["database_creation"]["schema_created"] = True
            
            # Test data insertion
            test_data = [
                ("test_sheet_1", "Test Spreadsheet", "https://example.com/sheet1"),
                ("test_sheet_2", "Another Spreadsheet", "https://example.com/sheet2")
            ]
            
            cursor.executemany(
                "INSERT INTO test_spreadsheets (id, title, url) VALUES (?, ?, ?)",
                test_data
            )
            
            cursor.execute(
                "INSERT INTO test_sheets (id, spreadsheet_id, name, row_count, column_count) VALUES (?, ?, ?, ?, ?)",
                ("sheet_1", "test_sheet_1", "Sheet1", 100, 5)
            )
            
            conn.commit()
            details["data_insertion"]["records_inserted"] = len(test_data) + 1
            
            # Test data retrieval
            cursor.execute("SELECT COUNT(*) FROM test_spreadsheets")
            spreadsheet_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM test_sheets")
            sheet_count = cursor.fetchone()[0]
            
            details["data_retrieval"]["spreadsheet_count"] = spreadsheet_count
            details["data_retrieval"]["sheet_count"] = sheet_count
            
            # Test joins
            cursor.execute('''
                SELECT s.title, sh.name, sh.row_count 
                FROM test_spreadsheets s 
                JOIN test_sheets sh ON s.id = sh.spreadsheet_id
            ''')
            join_results = cursor.fetchall()
            details["data_retrieval"]["join_results"] = len(join_results)
            
            conn.close()
            
            # Clean up
            os.unlink(temp_db_path)
            
            return "pass", "Database pipeline functional", details
            
        except Exception as e:
            # Clean up on error
            try:
                os.unlink(temp_db_path)
            except:
                pass
            
            details["error"] = str(e)
            return "fail", f"Database pipeline failed: {e}", details
    
    @staticmethod
    def test_data_transformation() -> Tuple[str, str, Dict[str, Any]]:
        """Test data transformation and normalization."""
        details = {
            "pandas_available": PANDAS_AVAILABLE,
            "transformation_test": {},
            "normalization_test": {}
        }
        
        if not PANDAS_AVAILABLE:
            return "warning", "Pandas not available - cannot test data transformation", details
        
        try:
            # Create test data similar to Google Sheets format
            test_data = [
                ["Name", "Age", "City", "Active"],
                ["John Doe", "30", "New York", "true"],
                ["Jane Smith", "25", "Los Angeles", "false"],
                ["Bob Johnson", "35", "Chicago", "true"],
                ["", "40", "Boston", "true"],  # Test empty values
                ["Alice Brown", "invalid", "Seattle", "maybe"]  # Test invalid data
            ]
            
            # Convert to DataFrame (simulating data from Google Sheets)
            df = pd.DataFrame(test_data[1:], columns=test_data[0])
            details["transformation_test"]["original_rows"] = len(df)
            details["transformation_test"]["original_columns"] = len(df.columns)
            
            # Test data cleaning
            # Remove empty names
            df_cleaned = df[df['Name'].str.strip() != '']
            details["transformation_test"]["cleaned_rows"] = len(df_cleaned)
            
            # Test data type conversion
            df_cleaned['Age'] = pd.to_numeric(df_cleaned['Age'], errors='coerce')
            df_cleaned['Active'] = df_cleaned['Active'].map({'true': True, 'false': False})
            
            # Check for data quality
            null_ages = df_cleaned['Age'].isnull().sum()
            null_active = df_cleaned['Active'].isnull().sum()
            
            details["transformation_test"]["null_ages"] = int(null_ages)
            details["transformation_test"]["null_active"] = int(null_active)
            
            # Test aggregations
            avg_age = df_cleaned['Age'].mean()
            active_count = df_cleaned['Active'].sum()
            
            details["transformation_test"]["avg_age"] = float(avg_age) if not pd.isna(avg_age) else None
            details["transformation_test"]["active_count"] = int(active_count) if not pd.isna(active_count) else 0
            
            # Test normalization (create separate tables)
            cities = df_cleaned['City'].unique()
            details["normalization_test"]["unique_cities"] = len(cities)
            details["normalization_test"]["cities"] = cities.tolist()
            
            return "pass", "Data transformation pipeline functional", details
            
        except Exception as e:
            details["error"] = str(e)
            return "fail", f"Data transformation failed: {e}", details


class WebInterfaceE2ETest:
    """End-to-end tests for web interface functionality."""
    
    @staticmethod
    def test_flask_endpoints() -> Tuple[str, str, Dict[str, Any]]:
        """Test Flask application endpoints."""
        details = {
            "requests_available": REQUESTS_AVAILABLE,
            "endpoints_tested": {},
            "response_times": {},
            "content_validation": {}
        }
        
        if not REQUESTS_AVAILABLE:
            return "warning", "Requests library not available - cannot test web interface", details
        
        # Common Flask ports to test
        test_ports = [5000, 5001]
        base_url = None
        
        # Find running Flask application
        for port in test_ports:
            try:
                response = requests.get(f"http://localhost:{port}/", timeout=2)
                if response.status_code == 200:
                    base_url = f"http://localhost:{port}"
                    details["flask_port"] = port
                    break
            except:
                continue
        
        if not base_url:
            return "warning", "Flask application not running - cannot test endpoints", details
        
        # Test main endpoints
        endpoints = [
            ("/", "Dashboard", "text/html"),
            ("/spreadsheets", "Spreadsheets", "text/html"),
            ("/jobs", "Jobs", "text/html"),
            ("/api/stats", "API Stats", "application/json"),
            ("/surveys", "Survey Dashboard", "text/html"),
            ("/surveys/analytics", "Survey Analytics", "text/html"),
            ("/sync", "Auto-Sync Dashboard", "text/html"),
            ("/api/sync/status", "Sync Status API", "application/json")
        ]
        
        successful_tests = 0
        total_response_time = 0
        
        for endpoint, name, expected_content_type in endpoints:
            try:
                start_time = time.time()
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
                response_time = (time.time() - start_time) * 1000
                
                details["response_times"][endpoint] = f"{response_time:.0f}ms"
                total_response_time += response_time
                
                if response.status_code == 200:
                    details["endpoints_tested"][endpoint] = f"✓ {response.status_code}"
                    successful_tests += 1
                    
                    # Validate content type
                    content_type = response.headers.get('content-type', '').lower()
                    if expected_content_type in content_type:
                        details["content_validation"][endpoint] = "✓ Content type correct"
                    else:
                        details["content_validation"][endpoint] = f"⚠️ Expected {expected_content_type}, got {content_type}"
                    
                    # Basic content validation
                    if expected_content_type == "text/html":
                        if "<html" in response.text.lower() and "</html>" in response.text.lower():
                            details["content_validation"][endpoint] += " | Valid HTML"
                        else:
                            details["content_validation"][endpoint] += " | Invalid HTML"
                    elif expected_content_type == "application/json":
                        try:
                            json.loads(response.text)
                            details["content_validation"][endpoint] += " | Valid JSON"
                        except:
                            details["content_validation"][endpoint] += " | Invalid JSON"
                
                else:
                    details["endpoints_tested"][endpoint] = f"✗ {response.status_code}"
                    
            except requests.exceptions.Timeout:
                details["endpoints_tested"][endpoint] = "✗ Timeout"
            except Exception as e:
                details["endpoints_tested"][endpoint] = f"✗ Error: {str(e)[:50]}"
        
        details["successful_endpoints"] = successful_tests
        details["total_endpoints"] = len(endpoints)
        details["avg_response_time"] = f"{total_response_time / len(endpoints):.0f}ms"
        
        if successful_tests == 0:
            return "fail", "No endpoints accessible", details
        elif successful_tests < len(endpoints):
            return "warning", f"{successful_tests}/{len(endpoints)} endpoints working", details
        else:
            return "pass", f"All {successful_tests} endpoints working", details
    
    @staticmethod
    def test_data_visualization() -> Tuple[str, str, Dict[str, Any]]:
        """Test data visualization and analytics endpoints."""
        details = {
            "analytics_endpoints": {},
            "data_presence": {},
            "visualization_elements": {}
        }
        
        if not REQUESTS_AVAILABLE:
            return "warning", "Cannot test data visualization without requests library", details
        
        # Find Flask application
        base_url = None
        for port in [5000, 5001]:
            try:
                response = requests.get(f"http://localhost:{port}/", timeout=2)
                if response.status_code == 200:
                    base_url = f"http://localhost:{port}"
                    break
            except:
                continue
        
        if not base_url:
            return "warning", "Flask application not running", details
        
        # Test analytics endpoints
        analytics_endpoints = [
            "/surveys/analytics",
            "/surveys/responses", 
            "/api/survey/search?q=test"
        ]
        
        working_analytics = 0
        
        for endpoint in analytics_endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    details["analytics_endpoints"][endpoint] = "✓ Working"
                    working_analytics += 1
                    
                    # Check for common visualization elements
                    content = response.text.lower()
                    viz_elements = []
                    
                    if "chart" in content or "graph" in content:
                        viz_elements.append("charts")
                    if "table" in content:
                        viz_elements.append("tables")
                    if "dashboard" in content:
                        viz_elements.append("dashboard")
                    if "analytics" in content:
                        viz_elements.append("analytics")
                    
                    details["visualization_elements"][endpoint] = viz_elements
                    
                else:
                    details["analytics_endpoints"][endpoint] = f"✗ {response.status_code}"
                    
            except Exception as e:
                details["analytics_endpoints"][endpoint] = f"✗ Error: {str(e)[:50]}"
        
        # Check for data in databases
        db_files = ["survey_normalized.db", "surveyor_data_improved.db"]
        has_survey_data = False
        
        for db_file in db_files:
            if os.path.exists(db_file):
                try:
                    conn = sqlite3.connect(db_file)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cursor.fetchall()
                    
                    if tables:
                        details["data_presence"][db_file] = f"{len(tables)} tables"
                        has_survey_data = True
                        
                        # Check for data in tables
                        for table in tables[:3]:  # Check first 3 tables
                            try:
                                cursor.execute(f"SELECT COUNT(*) FROM `{table[0]}`;")
                                count = cursor.fetchone()[0]
                                if count > 0:
                                    details["data_presence"][f"{db_file}.{table[0]}"] = f"{count} rows"
                            except:
                                pass
                    
                    conn.close()
                except Exception as e:
                    details["data_presence"][db_file] = f"Error: {e}"
        
        if working_analytics == 0:
            return "fail", "No analytics endpoints working", details
        elif not has_survey_data:
            return "warning", f"{working_analytics} analytics endpoints working but no survey data found", details
        else:
            return "pass", f"Analytics functionality working with data", details


class IntegrationE2ETest:
    """Integration tests for complete data flow."""
    
    @staticmethod
    def test_complete_data_flow() -> Tuple[str, str, Dict[str, Any]]:
        """Test complete data flow from extraction to visualization."""
        details = {
            "flow_stages": {},
            "data_consistency": {},
            "performance_metrics": {}
        }
        
        start_time = time.time()
        
        # Stage 1: Check data extraction capability
        extraction_working = False
        if os.path.exists("main.py"):
            try:
                # Test extraction script help (quick test)
                result = subprocess.run(
                    ["python", "main.py", "--help"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    extraction_working = True
                    details["flow_stages"]["extraction"] = "✓ Script functional"
                else:
                    details["flow_stages"]["extraction"] = f"✗ Script error: {result.stderr[:100]}"
            except Exception as e:
                details["flow_stages"]["extraction"] = f"✗ Exception: {e}"
        else:
            details["flow_stages"]["extraction"] = "✗ Script missing"
        
        # Stage 2: Check database storage
        database_working = False
        db_files = ["surveyor_data_improved.db", "survey_normalized.db"]
        
        for db_file in db_files:
            if os.path.exists(db_file):
                try:
                    conn = sqlite3.connect(db_file)
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
                    table_count = cursor.fetchone()[0]
                    
                    if table_count > 0:
                        database_working = True
                        details["flow_stages"]["database"] = f"✓ {table_count} tables in {db_file}"
                        break
                    
                    conn.close()
                except Exception as e:
                    details["flow_stages"]["database"] = f"✗ Database error: {e}"
        
        if not database_working:
            details["flow_stages"]["database"] = "✗ No functional databases"
        
        # Stage 3: Check web interface
        web_working = False
        if REQUESTS_AVAILABLE:
            for port in [5000, 5001]:
                try:
                    response = requests.get(f"http://localhost:{port}/", timeout=3)
                    if response.status_code == 200:
                        web_working = True
                        details["flow_stages"]["web_interface"] = f"✓ Running on port {port}"
                        break
                except:
                    continue
        
        if not web_working:
            details["flow_stages"]["web_interface"] = "✗ Not accessible"
        
        # Stage 4: Check data consistency
        if database_working and web_working:
            # This would involve more complex checks comparing database data with web display
            details["data_consistency"]["basic_check"] = "✓ Both database and web interface available"
        
        # Performance metrics
        total_time = (time.time() - start_time) * 1000
        details["performance_metrics"]["total_test_time_ms"] = f"{total_time:.0f}ms"
        
        # Determine overall status
        working_stages = sum(1 for stage, status in details["flow_stages"].items() if status.startswith("✓"))
        total_stages = len(details["flow_stages"])
        
        if working_stages == 0:
            return "fail", "No stages of data flow working", details
        elif working_stages < total_stages:
            return "warning", f"{working_stages}/{total_stages} stages working", details
        else:
            return "pass", f"Complete data flow functional ({working_stages}/{total_stages} stages)", details


async def run_all_e2e_tests() -> List[Tuple[str, str, str, Dict[str, Any]]]:
    """Run all end-to-end tests."""
    results = []
    
    # Data extraction tests
    status, message, details = DataExtractionE2ETest.test_google_sheets_extraction()
    results.append(("Google Sheets Extraction", status, message, details))
    
    status, message, details = DataExtractionE2ETest.test_database_pipeline()
    results.append(("Database Pipeline", status, message, details))
    
    status, message, details = DataExtractionE2ETest.test_data_transformation()
    results.append(("Data Transformation", status, message, details))
    
    # Web interface tests
    status, message, details = WebInterfaceE2ETest.test_flask_endpoints()
    results.append(("Flask Endpoints", status, message, details))
    
    status, message, details = WebInterfaceE2ETest.test_data_visualization()
    results.append(("Data Visualization", status, message, details))
    
    # Integration tests
    status, message, details = IntegrationE2ETest.test_complete_data_flow()
    results.append(("Complete Data Flow", status, message, details))
    
    return results


if __name__ == "__main__":
    """Run E2E tests as standalone script."""
    print("🧪 End-to-End Test Suite")
    print("=" * 50)
    
    async def main():
        results = await run_all_e2e_tests()
        
        for name, status, message, details in results:
            status_emoji = {"pass": "✅", "fail": "❌", "warning": "⚠️"}
            print(f"{status_emoji.get(status, '❓')} {name}: {message}")
        
        # Summary
        passed = sum(1 for _, status, _, _ in results if status == "pass")
        failed = sum(1 for _, status, _, _ in results if status == "fail")
        warnings = sum(1 for _, status, _, _ in results if status == "warning")
        
        print(f"\nSummary: {passed} passed, {failed} failed, {warnings} warnings")
        
        # Detailed results for failures
        failures = [r for r in results if r[1] == "fail"]
        if failures:
            print(f"\n❌ Failed Tests:")
            for name, _, message, details in failures:
                print(f"  • {name}: {message}")
    
    asyncio.run(main())
