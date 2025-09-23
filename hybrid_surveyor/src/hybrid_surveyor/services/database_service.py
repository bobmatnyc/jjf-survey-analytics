"""
Database service for managing database operations.

This service provides async database operations with connection pooling,
transaction management, and comprehensive error handling.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, AsyncContextManager
from contextlib import asynccontextmanager
from datetime import datetime
import pandas as pd

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text, select, func

from ..core.interfaces import IDatabaseService
from ..core.exceptions import DatabaseError, ConfigurationError
from ..config.settings import DatabaseSettings
from ..models.database import (
    Base, DataSource, Worksheet, RawDataRecord, DataExtractionJob,
    ProcessingJob, NormalizedEntity, ValidationError, create_tables
)
from ..models.domain import ProcessingJob as DomainProcessingJob

logger = logging.getLogger(__name__)


class DatabaseService(IDatabaseService):
    """
    Async database service with comprehensive features.
    
    Features:
    - Async SQLAlchemy with connection pooling
    - Transaction management
    - Batch operations for performance
    - Health checking
    - Migration support
    """
    
    def __init__(self, settings: DatabaseSettings):
        self.settings = settings
        self._engine = None
        self._session_factory = None
        self._initialized = False
    
    @property
    def engine(self):
        """Get database engine, creating if necessary."""
        if self._engine is None:
            self._engine = create_async_engine(
                self.settings.url,
                echo=self.settings.echo,
                pool_size=self.settings.pool_size,
                max_overflow=self.settings.max_overflow,
                pool_pre_ping=True,
                pool_recycle=3600,
            )
        return self._engine
    
    @property
    def session_factory(self):
        """Get session factory, creating if necessary."""
        if self._session_factory is None:
            self._session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
        return self._session_factory
    
    @asynccontextmanager
    async def get_session(self) -> AsyncContextManager[AsyncSession]:
        """Get database session with automatic cleanup."""
        async with self.session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def initialize(self) -> None:
        """Initialize database schema."""
        try:
            # For SQLite, we need to use sync operations for table creation
            if "sqlite" in self.settings.url:
                # Convert async URL to sync for table creation
                sync_url = self.settings.url.replace("+aiosqlite", "")
                from sqlalchemy import create_engine
                sync_engine = create_engine(sync_url)
                Base.metadata.create_all(sync_engine)
                sync_engine.dispose()
            else:
                # For other databases, use async approach
                async with self.engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
            
            self._initialized = True
            logger.info("Database initialized successfully")
            
        except Exception as e:
            raise DatabaseError(
                "Failed to initialize database",
                details={"error": str(e), "url": self.settings.url},
                cause=e
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check."""
        try:
            async with self.get_session() as session:
                # Simple query to test connectivity
                result = await session.execute(text("SELECT 1"))
                result.fetchone()
                
                return {
                    "status": "healthy",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            raise DatabaseError(
                "Database health check failed",
                details={"error": str(e)},
                cause=e
            )
    
    async def create_data_source(
        self,
        url: str,
        title: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DataSource:
        """Create a new data source record."""
        try:
            # Extract spreadsheet ID from URL
            import re
            pattern = r'/spreadsheets/d/([a-zA-Z0-9-_]+)'
            match = re.search(pattern, url)
            if not match:
                raise ValueError(f"Invalid Google Sheets URL: {url}")
            
            spreadsheet_id = match.group(1)
            
            async with self.get_session() as session:
                # Check if data source already exists
                existing = await session.execute(
                    select(DataSource).where(DataSource.spreadsheet_id == spreadsheet_id)
                )
                existing_source = existing.scalar_one_or_none()
                
                if existing_source:
                    # Update existing source
                    existing_source.url = url
                    existing_source.title = title
                    existing_source.last_synced = datetime.utcnow()
                    if metadata:
                        existing_source.metadata = metadata
                    
                    await session.commit()
                    await session.refresh(existing_source)
                    return existing_source
                else:
                    # Create new source
                    data_source = DataSource(
                        spreadsheet_id=spreadsheet_id,
                        url=url,
                        title=title,
                        metadata=metadata or {}
                    )
                    
                    session.add(data_source)
                    await session.commit()
                    await session.refresh(data_source)
                    return data_source
                    
        except Exception as e:
            raise DatabaseError(
                "Failed to create data source",
                details={"url": url, "title": title, "error": str(e)},
                cause=e
            )
    
    async def save_raw_data(
        self,
        data_source_id: str,
        worksheet_id: str,
        data: List[Dict[str, Any]]
    ) -> List[RawDataRecord]:
        """Save raw data records in batches."""
        try:
            records = []
            
            async with self.get_session() as session:
                for i, row_data in enumerate(data):
                    # Create data hash for deduplication
                    import hashlib
                    import json
                    data_str = json.dumps(row_data, sort_keys=True)
                    data_hash = hashlib.sha256(data_str.encode()).hexdigest()
                    
                    record = RawDataRecord(
                        data_source_id=data_source_id,
                        worksheet_id=worksheet_id,
                        row_number=i + 1,
                        data=row_data,
                        data_hash=data_hash
                    )
                    records.append(record)
                
                # Batch insert
                session.add_all(records)
                await session.commit()
                
                # Refresh all records
                for record in records:
                    await session.refresh(record)
                
                return records
                
        except Exception as e:
            raise DatabaseError(
                "Failed to save raw data",
                details={
                    "data_source_id": data_source_id,
                    "worksheet_id": worksheet_id,
                    "record_count": len(data),
                    "error": str(e)
                },
                cause=e
            )
    
    async def save_normalized_data(
        self,
        table_name: str,
        data: pd.DataFrame,
        if_exists: str = "append"
    ) -> None:
        """Save normalized data to a table."""
        try:
            # Convert async engine to sync for pandas compatibility
            sync_url = self.settings.url.replace("+aiosqlite", "")
            
            # Use pandas to_sql for efficient bulk insert
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: data.to_sql(
                    table_name,
                    sync_url,
                    if_exists=if_exists,
                    index=False,
                    method='multi'
                )
            )
            
            logger.info(f"Saved {len(data)} records to table '{table_name}'")
            
        except Exception as e:
            raise DatabaseError(
                "Failed to save normalized data",
                details={
                    "table_name": table_name,
                    "record_count": len(data),
                    "error": str(e)
                },
                cause=e
            )
    
    async def create_processing_job(
        self,
        job_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DomainProcessingJob:
        """Create a new processing job."""
        try:
            async with self.get_session() as session:
                job = ProcessingJob(
                    job_type=job_type,
                    metadata=metadata or {},
                    started_at=datetime.utcnow()
                )
                
                session.add(job)
                await session.commit()
                await session.refresh(job)
                
                # Convert to domain model
                return DomainProcessingJob(
                    id=job.id,
                    job_type=job.job_type,
                    status=job.status,
                    started_at=job.started_at,
                    completed_at=job.completed_at,
                    error_message=job.error_message,
                    records_processed=job.records_processed,
                    records_failed=job.records_failed,
                    metadata=job.metadata or {}
                )
                
        except Exception as e:
            raise DatabaseError(
                "Failed to create processing job",
                details={"job_type": job_type, "error": str(e)},
                cause=e
            )
    
    async def update_processing_job(
        self,
        job_id: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> DomainProcessingJob:
        """Update processing job status."""
        try:
            async with self.get_session() as session:
                job = await session.get(ProcessingJob, job_id)
                if not job:
                    raise ValueError(f"Processing job not found: {job_id}")
                
                job.status = status
                if metadata:
                    job.metadata = {**(job.metadata or {}), **metadata}
                if error_message:
                    job.error_message = error_message
                if status in ["completed", "failed", "cancelled"]:
                    job.completed_at = datetime.utcnow()
                
                await session.commit()
                await session.refresh(job)
                
                # Convert to domain model
                return DomainProcessingJob(
                    id=job.id,
                    job_type=job.job_type,
                    status=job.status,
                    started_at=job.started_at,
                    completed_at=job.completed_at,
                    error_message=job.error_message,
                    records_processed=job.records_processed,
                    records_failed=job.records_failed,
                    metadata=job.metadata or {}
                )
                
        except Exception as e:
            raise DatabaseError(
                "Failed to update processing job",
                details={"job_id": job_id, "status": status, "error": str(e)},
                cause=e
            )
    
    async def close(self) -> None:
        """Close database connections."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
