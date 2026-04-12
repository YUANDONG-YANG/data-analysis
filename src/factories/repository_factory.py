"""
Factory for creating repository instances.
"""
from pathlib import Path
from typing import Optional

from ..repositories import FileRepository, APIRepository
from ..core.config import AppConfig
from ..core.interfaces import IAPIClient
from ..core.exceptions import ConfigurationError


class RepositoryFactory:
    """Factory for creating repository instances."""
    
    @staticmethod
    def create_file_repository(config: AppConfig) -> FileRepository:
        """
        Create file repository instance.
        
        Args:
            config: Application configuration
            
        Returns:
            FileRepository instance
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        raw_path = config.data.get_raw_path(config.project_root)
        return FileRepository(raw_path)
    
    @staticmethod
    def create_api_repository(
        config: AppConfig,
        api_client: Optional[IAPIClient]
    ) -> Optional[APIRepository]:
        """
        Create API repository instance.
        
        Args:
            config: Application configuration
            api_client: API client instance (optional)
            
        Returns:
            APIRepository instance or None if API client not available
        """
        if api_client is None:
            return None
        
        return APIRepository(api_client)
