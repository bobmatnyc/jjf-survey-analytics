"""
Unit tests for configuration and settings.
"""

import pytest
from pathlib import Path
from pydantic import ValidationError

from hybrid_surveyor.config.settings import (
    Settings, DatabaseSettings, GoogleSheetsSettings,
    ProcessingSettings, LoggingSettings, load_settings
)


class TestDatabaseSettings:
    """Test database configuration settings."""
    
    def test_default_settings(self):
        """Test default database settings."""
        settings = DatabaseSettings()
        
        assert settings.url == "sqlite+aiosqlite:///hybrid_surveyor.db"
        assert settings.echo is False
        assert settings.pool_size == 5
        assert settings.max_overflow == 10
    
    def test_custom_settings(self):
        """Test custom database settings."""
        settings = DatabaseSettings(
            url="postgresql+asyncpg://user:pass@localhost/db",
            echo=True,
            pool_size=10,
            max_overflow=20
        )
        
        assert settings.url == "postgresql+asyncpg://user:pass@localhost/db"
        assert settings.echo is True
        assert settings.pool_size == 10
        assert settings.max_overflow == 20


class TestGoogleSheetsSettings:
    """Test Google Sheets configuration settings."""
    
    def test_default_settings(self):
        """Test default Google Sheets settings."""
        settings = GoogleSheetsSettings()
        
        assert settings.credentials_file is None
        assert settings.client_secrets_file is None
        assert len(settings.scopes) == 2
        assert 'https://www.googleapis.com/auth/spreadsheets.readonly' in settings.scopes
        assert settings.rate_limit_requests == 100
        assert settings.rate_limit_period == 60
    
    def test_file_validation_nonexistent(self):
        """Test file validation for non-existent files."""
        with pytest.raises(ValidationError):
            GoogleSheetsSettings(credentials_file="/nonexistent/file.json")
    
    def test_file_validation_none(self):
        """Test file validation with None values."""
        settings = GoogleSheetsSettings(
            credentials_file=None,
            client_secrets_file=None
        )
        
        assert settings.credentials_file is None
        assert settings.client_secrets_file is None


class TestProcessingSettings:
    """Test processing configuration settings."""
    
    def test_default_settings(self):
        """Test default processing settings."""
        settings = ProcessingSettings()
        
        assert settings.batch_size == 1000
        assert settings.max_concurrent_jobs == 5
        assert settings.chunk_size == 10000
        assert settings.enable_data_validation is True
        assert settings.validation_sample_size == 1000
        assert settings.retry_config.max_attempts == 3
    
    def test_custom_settings(self):
        """Test custom processing settings."""
        settings = ProcessingSettings(
            batch_size=2000,
            max_concurrent_jobs=10,
            enable_data_validation=False
        )
        
        assert settings.batch_size == 2000
        assert settings.max_concurrent_jobs == 10
        assert settings.enable_data_validation is False


class TestLoggingSettings:
    """Test logging configuration settings."""
    
    def test_default_settings(self):
        """Test default logging settings."""
        settings = LoggingSettings()
        
        assert settings.level == "INFO"
        assert "%(asctime)s" in settings.format
        assert settings.file is None
        assert settings.max_file_size == 10 * 1024 * 1024
        assert settings.backup_count == 5
        assert settings.enable_structured_logging is True


class TestMainSettings:
    """Test main application settings."""
    
    def test_default_settings(self):
        """Test default application settings."""
        settings = Settings()
        
        assert settings.app_name == "Hybrid Surveyor"
        assert settings.app_version == "0.2.0"
        assert settings.debug is False
        assert len(settings.sheet_urls) == 6
        
        # Check that all component settings are present
        assert isinstance(settings.database, DatabaseSettings)
        assert isinstance(settings.google_sheets, GoogleSheetsSettings)
        assert isinstance(settings.processing, ProcessingSettings)
        assert isinstance(settings.logging, LoggingSettings)
    
    def test_sheet_urls_parsing_string(self):
        """Test parsing sheet URLs from comma-separated string."""
        url_string = "https://docs.google.com/spreadsheets/d/1/edit,https://docs.google.com/spreadsheets/d/2/edit"
        
        # This would normally be handled by environment variable parsing
        urls = [url.strip() for url in url_string.split(',')]
        
        assert len(urls) == 2
        assert "spreadsheets/d/1" in urls[0]
        assert "spreadsheets/d/2" in urls[1]
    
    def test_load_settings_function(self):
        """Test the load_settings function."""
        settings = load_settings()
        
        assert isinstance(settings, Settings)
        assert settings.app_name == "Hybrid Surveyor"


class TestSettingsValidation:
    """Test settings validation."""
    
    def test_invalid_sheet_url(self):
        """Test validation of invalid sheet URLs."""
        with pytest.raises(ValidationError):
            Settings(sheet_urls=["not-a-valid-url"])
    
    def test_valid_sheet_urls(self):
        """Test validation of valid sheet URLs."""
        valid_urls = [
            "https://docs.google.com/spreadsheets/d/1fAAXXGOiDWc8lMVaRwqvuM2CDNAyNY_Px3usyisGhaw/edit",
            "https://docs.google.com/spreadsheets/d/1qEHKDVIO4YTR3TjMt336HdKLIBMV2cebAcvdbGOUdCU/edit?usp=sharing"
        ]
        
        settings = Settings(sheet_urls=valid_urls)
        assert len(settings.sheet_urls) == 2
