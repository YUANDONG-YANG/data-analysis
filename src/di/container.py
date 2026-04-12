"""
Dependency Injection container for managing object dependencies.
"""
from typing import Optional, Dict, Any, Callable
from ..core.config import AppConfig
from ..core.interfaces import IAPIClient, IDataProcessor, IMetricsCalculator
from ..repositories import FileRepository, APIRepository
from ..services import DataService, MetricsService, PipelineService
from ..factories import RepositoryFactory, ServiceFactory


class DIContainer:
    """Dependency Injection container."""
    
    def __init__(self, config: AppConfig):
        """
        Initialize DI container.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self._instances: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
    
    def register_singleton(self, name: str, instance: Any) -> None:
        """Register a singleton instance."""
        self._instances[name] = instance
    
    def register_factory(self, name: str, factory: Callable) -> None:
        """Register a factory function."""
        self._factories[name] = factory
    
    def get(self, name: str) -> Any:
        """Get instance by name."""
        if name in self._instances:
            return self._instances[name]
        
        if name in self._factories:
            instance = self._factories[name]()
            self._instances[name] = instance
            return instance
        
        raise ValueError(f"Unknown dependency: {name}")
    
    def build_pipeline_service(
        self,
        api_client: Optional[IAPIClient],
        data_processor: IDataProcessor,
        metrics_calculator: IMetricsCalculator
    ) -> PipelineService:
        """
        Build complete pipeline service with all dependencies.
        
        Args:
            api_client: API client instance
            data_processor: Data processor instance
            metrics_calculator: Metrics calculator instance
            
        Returns:
            Configured PipelineService instance
        """
        # Create repositories
        file_repository = RepositoryFactory.create_file_repository(self.config)
        api_repository = RepositoryFactory.create_api_repository(self.config, api_client)
        
        # Create services
        data_service = ServiceFactory.create_data_service(
            file_repository,
            api_repository,
            data_processor
        )
        
        metrics_service = ServiceFactory.create_metrics_service(metrics_calculator)
        
        # Create pipeline service
        pipeline_service = ServiceFactory.create_pipeline_service(
            data_service,
            metrics_service,
            self.config
        )
        
        return pipeline_service
