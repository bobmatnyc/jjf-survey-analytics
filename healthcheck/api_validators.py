#!/usr/bin/env python3
"""
API Key and Authentication Validators

This module provides comprehensive validation for all API keys and authentication
mechanisms used in the JJF Survey Analytics project.
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
import base64

# Google API imports
try:
    from google.oauth2 import service_account
    from google.auth.transport.requests import Request
    from google.auth.exceptions import GoogleAuthError
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_APIS_AVAILABLE = True
except ImportError:
    GOOGLE_APIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class GoogleCredentialsValidator:
    """Validator for Google API credentials."""
    
    @staticmethod
    def validate_service_account_file(credentials_path: str) -> Tuple[str, str, Dict[str, Any]]:
        """Validate Google service account credentials file."""
        details = {
            "file_path": credentials_path,
            "file_exists": False,
            "file_readable": False,
            "json_valid": False,
            "credentials_valid": False,
            "auth_test_passed": False
        }
        
        # Check file existence
        if not os.path.exists(credentials_path):
            return "fail", f"Credentials file not found: {credentials_path}", details
        
        details["file_exists"] = True
        
        # Check file readability
        try:
            with open(credentials_path, 'r') as f:
                content = f.read()
            details["file_readable"] = True
        except PermissionError:
            return "fail", f"Cannot read credentials file: {credentials_path}", details
        except Exception as e:
            return "fail", f"Error reading file: {e}", details
        
        # Validate JSON structure
        try:
            creds_data = json.loads(content)
            details["json_valid"] = True
        except json.JSONDecodeError as e:
            return "fail", f"Invalid JSON in credentials file: {e}", details
        
        # Validate service account structure
        required_fields = [
            "type", "project_id", "private_key_id", "private_key",
            "client_email", "client_id", "auth_uri", "token_uri"
        ]
        
        missing_fields = [field for field in required_fields if field not in creds_data]
        if missing_fields:
            return "fail", f"Missing required fields: {missing_fields}", details
        
        # Validate field values
        if creds_data.get("type") != "service_account":
            return "fail", f"Invalid credential type: {creds_data.get('type')}", details
        
        details["credentials_valid"] = True
        details["project_id"] = creds_data.get("project_id")
        details["client_email"] = creds_data.get("client_email")
        
        # Test authentication if Google APIs are available
        if GOOGLE_APIS_AVAILABLE:
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    credentials_path,
                    scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
                )
                
                # Test token refresh
                credentials.refresh(Request())
                details["auth_test_passed"] = True
                details["token_valid"] = True
                
                return "pass", "Service account credentials valid and authenticated", details
                
            except GoogleAuthError as e:
                return "fail", f"Authentication failed: {e}", details
            except Exception as e:
                return "warning", f"Credentials valid but auth test failed: {e}", details
        else:
            return "warning", "Credentials valid but Google APIs not available for testing", details
    
    @staticmethod
    def validate_oauth_client_secrets(secrets_path: str) -> Tuple[str, str, Dict[str, Any]]:
        """Validate OAuth client secrets file."""
        details = {
            "file_path": secrets_path,
            "file_exists": False,
            "json_valid": False,
            "oauth_valid": False
        }
        
        if not os.path.exists(secrets_path):
            return "fail", f"Client secrets file not found: {secrets_path}", details
        
        details["file_exists"] = True
        
        try:
            with open(secrets_path, 'r') as f:
                secrets_data = json.load(f)
            details["json_valid"] = True
        except json.JSONDecodeError as e:
            return "fail", f"Invalid JSON in secrets file: {e}", details
        except Exception as e:
            return "fail", f"Error reading secrets file: {e}", details
        
        # Check OAuth structure
        if "installed" in secrets_data:
            oauth_config = secrets_data["installed"]
            details["oauth_type"] = "installed"
        elif "web" in secrets_data:
            oauth_config = secrets_data["web"]
            details["oauth_type"] = "web"
        else:
            return "fail", "Invalid OAuth client secrets format", details
        
        required_oauth_fields = ["client_id", "client_secret", "auth_uri", "token_uri"]
        missing_fields = [field for field in required_oauth_fields if field not in oauth_config]
        
        if missing_fields:
            return "fail", f"Missing OAuth fields: {missing_fields}", details
        
        details["oauth_valid"] = True
        details["client_id"] = oauth_config.get("client_id", "")[:20] + "..."  # Truncate for security
        
        return "pass", "OAuth client secrets valid", details
    
    @staticmethod
    def test_sheets_api_access(credentials_path: str) -> Tuple[str, str, Dict[str, Any]]:
        """Test actual Google Sheets API access."""
        details = {
            "api_available": GOOGLE_APIS_AVAILABLE,
            "service_created": False,
            "api_call_successful": False
        }
        
        if not GOOGLE_APIS_AVAILABLE:
            return "warning", "Google APIs not available for testing", details
        
        try:
            # Create credentials
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=[
                    'https://www.googleapis.com/auth/spreadsheets.readonly',
                    'https://www.googleapis.com/auth/drive.readonly'
                ]
            )
            
            # Build service
            service = build('sheets', 'v4', credentials=credentials)
            details["service_created"] = True
            
            # Test with a minimal API call (this will fail but tests auth)
            try:
                # Try to get spreadsheet info for a non-existent sheet
                # This tests authentication without requiring a real spreadsheet
                service.spreadsheets().get(spreadsheetId='test_id_that_does_not_exist').execute()
            except HttpError as e:
                if e.resp.status == 404:
                    # 404 means auth worked but spreadsheet not found - this is expected
                    details["api_call_successful"] = True
                    return "pass", "Google Sheets API access confirmed", details
                elif e.resp.status == 403:
                    return "fail", f"API access denied: {e}", details
                else:
                    return "warning", f"API accessible but got error: {e}", details
            
            # If we get here without an error, something unexpected happened
            details["api_call_successful"] = True
            return "pass", "Google Sheets API access confirmed", details
            
        except GoogleAuthError as e:
            return "fail", f"Authentication failed: {e}", details
        except Exception as e:
            return "fail", f"API test failed: {e}", details


class EnvironmentValidator:
    """Validator for environment variables and configuration."""
    
    @staticmethod
    def validate_required_env_vars() -> Tuple[str, str, Dict[str, Any]]:
        """Validate required environment variables."""
        required_vars = {
            "GOOGLE_CREDENTIALS_FILE": "Path to Google service account credentials",
        }
        
        optional_vars = {
            "DATABASE_URL": "Database connection URL",
            "LOG_LEVEL": "Logging level",
            "SHEET_URLS": "Default Google Sheets URLs",
            "GOOGLE_CLIENT_SECRETS_FILE": "OAuth client secrets file",
            "DEBUG": "Debug mode flag"
        }
        
        details = {
            "required": {},
            "optional": {},
            "missing_required": [],
            "env_file_exists": False
        }
        
        # Check for .env file
        env_files = [".env", "hybrid_surveyor/.env"]
        for env_file in env_files:
            if os.path.exists(env_file):
                details["env_file_exists"] = True
                details["env_file_path"] = env_file
                break
        
        # Check required variables
        for var, description in required_vars.items():
            value = os.getenv(var)
            if value:
                details["required"][var] = {
                    "status": "set",
                    "description": description,
                    "value_preview": value[:20] + "..." if len(value) > 20 else value
                }
            else:
                details["required"][var] = {
                    "status": "missing",
                    "description": description
                }
                details["missing_required"].append(var)
        
        # Check optional variables
        for var, description in optional_vars.items():
            value = os.getenv(var)
            details["optional"][var] = {
                "status": "set" if value else "not_set",
                "description": description,
                "value_preview": (value[:20] + "..." if value and len(value) > 20 else value) if value else None
            }
        
        if details["missing_required"]:
            return "fail", f"Missing required environment variables: {details['missing_required']}", details
        
        return "pass", "All required environment variables are set", details
    
    @staticmethod
    def validate_file_paths() -> Tuple[str, str, Dict[str, Any]]:
        """Validate file paths specified in environment variables."""
        details = {
            "credentials_file": {},
            "client_secrets_file": {},
            "database_files": {}
        }
        
        issues = []
        
        # Check credentials file
        creds_file = os.getenv("GOOGLE_CREDENTIALS_FILE")
        if creds_file:
            details["credentials_file"]["path"] = creds_file
            details["credentials_file"]["exists"] = os.path.exists(creds_file)
            details["credentials_file"]["readable"] = False
            
            if os.path.exists(creds_file):
                try:
                    with open(creds_file, 'r') as f:
                        f.read(1)  # Try to read one character
                    details["credentials_file"]["readable"] = True
                except Exception as e:
                    details["credentials_file"]["error"] = str(e)
                    issues.append(f"Credentials file not readable: {e}")
            else:
                issues.append(f"Credentials file not found: {creds_file}")
        
        # Check client secrets file
        secrets_file = os.getenv("GOOGLE_CLIENT_SECRETS_FILE")
        if secrets_file:
            details["client_secrets_file"]["path"] = secrets_file
            details["client_secrets_file"]["exists"] = os.path.exists(secrets_file)
            if not os.path.exists(secrets_file):
                issues.append(f"Client secrets file not found: {secrets_file}")
        
        # Check database files
        db_url = os.getenv("DATABASE_URL", "sqlite:///surveyor.db")
        if db_url.startswith("sqlite"):
            # Extract database file path
            db_path = db_url.replace("sqlite:///", "").replace("sqlite+aiosqlite:///", "")
            if not db_path.startswith(":memory:"):
                details["database_files"]["path"] = db_path
                details["database_files"]["exists"] = os.path.exists(db_path)
                
                # Check if directory is writable
                db_dir = os.path.dirname(db_path) or "."
                details["database_files"]["directory_writable"] = os.access(db_dir, os.W_OK)
                
                if not os.access(db_dir, os.W_OK):
                    issues.append(f"Database directory not writable: {db_dir}")
        
        if issues:
            return "fail", f"File path issues: {'; '.join(issues)}", details
        
        return "pass", "All file paths are valid", details


class ConfigurationValidator:
    """Validator for application configuration."""
    
    @staticmethod
    def validate_project_structure() -> Tuple[str, str, Dict[str, Any]]:
        """Validate project structure and required files."""
        details = {
            "main_project": {},
            "hybrid_project": {},
            "config_files": {},
            "script_files": {}
        }
        
        # Check main project files
        main_files = [
            "app.py",
            "main.py", 
            "requirements.txt",
            "src/surveyor",
            "templates"
        ]
        
        for file_path in main_files:
            exists = os.path.exists(file_path)
            details["main_project"][file_path] = "exists" if exists else "missing"
        
        # Check hybrid project files
        hybrid_files = [
            "hybrid_surveyor/pyproject.toml",
            "hybrid_surveyor/src/hybrid_surveyor",
            "hybrid_surveyor/requirements.txt"
        ]
        
        for file_path in hybrid_files:
            exists = os.path.exists(file_path)
            details["hybrid_project"][file_path] = "exists" if exists else "missing"
        
        # Check configuration files
        config_files = [
            ".env.example",
            "hybrid_surveyor/.env.example",
            "pyproject.toml"
        ]
        
        for file_path in config_files:
            exists = os.path.exists(file_path)
            details["config_files"][file_path] = "exists" if exists else "missing"
        
        # Count existing files
        total_files = len(main_files) + len(hybrid_files) + len(config_files)
        existing_files = sum(1 for category in details.values() 
                           for status in category.values() 
                           if status == "exists")
        
        if existing_files < total_files * 0.7:  # Less than 70% of files exist
            return "fail", f"Missing critical project files ({existing_files}/{total_files})", details
        elif existing_files < total_files:
            return "warning", f"Some project files missing ({existing_files}/{total_files})", details
        else:
            return "pass", f"Project structure complete ({existing_files}/{total_files})", details
    
    @staticmethod
    def validate_dependencies() -> Tuple[str, str, Dict[str, Any]]:
        """Validate Python dependencies."""
        details = {
            "requirements_files": {},
            "critical_imports": {},
            "optional_imports": {}
        }
        
        # Check requirements files
        req_files = ["requirements.txt", "hybrid_surveyor/requirements.txt"]
        for req_file in req_files:
            if os.path.exists(req_file):
                try:
                    with open(req_file, 'r') as f:
                        lines = f.readlines()
                    details["requirements_files"][req_file] = {
                        "exists": True,
                        "package_count": len([l for l in lines if l.strip() and not l.startswith('#')])
                    }
                except Exception as e:
                    details["requirements_files"][req_file] = {
                        "exists": True,
                        "error": str(e)
                    }
            else:
                details["requirements_files"][req_file] = {"exists": False}
        
        # Test critical imports
        critical_modules = [
            "flask",
            "sqlite3",
            "json",
            "os",
            "datetime"
        ]
        
        for module in critical_modules:
            try:
                __import__(module)
                details["critical_imports"][module] = "available"
            except ImportError:
                details["critical_imports"][module] = "missing"
        
        # Test optional imports
        optional_modules = [
            "google.oauth2.service_account",
            "googleapiclient.discovery",
            "pandas",
            "psutil",
            "requests"
        ]
        
        for module in optional_modules:
            try:
                __import__(module)
                details["optional_imports"][module] = "available"
            except ImportError:
                details["optional_imports"][module] = "missing"
        
        # Determine status
        missing_critical = [m for m, status in details["critical_imports"].items() if status == "missing"]
        missing_optional = [m for m, status in details["optional_imports"].items() if status == "missing"]
        
        if missing_critical:
            return "fail", f"Missing critical dependencies: {missing_critical}", details
        elif missing_optional:
            return "warning", f"Missing optional dependencies: {missing_optional}", details
        else:
            return "pass", "All dependencies available", details


def run_all_api_validations() -> List[Tuple[str, str, str, Dict[str, Any]]]:
    """Run all API and configuration validations."""
    results = []
    
    # Google Credentials validation
    creds_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
    if os.path.exists(creds_file):
        status, message, details = GoogleCredentialsValidator.validate_service_account_file(creds_file)
        results.append(("Google Service Account", status, message, details))
        
        if status in ["pass", "warning"]:
            # Test API access
            status, message, details = GoogleCredentialsValidator.test_sheets_api_access(creds_file)
            results.append(("Google Sheets API Access", status, message, details))
    else:
        results.append(("Google Service Account", "fail", f"Credentials file not found: {creds_file}", {}))
    
    # OAuth secrets validation (if configured)
    secrets_file = os.getenv("GOOGLE_CLIENT_SECRETS_FILE")
    if secrets_file:
        status, message, details = GoogleCredentialsValidator.validate_oauth_client_secrets(secrets_file)
        results.append(("OAuth Client Secrets", status, message, details))
    
    # Environment variables validation
    status, message, details = EnvironmentValidator.validate_required_env_vars()
    results.append(("Environment Variables", status, message, details))
    
    # File paths validation
    status, message, details = EnvironmentValidator.validate_file_paths()
    results.append(("File Paths", status, message, details))
    
    # Project structure validation
    status, message, details = ConfigurationValidator.validate_project_structure()
    results.append(("Project Structure", status, message, details))
    
    # Dependencies validation
    status, message, details = ConfigurationValidator.validate_dependencies()
    results.append(("Dependencies", status, message, details))
    
    return results


if __name__ == "__main__":
    """Run API validations as standalone script."""
    print("🔑 API Key and Configuration Validation")
    print("=" * 50)
    
    results = run_all_api_validations()
    
    for name, status, message, details in results:
        status_emoji = {"pass": "✅", "fail": "❌", "warning": "⚠️"}
        print(f"{status_emoji.get(status, '❓')} {name}: {message}")
        
        if status == "fail":
            print(f"   Details: {details}")
    
    # Summary
    passed = sum(1 for _, status, _, _ in results if status == "pass")
    failed = sum(1 for _, status, _, _ in results if status == "fail")
    warnings = sum(1 for _, status, _, _ in results if status == "warning")
    
    print(f"\nSummary: {passed} passed, {failed} failed, {warnings} warnings")
