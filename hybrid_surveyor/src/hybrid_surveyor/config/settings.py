"""
Application settings and configuration management.

This module combines the best practices from both approaches:
- Pydantic for type safety and validation
- Environment variable support
- Comprehensive configuration options
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
from pydantic import BaseSettings, Field, HttpUrl, validator
import os

from ..models.domain import RetryConfig


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    url: str = Field(
        default="sqlite+aiosqlite:///hybrid_surveyor.db",
        env="DATABASE_URL",
        description="Database connection URL"
    )
    
    echo: bool = Field(
        default=False,
        env="DATABASE_ECHO",
        description="Enable SQL query logging"
    )
    
    pool_size: int = Field(
        default=5,
        env="DATABASE_POOL_SIZE",
        description="Database connection pool size"
    )
    
    max_overflow: int = Field(
        default=10,
        env="DATABASE_MAX_OVERFLOW",
        description="Maximum database connection overflow"
    )
    
    class Config:
        env_prefix = "DATABASE_"


class GoogleSheetsSettings(BaseSettings):
    """Google Sheets API configuration."""
    
    credentials_file: Optional[Path] = Field(
        default=None,
        env="GOOGLE_CREDENTIALS_FILE",
        description="Path to Google service account credentials JSON file"
    )
    
    client_secrets_file: Optional[Path] = Field(
        default=None,
        env="GOOGLE_CLIENT_SECRETS_FILE",
        description="Path to Google OAuth client secrets JSON file"
    )
    
    scopes: List[str] = Field(
        default_factory=lambda: [
            'https://www.googleapis.com/auth/spreadsheets.readonly',
            'https://www.googleapis.com/auth/drive.readonly'
        ],
        description="Google API scopes"
    )
    
    rate_limit_requests: int = Field(
        default=100,
        env="GOOGLE_RATE_LIMIT_REQUESTS",
        description="Requests per minute rate limit"
    )
    
    rate_limit_period: int = Field(
        default=60,
        env="GOOGLE_RATE_LIMIT_PERIOD",
        description="Rate limit period in seconds"
    )
    
    @validator('credentials_file', 'client_secrets_file', pre=True)
    def validate_file_paths(cls, v):
        if v is None:
            return v
        path = Path(v)
        if not path.exists():
            raise ValueError(f"File does not exist: {path}")
        return path
    
    class Config:
        env_prefix = "GOOGLE_"


class ProcessingSettings(BaseSettings):
    """Data processing configuration."""
    
    batch_size: int = Field(
        default=1000,
        env="PROCESSING_BATCH_SIZE",
        description="Batch size for data processing operations"
    )
    
    max_concurrent_jobs: int = Field(
        default=5,
        env="PROCESSING_MAX_CONCURRENT_JOBS",
        description="Maximum number of concurrent processing jobs"
    )
    
    chunk_size: int = Field(
        default=10000,
        env="PROCESSING_CHUNK_SIZE",
        description="Chunk size for large data operations"
    )
    
    enable_data_validation: bool = Field(
        default=True,
        env="PROCESSING_ENABLE_DATA_VALIDATION",
        description="Enable data validation during processing"
    )
    
    validation_sample_size: int = Field(
        default=1000,
        env="PROCESSING_VALIDATION_SAMPLE_SIZE",
        description="Sample size for data validation"
    )
    
    retry_config: RetryConfig = Field(
        default_factory=RetryConfig,
        description="Retry configuration for failed operations"
    )
    
    class Config:
        env_prefix = "PROCESSING_"


class LoggingSettings(BaseSettings):
    """Logging configuration."""
    
    level: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="Logging level"
    )
    
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT",
        description="Log message format"
    )
    
    file: Optional[Path] = Field(
        default=None,
        env="LOG_FILE",
        description="Log file path"
    )
    
    max_file_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        env="LOG_MAX_FILE_SIZE",
        description="Maximum log file size in bytes"
    )
    
    backup_count: int = Field(
        default=5,
        env="LOG_BACKUP_COUNT",
        description="Number of log file backups to keep"
    )
    
    enable_structured_logging: bool = Field(
        default=True,
        env="LOG_ENABLE_STRUCTURED",
        description="Enable structured logging with JSON output"
    )
    
    class Config:
        env_prefix = "LOG_"


class MonitoringSettings(BaseSettings):
    """Monitoring and observability configuration."""
    
    enable_metrics: bool = Field(
        default=True,
        env="MONITORING_ENABLE_METRICS",
        description="Enable metrics collection"
    )
    
    metrics_port: int = Field(
        default=8080,
        env="MONITORING_METRICS_PORT",
        description="Port for metrics endpoint"
    )
    
    health_check_interval: int = Field(
        default=30,
        env="MONITORING_HEALTH_CHECK_INTERVAL",
        description="Health check interval in seconds"
    )
    
    enable_tracing: bool = Field(
        default=False,
        env="MONITORING_ENABLE_TRACING",
        description="Enable distributed tracing"
    )
    
    class Config:
        env_prefix = "MONITORING_"


class Settings(BaseSettings):
    """Main application settings."""
    
    # Application info
    app_name: str = Field(
        default="Hybrid Surveyor",
        env="APP_NAME",
        description="Application name"
    )
    
    app_version: str = Field(
        default="0.2.0",
        env="APP_VERSION",
        description="Application version"
    )
    
    debug: bool = Field(
        default=False,
        env="DEBUG",
        description="Enable debug mode"
    )
    
    # Default sheet URLs
    sheet_urls: List[HttpUrl] = Field(
        default_factory=lambda: [
            "https://docs.google.com/spreadsheets/d/1fAAXXGOiDWc8lMVaRwqvuM2CDNAyNY_Px3usyisGhaw/edit?gid=365352546#gid=365352546",
            "https://docs.google.com/spreadsheets/d/1qEHKDVIO4YTR3TjMt336HdKLIBMV2cebAcvdbGOUdCU/edit?usp=sharing",
            "https://docs.google.com/spreadsheets/d/1-aw7gjjvRMQj89lstVBtKDZ67Cs-dO1SHNsp4scJ4II/edit?usp=sharing",
            "https://docs.google.com/spreadsheets/d/1f3NKqhNR-CJr_e6_eLSTLbSFuYY8Gm0dxpSL0mlybMA/edit?usp=sharing",
            "https://docs.google.com/spreadsheets/d/1mQxcZ9U1UsVmHstgWdbHuT7bqfVXV4ZNCr9pn0TlVWM/edit?usp=sharing",
            "https://docs.google.com/spreadsheets/d/1h9AooI-E70v36EOxuErh4uYBg2TLbsF7X5kXdkrUkoQ/edit?usp=sharing"
        ],
        env="SHEET_URLS",
        description="Default Google Sheets URLs to process"
    )
    
    # Component settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    google_sheets: GoogleSheetsSettings = Field(default_factory=GoogleSheetsSettings)
    processing: ProcessingSettings = Field(default_factory=ProcessingSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
    @validator('sheet_urls', pre=True)
    def parse_sheet_urls(cls, v):
        if isinstance(v, str):
            # Handle comma-separated URLs from environment variable
            return [url.strip() for url in v.split(',') if url.strip()]
        return v


def load_settings() -> Settings:
    """Load and validate application settings."""
    return Settings()
