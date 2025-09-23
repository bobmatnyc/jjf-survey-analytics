"""
Unit tests for domain models.
"""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from hybrid_surveyor.models.domain import (
    JobStatus, DataType, WorksheetInfo, SpreadsheetInfo,
    RawDataRecord, DataExtractionJob, ProcessingJob,
    ValidationError as DomainValidationError, RetryConfig
)


class TestJobStatus:
    """Test JobStatus enumeration."""
    
    def test_job_status_values(self):
        """Test job status enumeration values."""
        assert JobStatus.PENDING == "pending"
        assert JobStatus.RUNNING == "running"
        assert JobStatus.COMPLETED == "completed"
        assert JobStatus.FAILED == "failed"
        assert JobStatus.CANCELLED == "cancelled"


class TestDataType:
    """Test DataType enumeration."""
    
    def test_data_type_values(self):
        """Test data type enumeration values."""
        assert DataType.TEXT == "text"
        assert DataType.INTEGER == "integer"
        assert DataType.FLOAT == "float"
        assert DataType.BOOLEAN == "boolean"
        assert DataType.DATE == "date"
        assert DataType.DATETIME == "datetime"
        assert DataType.JSON == "json"
        assert DataType.UNKNOWN == "unknown"


class TestWorksheetInfo:
    """Test WorksheetInfo model."""
    
    def test_worksheet_info_creation(self):
        """Test creating worksheet info."""
        worksheet = WorksheetInfo(
            id="ws123",
            title="Test Sheet",
            row_count=100,
            column_count=5,
            gid="0"
        )
        
        assert worksheet.id == "ws123"
        assert worksheet.title == "Test Sheet"
        assert worksheet.row_count == 100
        assert worksheet.column_count == 5
        assert worksheet.gid == "0"
    
    def test_worksheet_info_optional_gid(self):
        """Test worksheet info with optional GID."""
        worksheet = WorksheetInfo(
            id="ws123",
            title="Test Sheet",
            row_count=100,
            column_count=5
        )
        
        assert worksheet.gid is None
    
    def test_worksheet_info_immutable(self):
        """Test that worksheet info is immutable."""
        worksheet = WorksheetInfo(
            id="ws123",
            title="Test Sheet",
            row_count=100,
            column_count=5
        )
        
        with pytest.raises(ValidationError):
            worksheet.title = "New Title"


class TestSpreadsheetInfo:
    """Test SpreadsheetInfo model."""
    
    def test_spreadsheet_info_creation(self):
        """Test creating spreadsheet info."""
        worksheets = [
            WorksheetInfo(id="ws1", title="Sheet1", row_count=100, column_count=5),
            WorksheetInfo(id="ws2", title="Sheet2", row_count=50, column_count=3)
        ]
        
        spreadsheet = SpreadsheetInfo(
            id="ss123",
            title="Test Spreadsheet",
            url="https://docs.google.com/spreadsheets/d/ss123/edit",
            worksheets=worksheets
        )
        
        assert spreadsheet.id == "ss123"
        assert spreadsheet.title == "Test Spreadsheet"
        assert len(spreadsheet.worksheets) == 2
        assert isinstance(spreadsheet.created_at, datetime)
    
    def test_spreadsheet_info_url_validation(self):
        """Test URL validation in spreadsheet info."""
        with pytest.raises(ValidationError):
            SpreadsheetInfo(
                id="ss123",
                title="Test Spreadsheet",
                url="not-a-valid-url",
                worksheets=[]
            )


class TestRawDataRecord:
    """Test RawDataRecord model."""
    
    def test_raw_data_record_creation(self):
        """Test creating raw data record."""
        record = RawDataRecord(
            data_source_id="ds123",
            worksheet_id="ws123",
            row_number=1,
            data={"name": "John", "age": 30}
        )
        
        assert record.data_source_id == "ds123"
        assert record.worksheet_id == "ws123"
        assert record.row_number == 1
        assert record.data == {"name": "John", "age": 30}
        assert record.processed is False
        assert record.processed_at is None
        assert isinstance(record.created_at, datetime)
        assert len(record.id) > 0  # UUID should be generated
    
    def test_raw_data_record_optional_fields(self):
        """Test raw data record with optional fields."""
        record = RawDataRecord(
            data_source_id="ds123",
            row_number=1,
            data={"name": "John"}
        )
        
        assert record.worksheet_id is None


