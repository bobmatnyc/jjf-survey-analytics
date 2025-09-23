"""
Interface definitions for the Hybrid Surveyor application.

This module defines abstract base classes that establish contracts for
different components of the system, enabling dependency injection and
testability.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncIterator
from datetime import datetime
import pandas as pd

from ..models.domain import (
    SpreadsheetInfo, WorksheetInfo, RawDataRecord, ProcessingJob,
    DataExtractionJob, NormalizedEntity
)


class ISheetsService(ABC):
    """Interface for Google Sheets data extraction service."""
    
    @abstractmethod
    async def get_spreadsheet_info(self, sheet_url: str) -> SpreadsheetInfo:
        """Get metadata about a spreadsheet."""
        pass
    
    @abstractmethod
    async def get_worksheet_data(
        self, 
        sheet_url: str, 
        worksheet_name: Optional[str] = None
    ) -> pd.DataFrame:
        """Get data from a specific worksheet."""
        pass
    
    @abstractmethod
    async def get_all_worksheets(self, sheet_url: str) -> List[WorksheetInfo]:
        """Get information about all worksheets in a spreadsheet."""
        pass
    
    @abstractmethod
    def extract_spreadsheet_id(self, sheet_url: str) -> str:
        """Extract spreadsheet ID from URL."""
        pass


class IDataTransformationService(ABC):
    """Interface for data transformation and normalization service."""
    
    @abstractmethod
    async def transform_raw_data(
        self, 
        raw_data: pd.DataFrame, 
        source_info: SpreadsheetInfo
    ) -> pd.DataFrame:
        """Transform raw data with cleaning and type conversion."""
        pass
    
    @abstractmethod
    async def normalize_data(
        self, 
        transformed_data: List[pd.DataFrame]
    ) -> Dict[str, pd.DataFrame]:
        """Normalize data into structured entities."""
        pass
    
    @abstractmethod
    async def detect_schema(self, data: pd.DataFrame) -> Dict[str, str]:
        """Detect data types and schema from DataFrame."""
        pass


class IDatabaseService(ABC):
    """Interface for database operations."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize database schema."""
        pass
    
    @abstractmethod
    async def create_data_source(
        self, 
        url: str, 
        title: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Create a new data source record."""
        pass
    
    @abstractmethod
    async def save_raw_data(
        self,
        data_source_id: str,
        worksheet_id: str,
        data: List[Dict[str, Any]]
    ) -> List[RawDataRecord]:
        """Save raw data records."""
        pass
    
    @abstractmethod
    async def save_normalized_data(
        self,
        table_name: str,
        data: pd.DataFrame,
        if_exists: str = "append"
    ) -> None:
        """Save normalized data to a table."""
        pass
    
    @abstractmethod
    async def create_processing_job(
        self,
        job_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProcessingJob:
        """Create a new processing job."""
        pass
    
    @abstractmethod
    async def update_processing_job(
        self,
        job_id: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> ProcessingJob:
        """Update processing job status."""
        pass


class IRepository(ABC):
    """Generic repository interface."""
    
    @abstractmethod
    async def save(self, entity: Any) -> Any:
        """Save an entity."""
        pass
    
    @abstractmethod
    async def find_by_id(self, entity_id: str) -> Optional[Any]:
        """Find entity by ID."""
        pass
    
    @abstractmethod
    async def find_all(self, limit: Optional[int] = None) -> List[Any]:
        """Find all entities."""
        pass
    
    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """Delete an entity."""
        pass


class IDataExtractionService(ABC):
    """Interface for the main data extraction orchestration service."""
    
    @abstractmethod
    async def extract_and_process(
        self,
        sheet_urls: List[str],
        job_name: Optional[str] = None,
        extract_only: bool = False
    ) -> DataExtractionJob:
        """Extract and optionally process data from multiple sheets."""
        pass
    
    @abstractmethod
    async def process_unprocessed_data(
        self,
        batch_size: int = 1000
    ) -> ProcessingJob:
        """Process previously extracted but unprocessed data."""
        pass
    
    @abstractmethod
    async def get_job_status(self, job_id: str) -> Optional[DataExtractionJob]:
        """Get status of a data extraction job."""
        pass


class IRetryStrategy(ABC):
    """Interface for retry strategies."""
    
    @abstractmethod
    async def execute_with_retry(
        self,
        operation: Any,
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """Execute operation with retry logic."""
        pass


class IHealthChecker(ABC):
    """Interface for health checking services."""
    
    @abstractmethod
    async def check_health(self) -> Dict[str, Any]:
        """Check health of the service."""
        pass
    
    @abstractmethod
    async def check_dependencies(self) -> Dict[str, bool]:
        """Check health of external dependencies."""
        pass
