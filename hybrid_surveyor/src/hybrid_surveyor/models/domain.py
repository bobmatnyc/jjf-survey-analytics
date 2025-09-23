"""
Domain models for the Hybrid Surveyor application.

These models represent the core business entities and data structures
used throughout the application. They combine type safety from Pydantic
with the flexibility needed for data processing.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl, validator
import uuid


class JobStatus(str, Enum):
    """Enumeration of job statuses."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DataType(str, Enum):
    """Enumeration of detected data types."""
    TEXT = "text"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    JSON = "json"
    UNKNOWN = "unknown"


class WorksheetInfo(BaseModel):
    """Information about a worksheet within a spreadsheet."""
    id: str
    title: str
    row_count: int
    column_count: int
    gid: Optional[str] = None
    
    class Config:
        frozen = True


class SpreadsheetInfo(BaseModel):
    """Information about a Google Spreadsheet."""
    id: str
    title: str
    url: HttpUrl
    worksheets: List[WorksheetInfo]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        frozen = True


class ColumnSchema(BaseModel):
    """Schema information for a column."""
    name: str
    data_type: DataType
    nullable: bool = True
    unique: bool = False
    description: Optional[str] = None
    
    class Config:
        frozen = True


class TableSchema(BaseModel):
    """Schema information for a table."""
    name: str
    columns: List[ColumnSchema]
    primary_key: Optional[List[str]] = None
    indexes: Optional[List[List[str]]] = None
    
    class Config:
        frozen = True


class RawDataRecord(BaseModel):
    """Raw data record from a spreadsheet."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    data_source_id: str
    worksheet_id: Optional[str] = None
    row_number: int
    data: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed: bool = False
    processed_at: Optional[datetime] = None
    
    class Config:
        frozen = True


class NormalizedEntity(BaseModel):
    """Normalized entity after data transformation."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: str
    entity_data: Dict[str, Any]
    source_record_ids: List[str]
    schema_version: str = "1.0"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        frozen = True


class ProcessingJob(BaseModel):
    """Processing job for data transformation."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_type: str
    status: JobStatus = JobStatus.PENDING
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    records_processed: int = 0
    records_failed: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('completed_at')
    def validate_completed_at(cls, v, values):
        if v and values.get('started_at') and v < values['started_at']:
            raise ValueError('completed_at cannot be before started_at')
        return v


class DataExtractionJob(BaseModel):
    """Main data extraction job."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    status: JobStatus = JobStatus.PENDING
    sheet_urls: List[HttpUrl]
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    # Progress tracking
    total_spreadsheets: int = 0
    processed_spreadsheets: int = 0
    total_worksheets: int = 0
    processed_worksheets: int = 0
    total_rows: int = 0
    processed_rows: int = 0
    
    # Configuration
    extract_only: bool = False
    batch_size: int = 1000
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @property
    def progress_percentage(self) -> float:
        """Calculate overall progress percentage."""
        if self.total_rows == 0:
            return 0.0
        return (self.processed_rows / self.total_rows) * 100
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate job duration in seconds."""
        if not self.completed_at:
            return None
        return (self.completed_at - self.started_at).total_seconds()


class ValidationError(BaseModel):
    """Data validation error."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    record_id: Optional[str] = None
    field_name: Optional[str] = None
    error_type: str
    error_message: str
    raw_value: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        frozen = True


class DataQualityReport(BaseModel):
    """Data quality assessment report."""
    job_id: str
    total_records: int
    valid_records: int
    invalid_records: int
    validation_errors: List[ValidationError]
    quality_score: float = Field(ge=0.0, le=1.0)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('quality_score', pre=True, always=True)
    def calculate_quality_score(cls, v, values):
        total = values.get('total_records', 0)
        if total == 0:
            return 1.0
        valid = values.get('valid_records', 0)
        return valid / total
    
    class Config:
        frozen = True


class RetryConfig(BaseModel):
    """Configuration for retry behavior."""
    max_attempts: int = Field(default=3, ge=1, le=10)
    base_delay: float = Field(default=1.0, ge=0.1)
    max_delay: float = Field(default=60.0, ge=1.0)
    exponential_base: float = Field(default=2.0, ge=1.0)
    jitter: bool = True
    
    class Config:
        frozen = True
