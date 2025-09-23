"""
Database models for the Hybrid Surveyor application.

This module combines the flexible raw+processed approach from sheets_processor
with the type safety and structure from Surveyor. It provides both raw data
storage for reprocessing and strongly-typed normalized tables.
"""

from sqlalchemy import (
    Column, String, Integer, DateTime, Boolean, Text, JSON, Float,
    ForeignKey, Index, create_engine, MetaData, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional
import uuid

Base = declarative_base()
metadata = MetaData()


class TimestampMixin:
    """Mixin for timestamp fields."""
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class DataSource(Base, TimestampMixin):
    """Represents a Google Spreadsheet data source."""
    __tablename__ = 'data_sources'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    spreadsheet_id = Column(String, nullable=False, unique=True, index=True)
    url = Column(Text, nullable=False)
    title = Column(String(500))
    source_type = Column(String(50), default='google_sheets')
    last_synced = Column(DateTime)
    is_active = Column(Boolean, default=True)
    metadata = Column(JSON)
    
    # Relationships
    worksheets = relationship("Worksheet", back_populates="data_source", cascade="all, delete-orphan")
    raw_records = relationship("RawDataRecord", back_populates="data_source", cascade="all, delete-orphan")
    extraction_jobs = relationship("DataExtractionJob", back_populates="data_source")
    
    __table_args__ = (
        Index('idx_data_source_active', 'is_active'),
        Index('idx_data_source_last_synced', 'last_synced'),
    )


class Worksheet(Base, TimestampMixin):
    """Represents a worksheet within a spreadsheet."""
    __tablename__ = 'worksheets'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    data_source_id = Column(String, ForeignKey('data_sources.id'), nullable=False)
    name = Column(String(255), nullable=False)
    gid = Column(String(50))  # Google's internal worksheet ID
    row_count = Column(Integer, default=0)
    column_count = Column(Integer, default=0)
    last_updated = Column(DateTime)
    schema_detected = Column(JSON)  # Detected column schemas
    
    # Relationships
    data_source = relationship("DataSource", back_populates="worksheets")
    raw_records = relationship("RawDataRecord", back_populates="worksheet", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_worksheet_data_source', 'data_source_id'),
        UniqueConstraint('data_source_id', 'name', name='uq_worksheet_data_source_name'),
    )


class RawDataRecord(Base, TimestampMixin):
    """Raw data record from spreadsheet extraction."""
    __tablename__ = 'raw_data_records'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    data_source_id = Column(String, ForeignKey('data_sources.id'), nullable=False)
    worksheet_id = Column(String, ForeignKey('worksheets.id'))
    row_number = Column(Integer, nullable=False)
    data = Column(JSON, nullable=False)  # Raw row data as JSON
    data_hash = Column(String(64))  # Hash for deduplication
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime)
    processing_errors = Column(JSON)  # Any errors during processing
    
    # Relationships
    data_source = relationship("DataSource", back_populates="raw_records")
    worksheet = relationship("Worksheet", back_populates="raw_records")
    
    __table_args__ = (
        Index('idx_raw_data_source', 'data_source_id'),
        Index('idx_raw_worksheet', 'worksheet_id'),
        Index('idx_raw_processed', 'processed'),
        Index('idx_raw_hash', 'data_hash'),
        Index('idx_raw_row_number', 'row_number'),
    )


class DataExtractionJob(Base, TimestampMixin):
    """Tracks data extraction jobs."""
    __tablename__ = 'data_extraction_jobs'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    status = Column(String(50), default='pending')  # pending, running, completed, failed, cancelled
    data_source_id = Column(String, ForeignKey('data_sources.id'))
    
    # Progress tracking
    total_spreadsheets = Column(Integer, default=0)
    processed_spreadsheets = Column(Integer, default=0)
    total_worksheets = Column(Integer, default=0)
    processed_worksheets = Column(Integer, default=0)
    total_rows = Column(Integer, default=0)
    processed_rows = Column(Integer, default=0)
    
    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Configuration and metadata
    extract_only = Column(Boolean, default=False)
    batch_size = Column(Integer, default=1000)
    sheet_urls = Column(JSON)  # List of URLs being processed
    error_message = Column(Text)
    metadata = Column(JSON)
    
    # Relationships
    data_source = relationship("DataSource", back_populates="extraction_jobs")
    processing_jobs = relationship("ProcessingJob", back_populates="extraction_job")
    
    __table_args__ = (
        Index('idx_extraction_job_status', 'status'),
        Index('idx_extraction_job_started', 'started_at'),
    )


