"""
Hybrid Surveyor - Advanced Google Sheets Data Extraction and Normalization Tool.

This package combines the best features from multiple approaches:
- Async architecture for high performance
- Mature dependency injection framework
- Flexible data pipeline with type safety
- Comprehensive error handling and recovery
- Production-ready configuration and monitoring
"""

__version__ = "0.2.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .core.exceptions import (
    HybridSurveyorException,
    ConfigurationError,
    AuthenticationError,
    DataExtractionError,
    DataTransformationError,
    DatabaseError,
)

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "HybridSurveyorException",
    "ConfigurationError", 
    "AuthenticationError",
    "DataExtractionError",
    "DataTransformationError",
    "DatabaseError",
]
