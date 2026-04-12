"""
Interfaces and protocols used across the codebase.
Uses Protocol for structural subtyping (duck typing).
"""
from abc import ABC, abstractmethod
from typing import Protocol, List, Optional, Dict, Any
from pathlib import Path
import pandas as pd


class IDataLoader(Protocol):
    """Interface for data loading operations."""
    
    def load_sales_data(self, builder: str) -> pd.DataFrame:
        """Load sales data for a specific builder."""
        ...
    
    def load_targets_data(self, builder: str) -> pd.DataFrame:
        """Load targets data for a specific builder."""
        ...
    
    def load_crm_data(self, builder: str) -> pd.DataFrame:
        """Load CRM data for a specific builder."""
        ...
    
    def load_web_traffic_data(self, builder: str) -> pd.DataFrame:
        """Load web traffic data for a specific builder."""
        ...


class IDataProcessor(Protocol):
    """Interface for data processing operations."""
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate data."""
        ...
    
    def process_sales_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process sales data."""
        ...
    
    def process_targets_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process targets data."""
        ...
    
    def process_crm_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process CRM data."""
        ...
    
    def process_web_traffic_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process web traffic data."""
        ...
    
    def merge_dataframes(self, dataframes: List[pd.DataFrame], 
                        how: str = 'outer', on: Optional[str] = None) -> pd.DataFrame:
        """Merge multiple dataframes."""
        ...


class IMetricsCalculator(Protocol):
    """Interface for metrics calculation operations."""
    
    def calculate_monthly_community_metrics(
        self,
        sales_df: pd.DataFrame,
        targets_df: pd.DataFrame,
        crm_df: pd.DataFrame,
        web_traffic_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Calculate monthly community-level metrics."""
        ...


class IAPIClient(Protocol):
    """Interface for API client operations."""
    
    def get_crm_data(self, builder: str) -> pd.DataFrame:
        """Get CRM data from API."""
        ...
    
    def get_web_traffic_data(self, builder: str) -> pd.DataFrame:
        """Get web traffic data from API."""
        ...


class IConfiguration(ABC):
    """Abstract base class for configuration management."""
    
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """Validate configuration."""
        pass


class ILogger(Protocol):
    """Interface for logging operations."""
    
    def info(self, message: str) -> None:
        """Log info message."""
        ...
    
    def warning(self, message: str) -> None:
        """Log warning message."""
        ...
    
    def error(self, message: str) -> None:
        """Log error message."""
        ...
    
    def debug(self, message: str) -> None:
        """Log debug message."""
        ...
