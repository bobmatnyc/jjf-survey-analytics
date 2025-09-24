#!/usr/bin/env python3
"""
Configuration Validator

This module provides comprehensive validation for all configuration files,
environment variables, and system settings.
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import configparser
import yaml

logger = logging.getLogger(__name__)


class EnvironmentConfigValidator:
    """Validator for environment variables and .env files."""
    
    @staticmethod
    def validate_env_files() -> Tuple[str, str, Dict[str, Any]]:
        """Validate .env files and their structure."""
        details = {
            "env_files": {},
            "example_files": {},
            "missing_vars": [],
            "validation_results": {}
        }
        
        # Check for .env files
        env_files = [
            ".env",
            "hybrid_surveyor/.env"
        ]
        
        example_files = [
            ".env.example",
            "hybrid_surveyor/.env.example"
        ]
        
        # Validate .env files
        for env_file in env_files:
            if os.path.exists(env_file):
                details["env_files"][env_file] = EnvironmentConfigValidator._validate_env_file(env_file)
            else:
                details["env_files"][env_file] = {"exists": False}
        
        # Check example files
        for example_file in example_files:
            if os.path.exists(example_file):
                details["example_files"][example_file] = EnvironmentConfigValidator._validate_env_file(example_file)
            else:
                details["example_files"][example_file] = {"exists": False}
        
        # Compare .env with .env.example
        for env_file, example_file in zip(env_files, example_files):
            if os.path.exists(example_file):
                comparison = EnvironmentConfigValidator._compare_env_files(env_file, example_file)
                details["validation_results"][f"{env_file}_vs_{example_file}"] = comparison
        
        # Determine overall status
        existing_env_files = sum(1 for info in details["env_files"].values() if info.get("exists", False))
        existing_example_files = sum(1 for info in details["example_files"].values() if info.get("exists", False))
        
        if existing_env_files == 0 and existing_example_files > 0:
            return "warning", "Example files exist but no .env files configured", details
        elif existing_env_files > 0:
            # Check for critical issues
            critical_issues = []
            for env_file, info in details["env_files"].items():
                if info.get("exists") and info.get("critical_missing"):
                    critical_issues.extend(info["critical_missing"])
            
            if critical_issues:
                return "fail", f"Critical environment variables missing: {critical_issues}", details
            else:
                return "pass", f"Environment configuration valid ({existing_env_files} files)", details
        else:
            return "warning", "No environment configuration files found", details
    
    @staticmethod
    def _validate_env_file(file_path: str) -> Dict[str, Any]:
        """Validate a single .env file."""
        result = {
            "exists": False,
            "readable": False,
            "variables": {},
            "variable_count": 0,
            "critical_missing": [],
            "warnings": []
        }
        
        if not os.path.exists(file_path):
            return result
        
        result["exists"] = True
        
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            result["readable"] = True
        except Exception as e:
            result["error"] = str(e)
            return result
        
        # Parse environment variables
        variables = {}
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                variables[key] = {
                    "value": value,
                    "line": line_num,
                    "has_value": bool(value)
                }
        
        result["variables"] = variables
        result["variable_count"] = len(variables)
        
        # Check for critical variables
        critical_vars = [
            "GOOGLE_CREDENTIALS_FILE",
            "DATABASE_URL"
        ]
        
        for var in critical_vars:
            if var not in variables:
                result["critical_missing"].append(var)
            elif not variables[var]["has_value"]:
                result["warnings"].append(f"{var} is defined but empty")
        
        return result
    
    @staticmethod
    def _compare_env_files(env_file: str, example_file: str) -> Dict[str, Any]:
        """Compare .env file with .env.example."""
        result = {
            "env_exists": os.path.exists(env_file),
            "example_exists": os.path.exists(example_file),
            "missing_in_env": [],
            "extra_in_env": [],
            "comparison_possible": False
        }
        
        if not (result["env_exists"] and result["example_exists"]):
            return result
        
        result["comparison_possible"] = True
        
        # Get variables from both files
        env_vars = set()
        example_vars = set()
        
        if result["env_exists"]:
            env_info = EnvironmentConfigValidator._validate_env_file(env_file)
            env_vars = set(env_info.get("variables", {}).keys())
        
        if result["example_exists"]:
            example_info = EnvironmentConfigValidator._validate_env_file(example_file)
            example_vars = set(example_info.get("variables", {}).keys())
        
        result["missing_in_env"] = list(example_vars - env_vars)
        result["extra_in_env"] = list(env_vars - example_vars)
        
        return result


class ProjectConfigValidator:
    """Validator for project configuration files."""
    
    @staticmethod
    def validate_pyproject_toml() -> Tuple[str, str, Dict[str, Any]]:
        """Validate pyproject.toml files."""
        details = {
            "files": {},
            "dependencies": {},
            "tool_configs": {}
        }
        
        pyproject_files = [
            "pyproject.toml",
            "hybrid_surveyor/pyproject.toml"
        ]
        
        valid_files = 0
        
        for file_path in pyproject_files:
            file_info = {
                "exists": False,
                "valid_toml": False,
                "has_project": False,
                "has_dependencies": False,
                "tool_configs": []
            }
            
            if os.path.exists(file_path):
                file_info["exists"] = True
                
                try:
                    import tomli
                    with open(file_path, 'rb') as f:
                        data = tomli.load(f)
                    
                    file_info["valid_toml"] = True
                    
                    # Check project section
                    if "project" in data:
                        file_info["has_project"] = True
                        project = data["project"]
                        
                        if "dependencies" in project:
                            file_info["has_dependencies"] = True
                            file_info["dependency_count"] = len(project["dependencies"])
                    
                    # Check tool configurations
                    if "tool" in data:
                        file_info["tool_configs"] = list(data["tool"].keys())
                    
                    valid_files += 1
                    
                except ImportError:
                    file_info["error"] = "tomli library not available"
                except Exception as e:
                    file_info["error"] = str(e)
            
            details["files"][file_path] = file_info
        
        if valid_files == 0:
            return "warning", "No valid pyproject.toml files found", details
        else:
            return "pass", f"Found {valid_files} valid pyproject.toml files", details
    
    @staticmethod
    def validate_requirements_files() -> Tuple[str, str, Dict[str, Any]]:
        """Validate requirements.txt files."""
        details = {
            "files": {},
            "total_packages": 0,
            "common_packages": {}
        }
        
        req_files = [
            "requirements.txt",
            "hybrid_surveyor/requirements.txt"
        ]
        
        valid_files = 0
        all_packages = set()
        
        for file_path in req_files:
            file_info = {
                "exists": False,
                "readable": False,
                "packages": [],
                "package_count": 0,
                "has_versions": 0,
                "comments": 0
            }
            
            if os.path.exists(file_path):
                file_info["exists"] = True
                
                try:
                    with open(file_path, 'r') as f:
                        lines = f.readlines()
                    
                    file_info["readable"] = True
                    
                    packages = []
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            packages.append(line)
                            all_packages.add(line.split('>=')[0].split('==')[0].split('~=')[0])
                            
                            if any(op in line for op in ['>=', '==', '~=', '>', '<']):
                                file_info["has_versions"] += 1
                        elif line.startswith('#'):
                            file_info["comments"] += 1
                    
                    file_info["packages"] = packages
                    file_info["package_count"] = len(packages)
                    valid_files += 1
                    
                except Exception as e:
                    file_info["error"] = str(e)
            
            details["files"][file_path] = file_info
        
        details["total_packages"] = len(all_packages)
        
        # Check for common critical packages
        critical_packages = [
            "flask", "click", "sqlalchemy", "pandas", 
            "google-api-python-client", "requests"
        ]
        
        for package in critical_packages:
            details["common_packages"][package] = package in all_packages
        
        if valid_files == 0:
            return "fail", "No readable requirements.txt files found", details
        else:
            missing_critical = [pkg for pkg, present in details["common_packages"].items() if not present]
            if missing_critical:
                return "warning", f"Some critical packages missing: {missing_critical}", details
            else:
                return "pass", f"Requirements files valid ({valid_files} files, {details['total_packages']} packages)", details


class DatabaseConfigValidator:
    """Validator for database configuration."""
    
    @staticmethod
    def validate_database_config() -> Tuple[str, str, Dict[str, Any]]:
        """Validate database configuration and files."""
        details = {
            "database_urls": {},
            "database_files": {},
            "connection_strings": {},
            "permissions": {}
        }
        
        # Check configured database URLs
        db_urls = [
            os.getenv("DATABASE_URL", "sqlite:///surveyor.db"),
            "sqlite:///surveyor_data_improved.db",
            "sqlite:///survey_normalized.db",
            "sqlite+aiosqlite:///hybrid_surveyor.db"
        ]
        
        for db_url in db_urls:
            url_info = {
                "url": db_url,
                "type": "unknown",
                "file_path": None,
                "file_exists": False,
                "directory_writable": False
            }
            
            # Determine database type
            if db_url.startswith("sqlite"):
                url_info["type"] = "sqlite"
                
                # Extract file path
                if ":///" in db_url:
                    file_path = db_url.split(":///")[1]
                    if not file_path.startswith(":memory:"):
                        url_info["file_path"] = file_path
                        url_info["file_exists"] = os.path.exists(file_path)
                        
                        # Check directory permissions
                        directory = os.path.dirname(file_path) or "."
                        url_info["directory_writable"] = os.access(directory, os.W_OK)
            
            elif db_url.startswith("postgresql"):
                url_info["type"] = "postgresql"
            elif db_url.startswith("mysql"):
                url_info["type"] = "mysql"
            
            details["database_urls"][db_url] = url_info
        
        # Check actual database files
        db_files = [
            "surveyor_data_improved.db",
            "survey_normalized.db",
            "surveyor_data.db",
            "hybrid_surveyor/hybrid_surveyor.db"
        ]
        
        existing_files = 0
        
        for db_file in db_files:
            file_info = {
                "exists": False,
                "readable": False,
                "writable": False,
                "size_bytes": 0
            }
            
            if os.path.exists(db_file):
                file_info["exists"] = True
                existing_files += 1
                
                try:
                    # Check readability
                    with open(db_file, 'rb') as f:
                        f.read(1)
                    file_info["readable"] = True
                except:
                    pass
                
                # Check writability
                file_info["writable"] = os.access(db_file, os.W_OK)
                
                # Get file size
                try:
                    file_info["size_bytes"] = os.path.getsize(db_file)
                except:
                    pass
            
            details["database_files"][db_file] = file_info
        
        # Determine overall status
        if existing_files == 0:
            return "warning", "No database files found", details
        else:
            # Check for permission issues
            permission_issues = []
            for db_file, info in details["database_files"].items():
                if info["exists"] and not info["readable"]:
                    permission_issues.append(f"{db_file} not readable")
                if info["exists"] and not info["writable"]:
                    permission_issues.append(f"{db_file} not writable")
            
            if permission_issues:
                return "warning", f"Database permission issues: {'; '.join(permission_issues)}", details
            else:
                return "pass", f"Database configuration valid ({existing_files} files)", details


class SecurityConfigValidator:
    """Validator for security-related configuration."""
    
    @staticmethod
    def validate_credentials_security() -> Tuple[str, str, Dict[str, Any]]:
        """Validate security of credential files and configuration."""
        details = {
            "credential_files": {},
            "file_permissions": {},
            "security_issues": [],
            "recommendations": []
        }
        
        # Check credential files
        cred_files = [
            "credentials.json",
            "client_secrets.json",
            ".env",
            "hybrid_surveyor/.env"
        ]
        
        for cred_file in cred_files:
            if os.path.exists(cred_file):
                file_info = {
                    "exists": True,
                    "permissions": oct(os.stat(cred_file).st_mode)[-3:],
                    "size_bytes": os.path.getsize(cred_file),
                    "world_readable": False,
                    "group_readable": False
                }
                
                # Check permissions
                mode = os.stat(cred_file).st_mode
                file_info["world_readable"] = bool(mode & 0o004)
                file_info["group_readable"] = bool(mode & 0o040)
                
                # Security checks
                if file_info["world_readable"]:
                    details["security_issues"].append(f"{cred_file} is world-readable")
                
                if file_info["group_readable"]:
                    details["security_issues"].append(f"{cred_file} is group-readable")
                
                details["credential_files"][cred_file] = file_info
        
        # Check for credentials in environment variables
        sensitive_env_vars = [
            "GOOGLE_CREDENTIALS_FILE",
            "DATABASE_URL",
            "SECRET_KEY"
        ]
        
        for var in sensitive_env_vars:
            value = os.getenv(var)
            if value:
                # Check if it looks like a direct credential vs file path
                if var == "DATABASE_URL" and ("password" in value.lower() or "@" in value):
                    details["security_issues"].append(f"{var} may contain embedded credentials")
                elif var == "SECRET_KEY" and len(value) < 32:
                    details["security_issues"].append(f"{var} appears to be weak (too short)")
        
        # Generate recommendations
        if details["security_issues"]:
            details["recommendations"].extend([
                "Set restrictive permissions on credential files (600 or 640)",
                "Use environment variables instead of hardcoded credentials",
                "Consider using a secrets management system",
                "Regularly rotate API keys and credentials"
            ])
        
        # Determine status
        if len(details["security_issues"]) > 2:
            return "fail", f"Multiple security issues found: {len(details['security_issues'])}", details
        elif details["security_issues"]:
            return "warning", f"Security issues found: {'; '.join(details['security_issues'][:2])}", details
        else:
            return "pass", "Credential security configuration acceptable", details


def run_all_config_validations() -> List[Tuple[str, str, str, Dict[str, Any]]]:
    """Run all configuration validations."""
    results = []
    
    # Environment configuration
    status, message, details = EnvironmentConfigValidator.validate_env_files()
    results.append(("Environment Files", status, message, details))
    
    # Project configuration
    status, message, details = ProjectConfigValidator.validate_pyproject_toml()
    results.append(("PyProject TOML", status, message, details))
    
    status, message, details = ProjectConfigValidator.validate_requirements_files()
    results.append(("Requirements Files", status, message, details))
    
    # Database configuration
    status, message, details = DatabaseConfigValidator.validate_database_config()
    results.append(("Database Configuration", status, message, details))
    
    # Security configuration
    status, message, details = SecurityConfigValidator.validate_credentials_security()
    results.append(("Security Configuration", status, message, details))
    
    return results


if __name__ == "__main__":
    """Run configuration validations as standalone script."""
    print("⚙️  Configuration Validation")
    print("=" * 50)
    
    results = run_all_config_validations()
    
    for name, status, message, details in results:
        status_emoji = {"pass": "✅", "fail": "❌", "warning": "⚠️"}
        print(f"{status_emoji.get(status, '❓')} {name}: {message}")
    
    # Summary
    passed = sum(1 for _, status, _, _ in results if status == "pass")
    failed = sum(1 for _, status, _, _ in results if status == "fail")
    warnings = sum(1 for _, status, _, _ in results if status == "warning")
    
    print(f"\nSummary: {passed} passed, {failed} failed, {warnings} warnings")
