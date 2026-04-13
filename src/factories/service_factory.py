"""
Factory for creating service instances.
"""
from typing import Optional
from pathlib import Path

from ..services import DataService, MetricsService, PipelineService
from ..repositories import FileRepository, APIRepository
from ..core.config import AppConfig
from ..core.interfaces import IDataProcessor, IMetricsCalculator


class ServiceFactory:
    """Factory for creating service instances."""
    
    @staticmethod
    def create_data_service(
        file_repository: FileRepository,
        api_repository: Optional[APIRepository],
        data_processor: IDataProcessor,
        processed_path: Optional[Path] = None
    ) -> DataService:
        """
        Create data service instance.
        
        Args:
            file_repository: File repository instance
            api_repository: API repository instance (optional)
            data_processor: Data processor instance
            processed_path: Path to Silver layer (processed data) directory
            
        Returns:
            DataService instance
        """
        return DataService(file_repository, api_repository, data_processor, processed_path)
    
    @staticmethod
    def create_metrics_service(
        metrics_calculator: IMetricsCalculator
    ) -> MetricsService:
        """
        Create metrics service instance.
        
        Args:
            metrics_calculator: Metrics calculator instance
            
        Returns:
            MetricsService instance
        """
        return MetricsService(metrics_calculator)
    
    @staticmethod
    def create_pipeline_service(
        data_service: DataService,
        metrics_service: MetricsService,
        config: AppConfig
    ) -> PipelineService:
        """
        Create pipeline service instance.
        
        Args:
            data_service: Data service instance
            metrics_service: Metrics service instance
            config: Application configuration
            
        Returns:
            PipelineService instance
        """
        return PipelineService(data_service, metrics_service, config)
