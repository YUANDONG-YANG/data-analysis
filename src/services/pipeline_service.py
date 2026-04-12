"""
Pipeline service orchestrating the entire data processing workflow.
"""
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any
import logging
import time
import os
import hashlib

from .data_service import DataService
from .metrics_service import MetricsService
from ..core.config import AppConfig
from ..core.exceptions import DataIntegrationError
from ..core.structured_logger import PerformanceLogger


class PipelineService:
    """Service orchestrating the data integration pipeline."""
    
    def __init__(
        self,
        data_service: DataService,
        metrics_service: MetricsService,
        config: AppConfig
    ):
        """
        Initialize pipeline service.
        
        Args:
            data_service: Data service instance
            metrics_service: Metrics service instance
            config: Application configuration
        """
        self.data_service = data_service
        self.metrics_service = metrics_service
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.perf_logger = PerformanceLogger(self.logger)
        self.output_path = config.data.get_output_path(config.project_root)
        self.pipeline_id = str(time.time_ns())[-12:]  # Unique pipeline execution ID
        
        # Run mode / environment help identify how/where a run happened (local, CI, etc.).
        self.run_mode = os.getenv('PIPELINE_MODE', 'local_demo')
        self.environment = os.getenv('ENVIRONMENT', 'dev')
    
    def execute(self) -> pd.DataFrame:
        """
        Execute the complete data integration pipeline.
        
        Returns:
            Final metrics DataFrame
            
        Raises:
            DataIntegrationError: If pipeline execution fails
        """
        pipeline_start_time = time.time()
        
        try:
            self.logger.info(
                "Starting data integration pipeline",
                extra={
                    'context': {
                        'pipeline_id': self.pipeline_id,
                        'step': 'initialization',
                        'mode': self.run_mode,
                        'environment': self.environment
                    }
                }
            )
            
            # Step 1: Load and process sales data
            with self.perf_logger.time_operation("load_and_process_sales_data"):
                self.logger.info(
                    "Step 1/6: Loading and processing sales data",
                    extra={'context': {'pipeline_id': self.pipeline_id, 'step': '1/6', 'step_name': 'sales_data'}}
                )
                sales_df = self.data_service.load_and_process_sales_data()
                # Calculate sales month range
                if 'year_month' in sales_df.columns:
                    sales_month_range = {
                        'min': sales_df['year_month'].min(),
                        'max': sales_df['year_month'].max()
                    }
                else:
                    sales_month_range = {'min': None, 'max': None}
                
                self.logger.info(
                    f"Sales data processed: {len(sales_df)} raw records",
                    extra={
                        'context': {
                            'pipeline_id': self.pipeline_id,
                            'step': '1/6',
                            'raw_records': len(sales_df),
                            'data_type': 'sales',
                            'observed_sales_month_range': sales_month_range
                        }
                    }
                )
            
            # Step 2: Load and process targets data
            with self.perf_logger.time_operation("load_and_process_targets_data"):
                self.logger.info(
                    "Step 2/6: Loading and processing targets data",
                    extra={'context': {'pipeline_id': self.pipeline_id, 'step': '2/6', 'step_name': 'targets_data'}}
                )
                targets_df = self.data_service.load_and_process_targets_data()
                # Calculate target month range
                month_col = 'year_month' if 'year_month' in targets_df.columns else 'month'
                if month_col in targets_df.columns:
                    target_month_range = {
                        'min': targets_df[month_col].min(),
                        'max': targets_df[month_col].max()
                    }
                else:
                    target_month_range = {'min': None, 'max': None}
                
                self.logger.info(
                    f"Targets data processed: {len(targets_df)} raw records",
                    extra={
                        'context': {
                            'pipeline_id': self.pipeline_id,
                            'step': '2/6',
                            'raw_records': len(targets_df),
                            'data_type': 'targets',
                            'target_month_range': target_month_range
                        }
                    }
                )
            
            # Step 3: Load and process CRM data
            with self.perf_logger.time_operation("load_and_process_crm_data"):
                self.logger.info(
                    "Step 3/6: Loading and processing CRM data",
                    extra={'context': {'pipeline_id': self.pipeline_id, 'step': '3/6', 'step_name': 'crm_data'}}
                )
                crm_df = self.data_service.load_and_process_crm_data()
                self.logger.info(
                    f"CRM data processed: {len(crm_df)} raw records",
                    extra={
                        'context': {
                            'pipeline_id': self.pipeline_id,
                            'step': '3/6',
                            'raw_records': len(crm_df),
                            'data_type': 'crm'
                        }
                    }
                )
            
            # Step 4: Load and process web traffic data
            with self.perf_logger.time_operation("load_and_process_web_traffic_data"):
                self.logger.info(
                    "Step 4/6: Loading and processing web traffic data",
                    extra={'context': {'pipeline_id': self.pipeline_id, 'step': '4/6', 'step_name': 'web_traffic_data'}}
                )
                web_traffic_df = self.data_service.load_and_process_web_traffic_data()
                self.logger.info(
                    f"Web traffic data processed: {len(web_traffic_df)} raw records",
                    extra={
                        'context': {
                            'pipeline_id': self.pipeline_id,
                            'step': '4/6',
                            'raw_records': len(web_traffic_df),
                            'data_type': 'web_traffic'
                        }
                    }
                )
            
            # Step 5: Calculate metrics
            with self.perf_logger.time_operation("calculate_metrics"):
                self.logger.info(
                    "Step 5/6: Calculating metrics",
                    extra={'context': {'pipeline_id': self.pipeline_id, 'step': '5/6', 'step_name': 'metrics_calculation'}}
                )
                metrics_df = self.metrics_service.calculate_metrics(
                    sales_df,
                    targets_df,
                    crm_df,
                    web_traffic_df
                )
                
                # Calculate conversion rate statistics for logging
                conversion_stats = self._calculate_conversion_rate_stats(metrics_df)
                
                # Define metrics calculated
                metrics_calculated = [
                    'actual_sales',
                    'target_sales',
                    'variance',
                    'crm_leads',
                    'web_traffic',
                    'estimated_revenue',
                    'achievement_rate',
                    'estimated_avg_sale_price',
                    'conversion_rate',
                    'traffic_to_sales_rate'
                ]
                
                self.logger.info(
                    f"Metrics calculated: {len(metrics_df)} final records",
                    extra={
                        'context': {
                            'pipeline_id': self.pipeline_id,
                            'step': '5/6',
                            'final_records': len(metrics_df),
                            'data_type': 'metrics',
                            'metrics_calculated': metrics_calculated,
                            'conversion_rate_stats': conversion_stats
                        }
                    }
                )
            
            # Step 6: Save results
            with self.perf_logger.time_operation("save_results"):
                self.logger.info(
                    "Step 6/6: Saving results",
                    extra={'context': {'pipeline_id': self.pipeline_id, 'step': '6/6', 'step_name': 'save_results'}}
                )
                self._save_results(metrics_df)
            
            # Generate quality report
            quality_report = self.metrics_service.generate_quality_report(metrics_df, targets_df)
            total_time = time.time() - pipeline_start_time
            
            # Distinguish month ranges so planning months don't get confused with observed actuals.
            observed_sales_month_range = quality_report.get('actual_data_range', {})
            target_month_range = quality_report.get('target_month_range', {})
            final_output_month_range = quality_report.get('month_range', {})
            
            # Calculate data latency metrics (for modern analytics pipeline)
            latency_metrics = self._calculate_data_latency(metrics_df, observed_sales_month_range)
            
            # Generate business summary for analytics stakeholders
            business_summary = self._generate_business_summary(metrics_df, quality_report)
            
            self.logger.info(
                "Pipeline execution completed successfully",
                extra={
                    'context': {
                        'pipeline_id': self.pipeline_id,
                        'step': 'completion',
                        'mode': self.run_mode,
                        'environment': self.environment,
                        'total_records': len(metrics_df),
                        'communities': quality_report['communities'],
                        'observed_sales_month_range': observed_sales_month_range,  # Range with actual sales data
                        'target_month_range': target_month_range,  # Range of target data
                        'final_output_month_range': final_output_month_range,  # Full output range including planning
                        'data_latency': latency_metrics,
                        'business_summary': business_summary
                    },
                    'performance': {
                        'total_execution_time_seconds': round(total_time, 3),
                        'records_per_second': round(len(metrics_df) / total_time, 2) if total_time > 0 else 0
                    }
                }
            )
            
            # Log quality report details
            self.logger.debug(
                "Data quality report",
                extra={
                    'context': {'pipeline_id': self.pipeline_id, 'report_type': 'quality'},
                    'quality_metrics': quality_report
                }
            )
            
            return metrics_df
            
        except DataIntegrationError as e:
            # Re-raise with enhanced context
            total_time = time.time() - pipeline_start_time
            error_dict = e.to_dict() if hasattr(e, 'to_dict') else {
                'error_type': type(e).__name__,
                'message': str(e)
            }
            
            self.logger.error(
                f"Pipeline execution failed: {e}",
                extra={
                    'context': {
                        'pipeline_id': self.pipeline_id,
                        'step': 'error',
                        'mode': self.run_mode,
                        'environment': self.environment,
                        **error_dict
                    },
                    'performance': {
                        'failed_after_seconds': round(total_time, 3)
                    }
                },
                exc_info=True
            )
            raise
            
        except Exception as e:
            # Wrap unexpected exceptions
            total_time = time.time() - pipeline_start_time
            wrapped_error = DataIntegrationError(
                f"Pipeline execution failed: {e}",
                error_code='PIPELINE_EXECUTION_ERROR',
                context={
                    'pipeline_id': self.pipeline_id,
                    'original_error_type': type(e).__name__
                }
            )
            
            self.logger.error(
                f"Pipeline execution failed with unexpected error: {e}",
                extra={
                    'context': {
                        'pipeline_id': self.pipeline_id,
                        'step': 'error',
                        'mode': self.run_mode,
                        'environment': self.environment,
                        **wrapped_error.to_dict()
                    },
                    'performance': {
                        'failed_after_seconds': round(total_time, 3)
                    }
                },
                exc_info=True
            )
            raise wrapped_error
    
    def _calculate_conversion_rate_stats(self, metrics_df: pd.DataFrame) -> dict:
        """
        Calculate conversion rate statistics for logging.
        
        Args:
            metrics_df: Metrics DataFrame
            
        Returns:
            Dictionary with conversion rate statistics
        """
        if 'conversion_rate' not in metrics_df.columns:
            return {}
        
        zero_lead_count = len(metrics_df[metrics_df['crm_leads'] == 0]) if 'crm_leads' in metrics_df.columns else 0
        zero_sales_count = len(metrics_df[metrics_df['actual_sales'] == 0]) if 'actual_sales' in metrics_df.columns else 0
        zero_conversion_count = len(metrics_df[metrics_df['conversion_rate'] == 0])
        
        return {
            'zero_lead_months': zero_lead_count,
            'zero_sales_months': zero_sales_count,
            'zero_conversion_months': zero_conversion_count,
            'filled_with': 0,
            'note': 'conversion_rate = 0 when crm_leads = 0 or actual_sales = 0'
        }
    
    def _save_results(self, metrics_df: pd.DataFrame) -> None:
        """
        Save results to output file.
        
        Args:
            metrics_df: Metrics DataFrame to save
        """
        # Ensure proper sorting before saving: month asc, builder asc, community_name asc
        # Only sort if DataFrame is not empty and has required columns
        if not metrics_df.empty:
            sort_columns = []
            for col in ['month', 'builder', 'community_name']:
                if col in metrics_df.columns:
                    sort_columns.append(col)
            
            if sort_columns:
                metrics_df = metrics_df.sort_values(sort_columns).reset_index(drop=True)
        
        output_file = self.output_path / "final_dataframe.csv"
        csv_content = metrics_df.to_csv(index=False)
        file_size = len(csv_content.encode('utf-8'))
        
        metrics_df.to_csv(output_file, index=False)
        
        # Generate output schema (field names and types)
        schema = self._generate_output_schema(metrics_df)
        
        # Calculate checksum for data consistency verification
        checksum = hashlib.md5(csv_content.encode('utf-8')).hexdigest()
        
        self.logger.info(
            f"Results saved successfully",
            extra={
                'context': {
                    'pipeline_id': self.pipeline_id,
                    'output_file': str(output_file),
                    'records_saved': len(metrics_df),
                    'columns_saved': len(metrics_df.columns),
                    'schema': schema,
                    'output_checksum': checksum
                },
                'performance': {
                    'file_size_bytes': file_size,
                    'file_size_kb': round(file_size / 1024, 2)
                }
            }
        )
    
    def _generate_output_schema(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Generate output schema with field names and types.
        
        Args:
            df: DataFrame to generate schema for
            
        Returns:
            Dictionary mapping column names to their types
        """
        schema = {}
        for col in df.columns:
            dtype = str(df[col].dtype)
            # Map pandas dtypes to more readable types
            if dtype.startswith('int'):
                schema[col] = 'integer'
            elif dtype.startswith('float'):
                schema[col] = 'float'
            elif dtype.startswith('bool'):
                schema[col] = 'boolean'
            else:
                schema[col] = 'string'
        return schema
    
    def _calculate_data_latency(self, metrics_df: pd.DataFrame, observed_range: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate data latency metrics for modern analytics pipeline.
        
        Args:
            metrics_df: Metrics DataFrame
            observed_range: Dictionary with 'min' and 'max' keys for observed sales month range
            
        Returns:
            Dictionary with latency metrics
        """
        from datetime import datetime
        
        latency_metrics = {}
        
        if observed_range.get('max'):
            latest_sales_month = observed_range['max']
            latency_metrics['latest_sales_month'] = latest_sales_month
            
            # Calculate freshness lag (months from latest sales data to current date)
            try:
                latest_date = datetime.strptime(latest_sales_month, '%Y-%m')
                current_date = datetime.now()
                months_diff = (current_date.year - latest_date.year) * 12 + (current_date.month - latest_date.month)
                latency_metrics['data_freshness_lag_months'] = months_diff
            except (ValueError, TypeError):
                latency_metrics['data_freshness_lag_months'] = None
        
        return latency_metrics
    
    def _generate_business_summary(self, metrics_df: pd.DataFrame, quality_report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate business summary for analytics stakeholders.
        
        Args:
            metrics_df: Metrics DataFrame
            quality_report: Quality report dictionary
            
        Returns:
            Dictionary with business summary metrics
        """
        summary = {
            'communities': quality_report.get('communities', 0),
            'builders': metrics_df['builder'].nunique() if 'builder' in metrics_df.columns else 0
        }
        
        # Calculate month span
        if 'month' in metrics_df.columns:
            unique_months = metrics_df['month'].nunique()
            summary['months'] = unique_months
        elif 'year_month' in metrics_df.columns:
            unique_months = metrics_df['year_month'].nunique()
            summary['months'] = unique_months
        else:
            summary['months'] = None
        
        # Calculate average achievement rate
        if 'achievement_rate' in metrics_df.columns:
            # Only calculate for months with actual sales > 0
            sales_months = metrics_df[metrics_df['actual_sales'] > 0] if 'actual_sales' in metrics_df.columns else metrics_df
            if not sales_months.empty and 'achievement_rate' in sales_months.columns:
                avg_achievement = sales_months['achievement_rate'].mean()
                if not pd.isna(avg_achievement):
                    summary['avg_achievement_rate_percent'] = float(round(avg_achievement, 2))
                else:
                    summary['avg_achievement_rate_percent'] = None
            else:
                summary['avg_achievement_rate_percent'] = None
        else:
            summary['avg_achievement_rate_percent'] = None
        
        return summary
