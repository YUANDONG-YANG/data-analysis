"""Core interfaces, config, and shared building blocks."""
from .interfaces import (
    IDataLoader,
    IDataProcessor,
    IMetricsCalculator,
    IAPIClient,
    IConfiguration
)
from .exceptions import (
    DataIntegrationError,
    DataLoadError,
    DataProcessError,
    APIClientError,
    ConfigurationError
)
from .config import AppConfig, DataConfig, APIConfig
from .clients import APIClient
from .processors import DataProcessor
from .calculators import MetricsCalculator

__all__ = [
    'IDataLoader',
    'IDataProcessor',
    'IMetricsCalculator',
    'IAPIClient',
    'IConfiguration',
    'DataIntegrationError',
    'DataLoadError',
    'DataProcessError',
    'APIClientError',
    'ConfigurationError',
    'AppConfig',
    'DataConfig',
    'APIConfig',
    'APIClient',
    'DataProcessor',
    'MetricsCalculator',
]