class ProcessingJob(Base, TimestampMixin):
    """Tracks data processing and normalization jobs."""
    __tablename__ = 'processing_jobs'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    extraction_job_id = Column(String, ForeignKey('data_extraction_jobs.id'))
    job_type = Column(String(100), nullable=False)  # normalization, validation, etc.
    status = Column(String(50), default='pending')
    
    # Progress tracking
    records_processed = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    records_skipped = Column(Integer, default=0)
    
    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Configuration
    batch_size = Column(Integer, default=1000)
    metadata = Column(JSON)
    
    # Relationships
    extraction_job = relationship("DataExtractionJob", back_populates="processing_jobs")
    validation_errors = relationship("ValidationError", back_populates="processing_job")
    
    __table_args__ = (
        Index('idx_processing_job_status', 'status'),
        Index('idx_processing_job_type', 'job_type'),
        Index('idx_processing_extraction_job', 'extraction_job_id'),
    )


class NormalizedEntity(Base, TimestampMixin):
    """Normalized entities after data transformation."""
    __tablename__ = 'normalized_entities'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type = Column(String(100), nullable=False)
    entity_data = Column(JSON, nullable=False)
    source_record_ids = Column(JSON)  # List of source raw record IDs
    schema_version = Column(String(20), default='1.0')
    data_hash = Column(String(64))  # Hash for deduplication
    
    __table_args__ = (
        Index('idx_normalized_entity_type', 'entity_type'),
        Index('idx_normalized_hash', 'data_hash'),
        Index('idx_normalized_schema_version', 'schema_version'),
    )


class ValidationError(Base, TimestampMixin):
    """Data validation errors."""
    __tablename__ = 'validation_errors'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    processing_job_id = Column(String, ForeignKey('processing_jobs.id'))
    record_id = Column(String)  # ID of the record that failed validation
    field_name = Column(String(255))
    error_type = Column(String(100))  # type_conversion, missing_required, invalid_format, etc.
    error_message = Column(Text)
    raw_value = Column(Text)
    expected_type = Column(String(50))
    severity = Column(String(20), default='error')  # error, warning, info
    
    # Relationships
    processing_job = relationship("ProcessingJob", back_populates="validation_errors")
    
    __table_args__ = (
        Index('idx_validation_error_job', 'processing_job_id'),
        Index('idx_validation_error_type', 'error_type'),
        Index('idx_validation_error_severity', 'severity'),
    )


class SystemMetrics(Base, TimestampMixin):
    """System performance and health metrics."""
    __tablename__ = 'system_metrics'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float)
    metric_unit = Column(String(50))
    tags = Column(JSON)  # Additional metadata tags
    recorded_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_metrics_name', 'metric_name'),
        Index('idx_metrics_recorded', 'recorded_at'),
    )


def create_database_engine(database_url: str, echo: bool = False, **kwargs):
    """Create database engine with optimized settings."""
    return create_engine(
        database_url,
        echo=echo,
        pool_pre_ping=True,
        pool_recycle=3600,
        **kwargs
    )


def create_session_factory(engine):
    """Create session factory."""
    return sessionmaker(bind=engine, expire_on_commit=False)


def create_tables(engine):
    """Create all tables."""
    Base.metadata.create_all(engine)


def drop_tables(engine):
    """Drop all tables (useful for testing)."""
    Base.metadata.drop_all(engine)
