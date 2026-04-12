"""
Metrics service for business logic related to metrics calculation.
"""
import pandas as pd
from typing import Optional
from ..core.interfaces import IMetricsCalculator
from ..core.exceptions import DataProcessError


class MetricsService:
    """Service for metrics calculation operations."""
    
    def __init__(self, metrics_calculator: IMetricsCalculator):
        """
        Initialize metrics service.
        
        Args:
            metrics_calculator: Metrics calculator instance
        """
        self.metrics_calculator = metrics_calculator
    
    def calculate_metrics(
        self,
        sales_df: pd.DataFrame,
        targets_df: pd.DataFrame,
        crm_df: pd.DataFrame,
        web_traffic_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate monthly community-level metrics.
        
        Args:
            sales_df: Processed sales data
            targets_df: Processed targets data
            crm_df: Processed CRM data
            web_traffic_df: Processed web traffic data
            
        Returns:
            DataFrame with calculated metrics
            
        Raises:
            DataProcessError: If calculation fails
        """
        try:
            return self.metrics_calculator.calculate_monthly_community_metrics(
                sales_df,
                targets_df,
                crm_df,
                web_traffic_df
            )
        except Exception as e:
            raise DataProcessError(f"Failed to calculate metrics: {e}")
    
    def generate_quality_report(self, metrics_df: pd.DataFrame, targets_df: Optional[pd.DataFrame] = None) -> dict:
        """
        Generate data quality report.
        
        Args:
            metrics_df: Metrics DataFrame
            targets_df: Optional targets DataFrame for calculating target month range
            
        Returns:
            Dictionary with quality metrics
        """
        month_col = 'month' if 'month' in metrics_df.columns else 'year_month'
        
        # Calculate month range for all data (includes future planning months)
        all_month_range = {
            'min': metrics_df[month_col].min(),
            'max': metrics_df[month_col].max()
        }
        
        # Calculate month range for actual sales data only (excludes future months with 0 sales)
        if 'actual_sales' in metrics_df.columns:
            actual_data_df = metrics_df[metrics_df['actual_sales'] > 0]
            if not actual_data_df.empty:
                actual_month_range = {
                    'min': actual_data_df[month_col].min(),
                    'max': actual_data_df[month_col].max()
                }
            else:
                actual_month_range = {'min': None, 'max': None}
        else:
            actual_month_range = {'min': None, 'max': None}
        
        # Calculate target month range if targets_df provided
        target_month_range = {'min': None, 'max': None}
        if targets_df is not None:
            target_month_col = 'year_month' if 'year_month' in targets_df.columns else 'month'
            if target_month_col in targets_df.columns:
                target_month_range = {
                    'min': targets_df[target_month_col].min(),
                    'max': targets_df[target_month_col].max()
                }
        
        return {
            'total_records': len(metrics_df),
            'communities': metrics_df['community_name'].nunique(),
            'month_range': all_month_range,  # Full range including future planning data
            'actual_data_range': actual_month_range,  # Range with actual sales data only
            'target_month_range': target_month_range,  # Range of target data
            'missing_values': metrics_df.isnull().sum().to_dict(),
            'data_types': metrics_df.dtypes.to_dict()
        }