class TestDataExtractionJob:
    """Test DataExtractionJob model."""
    
    def test_data_extraction_job_creation(self):
        """Test creating data extraction job."""
        job = DataExtractionJob(
            name="Test Job",
            sheet_urls=["https://docs.google.com/spreadsheets/d/123/edit"]
        )
        
        assert job.name == "Test Job"
        assert len(job.sheet_urls) == 1
        assert job.status == JobStatus.PENDING
        assert job.total_spreadsheets == 0
        assert job.processed_spreadsheets == 0
        assert job.extract_only is False
        assert job.batch_size == 1000
        assert isinstance(job.started_at, datetime)
        assert len(job.id) > 0
    
    def test_progress_percentage_calculation(self):
        """Test progress percentage calculation."""
        job = DataExtractionJob(
            name="Test Job",
            sheet_urls=["https://docs.google.com/spreadsheets/d/123/edit"],
            total_rows=100,
            processed_rows=25
        )
        
        assert job.progress_percentage == 25.0
    
    def test_progress_percentage_zero_total(self):
        """Test progress percentage with zero total rows."""
        job = DataExtractionJob(
            name="Test Job",
            sheet_urls=["https://docs.google.com/spreadsheets/d/123/edit"],
            total_rows=0,
            processed_rows=0
        )
        
        assert job.progress_percentage == 0.0
    
    def test_duration_calculation(self):
        """Test duration calculation."""
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(seconds=30)
        
        job = DataExtractionJob(
            name="Test Job",
            sheet_urls=["https://docs.google.com/spreadsheets/d/123/edit"],
            started_at=start_time,
            completed_at=end_time
        )
        
        assert job.duration == 30.0
    
    def test_duration_not_completed(self):
        """Test duration when job not completed."""
        job = DataExtractionJob(
            name="Test Job",
            sheet_urls=["https://docs.google.com/spreadsheets/d/123/edit"]
        )
        
        assert job.duration is None


class TestProcessingJob:
    """Test ProcessingJob model."""
    
    def test_processing_job_creation(self):
        """Test creating processing job."""
        job = ProcessingJob(
            job_type="normalization"
        )
        
        assert job.job_type == "normalization"
        assert job.status == JobStatus.PENDING
        assert job.records_processed == 0
        assert job.records_failed == 0
        assert isinstance(job.started_at, datetime)
        assert len(job.id) > 0
    
    def test_completed_at_validation(self):
        """Test completed_at validation."""
        start_time = datetime.utcnow()
        
        # This should work - completed after started
        job = ProcessingJob(
            job_type="test",
            started_at=start_time,
            completed_at=start_time + timedelta(seconds=10)
        )
        assert job.completed_at > job.started_at
        
        # This should fail - completed before started
        with pytest.raises(ValidationError):
            ProcessingJob(
                job_type="test",
                started_at=start_time,
                completed_at=start_time - timedelta(seconds=10)
            )


class TestRetryConfig:
    """Test RetryConfig model."""
    
    def test_retry_config_defaults(self):
        """Test retry config default values."""
        config = RetryConfig()
        
        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True
    
    def test_retry_config_validation(self):
        """Test retry config validation."""
        # Valid config
        config = RetryConfig(
            max_attempts=5,
            base_delay=0.5,
            max_delay=120.0
        )
        assert config.max_attempts == 5
        
        # Invalid max_attempts (too low)
        with pytest.raises(ValidationError):
            RetryConfig(max_attempts=0)
        
        # Invalid max_attempts (too high)
        with pytest.raises(ValidationError):
            RetryConfig(max_attempts=15)
        
        # Invalid base_delay (too low)
        with pytest.raises(ValidationError):
            RetryConfig(base_delay=0.05)
