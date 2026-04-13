"""
Data service for business logic related to data operations.
"""
import logging
import pandas as pd
from pathlib import Path
from typing import List, Optional
from ..core.interfaces import IDataProcessor
from ..core.exceptions import DataProcessError
from ..core.pipeline_reporter import dataframe_snapshot, log_internal_transition
from ..repositories import FileRepository, APIRepository

_logger = logging.getLogger(__name__)


class DataService:
    """Service for data loading and processing operations."""
    
    def __init__(
        self,
        file_repository: FileRepository,
        api_repository: Optional[APIRepository],
        data_processor: IDataProcessor,
        processed_path: Optional[Path] = None
    ):
        """
        Initialize data service.
        
        Args:
            file_repository: File-based data repository
            api_repository: API-based data repository (optional)
            data_processor: Data processor instance
            processed_path: Path to Silver layer (processed data) directory
        """
        self.file_repository = file_repository
        self.api_repository = api_repository
        self.data_processor = data_processor
        self.processed_path = processed_path
        
        # Create processed directory if path is provided
        if self.processed_path:
            self.processed_path.mkdir(parents=True, exist_ok=True)
    
    def _save_to_silver_layer(self, df: pd.DataFrame, filename: str) -> None:
        """
        Save DataFrame to Silver layer (processed data zone).
        
        Args:
            df: DataFrame to save
            filename: Output filename (e.g., 'sales_processed.csv')
        """
        if not self.processed_path or df.empty:
            return
        
        try:
            output_file = self.processed_path / filename
            df.to_csv(output_file, index=False)
            _logger.info(
                f"Silver layer output saved: {filename}",
                extra={
                    'context': {
                        'layer': 'silver',
                        'filename': filename,
                        'records': len(df),
                        'columns': len(df.columns),
                        'path': str(output_file)
                    }
                }
            )
        except Exception as e:
            _logger.warning(
                f"Failed to save Silver layer output {filename}: {e}",
                extra={'context': {'layer': 'silver', 'filename': filename, 'error': str(e)}}
            )
    
    def load_and_process_sales_data(self) -> pd.DataFrame:
        """
        Load and process all sales data.
        
        Returns:
            Processed sales DataFrame
            
        Raises:
            DataProcessError: If processing fails
        """
        try:
            sales_list = self.file_repository.load_all_sales_data()
            merged = self.data_processor.merge_dataframes(sales_list)
            snap_m = dataframe_snapshot(merged, "sales_merged")
            cleaned = self.data_processor.clean_data(merged)
            snap_c = dataframe_snapshot(cleaned, "sales_cleaned")
            log_internal_transition(_logger, "sales", "merge → clean", snap_m, snap_c)
            out = self.data_processor.process_sales_data(cleaned)
            snap_o = dataframe_snapshot(out, "sales_final")
            log_internal_transition(_logger, "sales", "clean → process_sales_data", snap_c, snap_o)
            
            # Save to Silver layer (processed data zone)
            self._save_to_silver_layer(out, "sales_processed.csv")
            
            return out
        except Exception as e:
            raise DataProcessError(f"Failed to load and process sales data: {e}")
    
    def load_and_process_targets_data(self) -> pd.DataFrame:
        """
        Load and process all targets data.
        
        Returns:
            Processed targets DataFrame
            
        Raises:
            DataProcessError: If processing fails
        """
        try:
            targets_list = self.file_repository.load_all_targets_data()
            merged = self.data_processor.merge_dataframes(targets_list)
            snap_m = dataframe_snapshot(merged, "targets_merged")
            cleaned = self.data_processor.clean_data(merged)
            snap_c = dataframe_snapshot(cleaned, "targets_cleaned")
            log_internal_transition(_logger, "targets", "merge → clean", snap_m, snap_c)
            out = self.data_processor.process_targets_data(cleaned)
            snap_o = dataframe_snapshot(out, "targets_final")
            log_internal_transition(_logger, "targets", "clean → process_targets_data", snap_c, snap_o)
            
            # Save to Silver layer (processed data zone)
            self._save_to_silver_layer(out, "targets_processed.csv")
            
            return out
        except Exception as e:
            raise DataProcessError(f"Failed to load and process targets data: {e}")
    
    def load_and_process_crm_data(self) -> pd.DataFrame:
        """
        Load and process CRM data from API.
        
        Returns:
            Processed CRM DataFrame
            
        Raises:
            DataProcessError: If API is not configured, returns no data, or processing fails
        """
        if not self.api_repository:
            raise DataProcessError(
                "Cannot load CRM data: API repository is not configured",
                operation="load_and_process_crm_data",
            )

        logger = logging.getLogger(__name__)
        try:
            crm_list = self.api_repository.load_all_crm_data()
            if not crm_list:
                raise DataProcessError(
                    "CRM API returned no datasets (empty list)",
                    operation="load_and_process_crm_data",
                )

            total_raw = sum(len(df) for df in crm_list)
            logger.info(
                f"CRM data loaded: {len(crm_list)} builders, {total_raw} total records",
                extra={'context': {'data_type': 'crm', 'builders': len(crm_list), 'total_raw_records': total_raw}}
            )

            merged = self.data_processor.merge_dataframes(crm_list)
            if merged.empty:
                raise DataProcessError(
                    "CRM API returned no records (merged result is empty)",
                    operation="load_and_process_crm_data",
                )

            logger.info(
                f"CRM data merged: {len(merged)} records",
                extra={'context': {'data_type': 'crm', 'merged_records': len(merged)}}
            )

            processed = self.data_processor.process_crm_data(merged)

            logger.info(
                f"CRM data processed: {len(processed)} records after processing",
                extra={'context': {'data_type': 'crm', 'processed_records': len(processed)}}
            )

            # Save to Silver layer (processed data zone)
            self._save_to_silver_layer(processed, "crm_processed.csv")

            return processed
        except DataProcessError:
            raise
        except Exception as e:
            raise DataProcessError(
                f"Failed to load and process CRM data: {e}",
                operation="load_and_process_crm_data",
            ) from e
    
    def load_and_process_web_traffic_data(self) -> pd.DataFrame:
        """
        Load and process web traffic data from API.
        
        Returns:
            Processed web traffic DataFrame
            
        Raises:
            DataProcessError: If API is not configured, returns no data, or processing fails
        """
        if not self.api_repository:
            raise DataProcessError(
                "Cannot load web traffic data: API repository is not configured",
                operation="load_and_process_web_traffic_data",
            )

        try:
            traffic_list = self.api_repository.load_all_web_traffic_data()
            if not traffic_list:
                raise DataProcessError(
                    "Web traffic API returned no datasets (empty list)",
                    operation="load_and_process_web_traffic_data",
                )

            merged = self.data_processor.merge_dataframes(traffic_list)
            if merged.empty:
                raise DataProcessError(
                    "Web traffic API returned no records (merged result is empty)",
                    operation="load_and_process_web_traffic_data",
                )

            processed = self.data_processor.process_web_traffic_data(merged)

            # Save to Silver layer (processed data zone)
            self._save_to_silver_layer(processed, "web_traffic_processed.csv")

            return processed
        except DataProcessError:
            raise
        except Exception as e:
            raise DataProcessError(
                f"Failed to load and process web traffic data: {e}",
                operation="load_and_process_web_traffic_data",
            ) from e
