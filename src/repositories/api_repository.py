"""
API-based data repository implementation.
"""
import pandas as pd
from typing import Optional
from .data_repository import DataRepository
from ..core.exceptions import DataLoadError, APIClientError
from ..core.interfaces import IAPIClient


class APIRepository(DataRepository):
    """Repository for API-based data sources."""
    
    def __init__(self, api_client: IAPIClient):
        """
        Initialize API repository.
        
        Args:
            api_client: API client instance
        """
        if api_client is None:
            raise ValueError("API client is required for APIRepository")
        self.api_client = api_client
    
    def load_sales_data(self, builder: str) -> pd.DataFrame:
        """Sales data is not available via API."""
        raise NotImplementedError("Sales data is loaded from files, not API")
    
    def load_targets_data(self, builder: str) -> pd.DataFrame:
        """Targets data is not available via API."""
        raise NotImplementedError("Targets data is loaded from files, not API")
    
    def load_crm_data(self, builder: str) -> pd.DataFrame:
        """
        Load CRM data from API.
        
        Args:
            builder: Builder identifier
            
        Returns:
            DataFrame with CRM data
            
        Raises:
            APIClientError: If API call fails
        """
        try:
            return self.api_client.get_crm_data(builder)
        except Exception as e:
            raise APIClientError(f"Failed to load CRM data for builder {builder}: {e}")
    
    def load_web_traffic_data(self, builder: str) -> pd.DataFrame:
        """
        Load web traffic data from API.
        
        Args:
            builder: Builder identifier
            
        Returns:
            DataFrame with web traffic data
            
        Raises:
            APIClientError: If API call fails
        """
        try:
            return self.api_client.get_web_traffic_data(builder)
        except Exception as e:
            raise APIClientError(f"Failed to load web traffic data for builder {builder}: {e}")
    
    def load_all_crm_data(self) -> list[pd.DataFrame]:
        """Load all CRM data."""
        return [
            self.load_crm_data('a'),
            self.load_crm_data('b')
        ]
    
    def load_all_web_traffic_data(self) -> list[pd.DataFrame]:
        """Load all web traffic data."""
        return [
            self.load_web_traffic_data('a'),
            self.load_web_traffic_data('b')
        ]
