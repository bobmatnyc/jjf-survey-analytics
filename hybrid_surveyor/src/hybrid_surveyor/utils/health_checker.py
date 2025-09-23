"""
Health checking utilities for monitoring system health.

This module provides health checking capabilities for various system
components including database, Google Sheets API, and overall system health.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import aiohttp
import gspread

from ..core.interfaces import IHealthChecker
from ..config.settings import Settings
from ..core.exceptions import HealthCheckError

logger = logging.getLogger(__name__)


class HealthChecker(IHealthChecker):
    """
    Comprehensive health checker for system components.
    
    Monitors:
    - Database connectivity
    - Google Sheets API availability
    - System resources
    - External dependencies
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.last_check: Optional[datetime] = None
        self.cached_results: Dict[str, Any] = {}
        self.cache_duration = timedelta(seconds=30)  # Cache results for 30 seconds
    
    async def check_health(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        # Check if we have cached results
        if (
            self.last_check
            and datetime.utcnow() - self.last_check < self.cache_duration
            and self.cached_results
        ):
            return self.cached_results
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {},
            "summary": {
                "total_checks": 0,
                "passed_checks": 0,
                "failed_checks": 0,
                "warning_checks": 0
            }
        }
        
        # Run all health checks
        checks = [
            ("database", self._check_database),
            ("google_sheets_api", self._check_google_sheets_api),
            ("system_resources", self._check_system_resources),
            ("configuration", self._check_configuration),
        ]
        
        for check_name, check_func in checks:
            try:
                result = await check_func()
                health_status["checks"][check_name] = result
                
                # Update summary
                health_status["summary"]["total_checks"] += 1
                if result["status"] == "healthy":
                    health_status["summary"]["passed_checks"] += 1
                elif result["status"] == "warning":
                    health_status["summary"]["warning_checks"] += 1
                else:
                    health_status["summary"]["failed_checks"] += 1
                    
            except Exception as e:
                logger.error(f"Health check '{check_name}' failed: {e}")
                health_status["checks"][check_name] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
                health_status["summary"]["total_checks"] += 1
                health_status["summary"]["failed_checks"] += 1
        
        # Determine overall status
        if health_status["summary"]["failed_checks"] > 0:
            health_status["status"] = "unhealthy"
        elif health_status["summary"]["warning_checks"] > 0:
            health_status["status"] = "warning"
        
        # Cache results
        self.cached_results = health_status
        self.last_check = datetime.utcnow()
        
        return health_status
    
    async def check_dependencies(self) -> Dict[str, bool]:
        """Check health of external dependencies."""
        dependencies = {}
        
        # Check Google Sheets API
        try:
            await self._check_google_sheets_api()
            dependencies["google_sheets_api"] = True
        except Exception:
            dependencies["google_sheets_api"] = False
        
        # Check database
        try:
            await self._check_database()
            dependencies["database"] = True
        except Exception:
            dependencies["database"] = False
        
        return dependencies
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity and health."""
        try:
            # Import here to avoid circular imports
            from ..services.database_service import DatabaseService
            
            # Create a temporary database service for health check
            db_service = DatabaseService(self.settings.database)
            
            # Test basic connectivity
            start_time = datetime.utcnow()
            await db_service.health_check()
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "status": "healthy",
                "response_time_seconds": response_time,
                "database_url": self.settings.database.url.split("://")[0] + "://***",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _check_google_sheets_api(self) -> Dict[str, Any]:
        """Check Google Sheets API connectivity."""
        try:
            # Test authentication and basic API call
            if self.settings.google_sheets.credentials_file:
                from google.oauth2.service_account import Credentials
                creds = Credentials.from_service_account_file(
                    str(self.settings.google_sheets.credentials_file),
                    scopes=self.settings.google_sheets.scopes
                )
                client = gspread.authorize(creds)
            else:
                client = gspread.service_account()
            
            # Test with a simple API call (list spreadsheets is lightweight)
            start_time = datetime.utcnow()
            # Note: This might fail if no spreadsheets are accessible, but it tests auth
            try:
                client.list_permissions("test")  # This will fail but tests auth
            except gspread.exceptions.APIError as e:
                if "not found" in str(e).lower():
                    # This is expected - we're just testing auth
                    pass
                else:
                    raise
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "status": "healthy",
                "response_time_seconds": response_time,
                "authentication_method": "service_account" if self.settings.google_sheets.credentials_file else "default",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage."""
        try:
            import psutil
            
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Determine status based on thresholds
            status = "healthy"
            warnings = []
            
            if cpu_percent > 80:
                status = "warning"
                warnings.append(f"High CPU usage: {cpu_percent}%")
            
            if memory.percent > 80:
                status = "warning"
                warnings.append(f"High memory usage: {memory.percent}%")
            
            if disk.percent > 80:
                status = "warning"
                warnings.append(f"High disk usage: {disk.percent}%")
            
            return {
                "status": status,
                "warnings": warnings,
                "metrics": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_percent": disk.percent,
                    "disk_free_gb": disk.free / (1024**3)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except ImportError:
            return {
                "status": "warning",
                "message": "psutil not available - system metrics unavailable",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _check_configuration(self) -> Dict[str, Any]:
        """Check configuration validity."""
        try:
            issues = []
            warnings = []
            
            # Check Google Sheets configuration
            if not self.settings.google_sheets.credentials_file and not self.settings.google_sheets.client_secrets_file:
                warnings.append("No Google Sheets credentials configured")
            
            # Check database configuration
            if "sqlite" in self.settings.database.url and ":memory:" not in self.settings.database.url:
                # Check if database file is writable
                import os
                from pathlib import Path
                
                db_path = self.settings.database.url.replace("sqlite:///", "").replace("sqlite+aiosqlite:///", "")
                db_dir = Path(db_path).parent
                
                if not db_dir.exists():
                    issues.append(f"Database directory does not exist: {db_dir}")
                elif not os.access(db_dir, os.W_OK):
                    issues.append(f"Database directory is not writable: {db_dir}")
            
            # Check sheet URLs
            if not self.settings.sheet_urls:
                warnings.append("No default sheet URLs configured")
            
            status = "healthy"
            if issues:
                status = "unhealthy"
            elif warnings:
                status = "warning"
            
            return {
                "status": status,
                "issues": issues,
                "warnings": warnings,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
