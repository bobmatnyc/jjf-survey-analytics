"""
Dependency injection container for the Hybrid Surveyor application.

This module uses the dependency-injector library to provide a mature,
feature-rich DI container with automatic wiring and provider patterns.
"""

from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject

from .settings import Settings, load_settings
from ..services.sheets_service import GoogleSheetsService
from ..services.data_transformation_service import DataTransformationService
from ..services.database_service import DatabaseService
from ..services.data_extraction_service import DataExtractionService
from ..repositories.database_repository import DatabaseRepository
from ..utils.retry_strategy import ExponentialBackoffRetry
from ..utils.health_checker import HealthChecker


class Container(containers.DeclarativeContainer):
    """Main dependency injection container."""
    
    # Configuration for automatic wiring
    wiring_config = containers.WiringConfiguration(
        modules=[
            "hybrid_surveyor.cli.main",
            "hybrid_surveyor.cli.commands",
            "hybrid_surveyor.services.data_extraction_service",
            "hybrid_surveyor.services.sheets_service",
            "hybrid_surveyor.services.data_transformation_service",
            "hybrid_surveyor.services.database_service",
        ]
    )
    
    # Configuration providers
    config = providers.Configuration()
    
    settings = providers.Singleton(
        load_settings
    )
    
    # Utility providers
    retry_strategy = providers.Factory(
        ExponentialBackoffRetry,
        config=settings.provided.processing.retry_config
    )
    
    health_checker = providers.Factory(
        HealthChecker,
        settings=settings
    )
    
    # Service providers
    sheets_service = providers.Factory(
        GoogleSheetsService,
        settings=settings.provided.google_sheets,
        retry_strategy=retry_strategy
    )
    
    data_transformation_service = providers.Factory(
        DataTransformationService,
        settings=settings.provided.processing
    )
    
    database_service = providers.Singleton(
        DatabaseService,
        settings=settings.provided.database
    )
    
    # Repository providers
    database_repository = providers.Factory(
        DatabaseRepository,
        database_service=database_service
    )
    
    # Main orchestration service
    data_extraction_service = providers.Factory(
        DataExtractionService,
        sheets_service=sheets_service,
        data_transformation_service=data_transformation_service,
        database_service=database_service,
        repository=database_repository,
        settings=settings.provided.processing
    )


# Global container instance
container = Container()


def wire_container() -> None:
    """Wire the container for dependency injection."""
    container.wire(modules=[
        "hybrid_surveyor.cli.main",
        "hybrid_surveyor.cli.commands",
    ])


def unwire_container() -> None:
    """Unwire the container (useful for testing)."""
    container.unwire()


# Convenience functions for common injections
def get_settings() -> Settings:
    """Get application settings."""
    return container.settings()


def get_data_extraction_service():
    """Get data extraction service."""
    return container.data_extraction_service()


def get_database_service():
    """Get database service."""
    return container.database_service()


def get_sheets_service():
    """Get Google Sheets service."""
    return container.sheets_service()


# Decorators for dependency injection
def inject_settings(func):
    """Decorator to inject settings into a function."""
    return inject(func)


def inject_services(func):
    """Decorator to inject all main services into a function."""
    return inject(func)
