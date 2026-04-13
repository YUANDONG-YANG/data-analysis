"""
Pipeline service orchestrating the entire data processing workflow.
"""
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
import time
import os
import hashlib
from datetime import datetime

from .data_service import DataService
from .metrics_service import MetricsService
from ..core.config import AppConfig
from ..core.exceptions import DataIntegrationError
from ..core.pipeline_reporter import (
    dataframe_snapshot,
    dataframe_to_preview_dict,
    input_bundle_snapshot,
    log_step_compare,
    write_pipeline_analysis_html,
    write_pipeline_runtime_status_json,
    write_pipeline_steps_json,
)
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
    
    def _clean_gold_layer(self) -> None:
        """
        Clean all files in the Gold layer (output directory) before starting pipeline.
        
        This ensures a fresh start for each pipeline run and prevents stale data.
        """
        try:
            if not self.output_path.exists():
                self.logger.info(
                    "Gold layer directory does not exist, skipping cleanup",
                    extra={'context': {'output_path': str(self.output_path)}}
                )
                return
            
            cleaned_files = []
            for file_path in self.output_path.iterdir():
                if file_path.is_file():
                    try:
                        file_path.unlink()
                        cleaned_files.append(file_path.name)
                    except Exception as e:
                        self.logger.warning(
                            f"Failed to delete file {file_path.name}: {e}",
                            extra={'context': {'file': str(file_path), 'error': str(e)}}
                        )
            
            if cleaned_files:
                self.logger.info(
                    f"Cleaned {len(cleaned_files)} file(s) from Gold layer",
                    extra={
                        'context': {
                            'output_path': str(self.output_path),
                            'cleaned_files': cleaned_files,
                            'count': len(cleaned_files)
                        }
                    }
                )
            else:
                self.logger.info(
                    "Gold layer is already clean (no files to remove)",
                    extra={'context': {'output_path': str(self.output_path)}}
                )
                
        except Exception as e:
            self.logger.warning(
                f"Error during Gold layer cleanup: {e}",
                extra={'context': {'output_path': str(self.output_path), 'error': str(e)}}
            )
    
    def execute(self) -> pd.DataFrame:
        """
        Execute the complete data integration pipeline.
        
        Returns:
            Final metrics DataFrame
            
        Raises:
            DataIntegrationError: If pipeline execution fails
        """
        pipeline_start_time = time.time()
        step_entries: List[Dict[str, Any]] = []
        empty_before = dataframe_snapshot(pd.DataFrame(), "pipeline_empty")
        runtime_started_at = datetime.now().isoformat(timespec="seconds")

        def persist_runtime_status(
            status: str,
            current_step: Optional[str] = None,
            current_title: Optional[str] = None,
            total_seconds: Optional[float] = None,
            finished_at: Optional[str] = None,
            output_csv: Optional[str] = None,
            output_checksum_md5: Optional[str] = None,
            quality_report: Optional[Dict[str, Any]] = None,
            error: Optional[Dict[str, Any]] = None,
        ) -> None:
            try:
                write_pipeline_runtime_status_json(
                    self.output_path,
                    self.pipeline_id,
                    self.run_mode,
                    self.environment,
                    status,
                    runtime_started_at,
                    step_entries,
                    current_step=current_step,
                    current_title=current_title,
                    total_seconds=total_seconds,
                    finished_at=finished_at,
                    output_csv=output_csv,
                    output_checksum_md5=output_checksum_md5,
                    quality_report=quality_report,
                    error=error,
                )
            except OSError as exc:
                self.logger.warning(
                    f"Could not write pipeline runtime status JSON: {exc}",
                    extra={'context': {'pipeline_id': self.pipeline_id, 'step': 'pipeline_runtime_status_error'}},
                )

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
            
            # Clean Gold layer before starting
            self._clean_gold_layer()
            
            persist_runtime_status("starting")
            
            # Step 1: Load and process sales data
            t_step = time.time()
            persist_runtime_status("running", "1/6", "Load and process sales")
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
            after1 = dataframe_snapshot(sales_df, "sales_processed")
            dur1 = time.time() - t_step
            log_step_compare(
                self.logger, self.pipeline_id, "1/6", "Load and process sales",
                empty_before, after1, dur1,
            )
            step_entries.append({
                "step": "1/6",
                "title": "Load and process sales",
                "before": empty_before,
                "after": after1,
                "duration_sec": dur1,
                "delta_display": f"+{after1['rows']} rows (from empty pipeline)",
                "output_preview": dataframe_to_preview_dict(sales_df, 15),
            })
            persist_runtime_status("running", "1/6", "Load and process sales")

            # Step 2: Load and process targets data
            t_step = time.time()
            persist_runtime_status("running", "2/6", "Load and process targets")
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
            before2 = dataframe_snapshot(sales_df, "context_after_step1_sales")
            after2 = dataframe_snapshot(targets_df, "targets_processed")
            dur2 = time.time() - t_step
            log_step_compare(self.logger, self.pipeline_id, "2/6", "Load and process targets", before2, after2, dur2)
            step_entries.append({
                "step": "2/6",
                "title": "Load and process targets",
                "before": before2,
                "after": after2,
                "duration_sec": dur2,
                "delta_display": f"targets={after2['rows']} rows (sales still {before2['rows']} rows)",
                "output_preview": dataframe_to_preview_dict(targets_df, 15),
            })
            persist_runtime_status("running", "2/6", "Load and process targets")

            # Step 3: Load and process CRM data
            t_step = time.time()
            persist_runtime_status("running", "3/6", "Load and process CRM")
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
            before3 = dataframe_snapshot(targets_df, "context_after_step2_targets")
            after3 = dataframe_snapshot(crm_df, "crm_processed")
            dur3 = time.time() - t_step
            log_step_compare(self.logger, self.pipeline_id, "3/6", "Load and process CRM", before3, after3, dur3)
            step_entries.append({
                "step": "3/6",
                "title": "Load and process CRM",
                "before": before3,
                "after": after3,
                "duration_sec": dur3,
                "delta_display": f"crm={after3['rows']} rows (targets context {before3['rows']} rows)",
                "output_preview": dataframe_to_preview_dict(crm_df, 15),
            })
            persist_runtime_status("running", "3/6", "Load and process CRM")

            # Step 4: Load and process web traffic data
            t_step = time.time()
            persist_runtime_status("running", "4/6", "Load and process web traffic")
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
            before4 = dataframe_snapshot(crm_df, "context_after_step3_crm")
            after4 = dataframe_snapshot(web_traffic_df, "web_traffic_processed")
            dur4 = time.time() - t_step
            log_step_compare(self.logger, self.pipeline_id, "4/6", "Load and process web traffic", before4, after4, dur4)
            step_entries.append({
                "step": "4/6",
                "title": "Load and process web traffic",
                "before": before4,
                "after": after4,
                "duration_sec": dur4,
                "delta_display": f"web_traffic={after4['rows']} rows (crm context {before4['rows']} rows)",
                "output_preview": dataframe_to_preview_dict(web_traffic_df, 15),
            })
            persist_runtime_status("running", "4/6", "Load and process web traffic")

            # Step 5: Calculate metrics
            t_step = time.time()
            persist_runtime_status("running", "5/6", "Calculate metrics")
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
            bundle_before = input_bundle_snapshot(sales_df, targets_df, crm_df, web_traffic_df)
            after5 = dataframe_snapshot(metrics_df, "metrics_calculated")
            dur5 = time.time() - t_step
            log_step_compare(self.logger, self.pipeline_id, "5/6", "Calculate metrics", bundle_before, after5, dur5)
            step_entries.append({
                "step": "5/6",
                "title": "Calculate metrics (join inputs → metrics)",
                "before": bundle_before,
                "after": after5,
                "duration_sec": dur5,
                "delta_display": f"Σ_input_rows={bundle_before['sum_rows']} → metrics_rows={after5['rows']}",
                "output_preview": dataframe_to_preview_dict(metrics_df, 15),
                "conversion_stats": conversion_stats,
            })
            persist_runtime_status("running", "5/6", "Calculate metrics")

            # Step 6: Save results
            t_step = time.time()
            before6 = dataframe_snapshot(metrics_df, "metrics_before_save")
            persist_runtime_status("running", "6/6", "Save results")
            with self.perf_logger.time_operation("save_results"):
                self.logger.info(
                    "Step 6/6: Saving results",
                    extra={'context': {'pipeline_id': self.pipeline_id, 'step': '6/6', 'step_name': 'save_results'}}
                )
                save_meta = self._save_results(metrics_df)
            metrics_df = save_meta["metrics_df"]
            dur6 = time.time() - t_step
            after6 = dict(dataframe_snapshot(metrics_df, "metrics_saved_csv"))
            after6["saved_file"] = save_meta["filename"]
            after6["output_checksum_md5"] = save_meta["checksum"]
            log_step_compare(self.logger, self.pipeline_id, "6/6", "Save results (CSV + report)", before6, after6, dur6)
            step_entries.append({
                "step": "6/6",
                "title": "Save results (sorted CSV + HTML analysis)",
                "before": before6,
                "after": after6,
                "duration_sec": dur6,
                "delta_display": f"rows={after6['rows']} written; MD5={save_meta['checksum'][:12]}…",
                "output_preview": dataframe_to_preview_dict(metrics_df, 15),
            })
            persist_runtime_status("running", "6/6", "Save results")

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

            try:
                report_path = write_pipeline_analysis_html(
                    self.output_path,
                    self.pipeline_id,
                    self.run_mode,
                    self.environment,
                    step_entries,
                    metrics_df,
                    save_meta["filename"],
                    save_meta["checksum"],
                    quality_report=quality_report,
                    total_seconds=total_time,
                    preview_rows=40,
                )
                self.logger.info(
                    f"Pipeline analysis HTML written: {report_path.name}",
                    extra={
                        'context': {
                            'pipeline_id': self.pipeline_id,
                            'step': 'analysis_html',
                            'path': str(report_path),
                        }
                    },
                )
            except OSError as exc:
                self.logger.warning(
                    f"Could not write pipeline analysis HTML: {exc}",
                    extra={'context': {'pipeline_id': self.pipeline_id, 'step': 'analysis_html_error'}},
                )

            try:
                json_path = write_pipeline_steps_json(
                    self.output_path,
                    self.pipeline_id,
                    self.run_mode,
                    self.environment,
                    total_time,
                    step_entries,
                    save_meta["filename"],
                    save_meta["checksum"],
                    quality_report=quality_report,
                )
                self.logger.info(
                    f"Pipeline steps JSON written: {json_path.name}",
                    extra={
                        'context': {
                            'pipeline_id': self.pipeline_id,
                            'step': 'pipeline_steps_json',
                            'path': str(json_path),
                        }
                    },
                )
            except OSError as exc:
                self.logger.warning(
                    f"Could not write pipeline steps JSON: {exc}",
                    extra={'context': {'pipeline_id': self.pipeline_id, 'step': 'pipeline_steps_json_error'}},
                )

            persist_runtime_status(
                "completed",
                "6/6",
                "Save results",
                total_seconds=total_time,
                finished_at=datetime.now().isoformat(timespec="seconds"),
                output_csv=save_meta["filename"],
                output_checksum_md5=save_meta["checksum"],
                quality_report=quality_report,
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
            persist_runtime_status(
                "failed",
                total_seconds=total_time,
                finished_at=datetime.now().isoformat(timespec="seconds"),
                error=error_dict,
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
            persist_runtime_status(
                "failed",
                total_seconds=total_time,
                finished_at=datetime.now().isoformat(timespec="seconds"),
                error=wrapped_error.to_dict(),
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
    
    def _save_results(self, metrics_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Save results to output file.

        Returns:
            Dict with sorted ``metrics_df``, CSV filename, MD5 checksum, and absolute output path.
        """
        df = metrics_df
        # Ensure proper sorting before saving: month asc, builder asc, community_name asc
        if not df.empty:
            sort_columns = []
            for col in ['month', 'builder', 'community_name']:
                if col in df.columns:
                    sort_columns.append(col)

            if sort_columns:
                df = df.sort_values(sort_columns).reset_index(drop=True)

        output_file = self.output_path / "final_dataframe.csv"
        csv_content = df.to_csv(index=False)
        file_size = len(csv_content.encode('utf-8'))

        df.to_csv(output_file, index=False)

        schema = self._generate_output_schema(df)
        checksum = hashlib.md5(csv_content.encode('utf-8')).hexdigest()

        self.logger.info(
            f"Results saved successfully",
            extra={
                'context': {
                    'pipeline_id': self.pipeline_id,
                    'output_file': str(output_file),
                    'records_saved': len(df),
                    'columns_saved': len(df.columns),
                    'schema': schema,
                    'output_checksum': checksum
                },
                'performance': {
                    'file_size_bytes': file_size,
                    'file_size_kb': round(file_size / 1024, 2)
                }
            }
        )
        return {
            'metrics_df': df,
            'filename': 'final_dataframe.csv',
            'checksum': checksum,
            'output_file': str(output_file),
        }
    
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
