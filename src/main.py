"""Main entry point for running the pipeline."""
import sys
import os
from pathlib import Path

# Set UTF-8 encoding for Windows console output
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):
        os.environ['PYTHONIOENCODING'] = 'utf-8'

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
from src.core.config import AppConfig
from src.core.logger import setup_logging
from src.core.exceptions import DataIntegrationError, ConfigurationError
from src.core.clients import APIClient
from src.core.processors import DataProcessor
from src.core.calculators import MetricsCalculator
from src.di.container import DIContainer


def create_api_client(config: AppConfig):
    """Factory function to create API client."""
    if config.api.base_url and config.api.api_key:
        return APIClient(
            base_url=config.api.base_url,
            api_key=config.api.api_key,
            timeout=config.api.timeout
        )
    return None


def main():
    """Main entry point with dependency injection."""
    try:
        # Load and validate configuration
        config = AppConfig.from_yaml()
        config.validate()
        
        # Setup logging first
        logger = setup_logging(config.logging)
        
        # Run mode / environment are read from env vars to make local runs and CI runs explicit.
        run_mode = os.getenv('PIPELINE_MODE', 'local_demo')
        environment = os.getenv('ENVIRONMENT', 'dev')
        
        # Log application startup with configuration
        logger.info(
            "Application started",
            extra={
                'context': {
                    'application': 'Real Estate Heterogeneous Data Analytics',
                    'version': '2.0.0',
                    'mode': run_mode,
                    'environment': environment,
                    'config': {
                        'data_path': config.data.raw_path,
                        'output_path': config.data.output_path,
                        'api_base_url': config.api.base_url[:50] + '...' if len(config.api.base_url) > 50 else config.api.base_url
                    }
                }
            }
        )
        
        # Create dependencies
        api_client = create_api_client(config)
        data_processor = DataProcessor.from_config(config)
        metrics_calculator = MetricsCalculator()
        
        # Build dependency injection container
        container = DIContainer(config)
        
        # Build pipeline service with all dependencies
        pipeline_service = container.build_pipeline_service(
            api_client=api_client,
            data_processor=data_processor,
            metrics_calculator=metrics_calculator
        )
        
        # Execute pipeline
        result = pipeline_service.execute()
        
        # Log completion summary
        logger.info(
            "Application completed successfully",
            extra={
                'context': {
                    'final_data_shape': list(result.shape),
                    'output_file': f"{config.data.output_path}/final_dataframe.csv",
                    'total_records': len(result),
                    'total_columns': len(result.columns)
                }
            }
        )
        
        return result
        
    except ConfigurationError as e:
        logger = logging.getLogger('root')
        logger.error(
            f"Configuration Error: {e}",
            extra={'context': {'error_type': 'ConfigurationError'}},
            exc_info=True
        )
        sys.exit(1)
    except DataIntegrationError as e:
        logger = logging.getLogger('root')
        logger.error(
            f"Pipeline error: {e}",
            extra={'context': {'error_type': 'DataIntegrationError'}},
            exc_info=True
        )
        sys.exit(1)
    except Exception as e:
        logger = logging.getLogger('root')
        logger.critical(
            f"Unexpected Error: {e}",
            extra={'context': {'error_type': type(e).__name__}},
            exc_info=True
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
