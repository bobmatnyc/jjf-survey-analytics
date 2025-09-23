"""
Pytest configuration and fixtures for Hybrid Surveyor tests.
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

from hybrid_surveyor.config.settings import Settings, DatabaseSettings, GoogleSheetsSettings
from hybrid_surveyor.config.container import Container
from hybrid_surveyor.services.database_service import DatabaseService


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings with in-memory database."""
    return Settings(
        app_name="Hybrid Surveyor Test",
        debug=True,
        database=DatabaseSettings(
            url="sqlite+aiosqlite:///:memory:",
            echo=False
        ),
        google_sheets=GoogleSheetsSettings(
            credentials_file=None,
            rate_limit_requests=10,
            rate_limit_period=60
        ),
        sheet_urls=["https://docs.google.com/spreadsheets/d/test123/edit"]
    )


@pytest.fixture
async def database_service(test_settings: Settings) -> AsyncGenerator[DatabaseService, None]:
    """Create test database service with in-memory database."""
    service = DatabaseService(test_settings.database)
    await service.initialize()
    yield service
    await service.close()


@pytest.fixture
def mock_sheets_service() -> AsyncMock:
    """Create mock Google Sheets service."""
    mock = AsyncMock()
    mock.extract_spreadsheet_id.return_value = "test_spreadsheet_id"
    mock.get_spreadsheet_info.return_value = MagicMock(
        id="test_spreadsheet_id",
        title="Test Spreadsheet",
        url="https://docs.google.com/spreadsheets/d/test123/edit",
        worksheets=[
            MagicMock(
                id="worksheet1",
                title="Sheet1",
                row_count=100,
                column_count=5,
                gid="0"
            )
        ]
    )
    return mock


@pytest.fixture
def mock_container(test_settings: Settings, mock_sheets_service: AsyncMock) -> Container:
    """Create mock container for testing."""
    container = Container()
    container.settings.override(test_settings)
    container.sheets_service.override(mock_sheets_service)
    return container


@pytest.fixture
def sample_sheet_data():
    """Sample sheet data for testing."""
    return [
        {"Name": "John Doe", "Age": "30", "City": "New York", "Active": "true"},
        {"Name": "Jane Smith", "Age": "25", "City": "Los Angeles", "Active": "false"},
        {"Name": "Bob Johnson", "Age": "35", "City": "Chicago", "Active": "true"},
    ]


@pytest.fixture
def sample_spreadsheet_info():
    """Sample spreadsheet info for testing."""
    from hybrid_surveyor.models.domain import SpreadsheetInfo, WorksheetInfo
    
    return SpreadsheetInfo(
        id="test_spreadsheet_id",
        title="Test Spreadsheet",
        url="https://docs.google.com/spreadsheets/d/test123/edit",
        worksheets=[
            WorksheetInfo(
                id="worksheet1",
                title="Sheet1",
                row_count=100,
                column_count=4,
                gid="0"
            ),
            WorksheetInfo(
                id="worksheet2", 
                title="Sheet2",
                row_count=50,
                column_count=3,
                gid="1"
            )
        ]
    )


class AsyncContextManagerMock:
    """Helper class for mocking async context managers."""
    
    def __init__(self, return_value):
        self.return_value = return_value
    
    async def __aenter__(self):
        return self.return_value
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def mock_database_session():
    """Create mock database session."""
    session_mock = AsyncMock()
    session_mock.commit = AsyncMock()
    session_mock.rollback = AsyncMock()
    session_mock.refresh = AsyncMock()
    session_mock.close = AsyncMock()
    return session_mock
