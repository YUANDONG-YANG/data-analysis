"""
Metrics calculation module for computing various business metrics.
"""
import pandas as pd
from typing import Optional


class MetricsCalculator:
    """Metrics calculator class for business metric calculations."""
    
    def __init__(self):
        """Initialize metrics calculator."""
        pass
    
    def calculate_monthly_community_metrics(
        self,
        sales_df: pd.DataFrame,
        targets_df: pd.DataFrame,
        crm_df: pd.DataFrame,
        web_traffic_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate monthly community-level metrics.
        
        Args:
            sales_df: Sales data DataFrame
            targets_df: Targets data DataFrame
            crm_df: CRM data DataFrame
            web_traffic_df: Web Traffic data DataFrame
            
        Returns:
            DataFrame containing all metrics
        """
        # Early return for empty input DataFrames
        if sales_df.empty and targets_df.empty:
            return pd.DataFrame(columns=[
                'month', 'community_name', 'builder', 'actual_sales', 'target_sales',
                'variance', 'crm_leads', 'web_traffic', 'estimated_revenue',
                'achievement_rate', 'estimated_avg_sale_price', 'conversion_rate',
                'traffic_to_sales_rate'
            ])
        
        # Check if sales_df has required columns
        if not sales_df.empty and 'year_month' not in sales_df.columns:
            if 'month' in sales_df.columns:
                sales_df = sales_df.copy()
                sales_df['year_month'] = sales_df['month']
            else:
                # If no month/year_month column, return empty result
                return pd.DataFrame(columns=[
                    'month', 'community_name', 'builder', 'actual_sales', 'target_sales',
                    'variance', 'crm_leads', 'web_traffic', 'estimated_revenue',
                    'achievement_rate', 'estimated_avg_sale_price', 'conversion_rate',
                    'traffic_to_sales_rate'
                ])
        
        # 1. Calculate actual sales (by community and month)
        if sales_df.empty:
            sales_agg = pd.DataFrame(columns=['year_month', 'community_name', 'builder', 'estimated_revenue', 'actual_sales_count'])
        else:
            sales_agg = sales_df.groupby(['year_month', 'community_name', 'builder']).agg({
            'total_sale_price': 'sum',
            'home_id': 'count'
        }).reset_index()
        sales_agg.columns = ['year_month', 'community_name', 'builder', 'estimated_revenue', 'actual_sales_count']
        
        # 2. Process targets data (by community and month)
        if targets_df.empty:
            targets_agg = pd.DataFrame(columns=['year_month', 'community_name', 'builder', 'target_sales'])
        else:
            # Ensure year_month column exists
            if 'year_month' not in targets_df.columns and 'month' in targets_df.columns:
                targets_df = targets_df.copy()
                targets_df['year_month'] = targets_df['month']
            
            if 'year_month' not in targets_df.columns:
                targets_agg = pd.DataFrame(columns=['year_month', 'community_name', 'builder', 'target_sales'])
            else:
                targets_agg = targets_df.groupby(['year_month', 'community_name', 'builder']).agg({
                    'target_sales': 'sum'
                }).reset_index()
                targets_agg = targets_agg[['year_month', 'community_name', 'builder', 'target_sales']]
        
        # 3. Calculate CRM lead count (by community and month)
        if not crm_df.empty and 'year_month' in crm_df.columns:
            # Ensure builder column exists, infer from data or use default if not present
            if 'builder' not in crm_df.columns:
                # Try to infer builder from other columns
                if 'builder_id' in crm_df.columns:
                    crm_df['builder'] = crm_df['builder_id'].str[-1].str.lower()
                else:
                    # If no builder information, set to empty string, will be handled later
                    crm_df['builder'] = ''
            
            group_cols = ['year_month', 'community_name']
            if 'builder' in crm_df.columns and crm_df['builder'].notna().any():
                group_cols.append('builder')
            
            crm_agg = crm_df.groupby(group_cols).size().reset_index(name='crm_lead_count')
            if 'builder' not in crm_agg.columns:
                crm_agg['builder'] = ''
        else:
            crm_agg = pd.DataFrame(columns=['year_month', 'community_name', 'builder', 'crm_lead_count'])
        
        # 4. Calculate Web Traffic (by community and month)
        if not web_traffic_df.empty and 'year_month' in web_traffic_df.columns:
            # Ensure builder column exists
            if 'builder' not in web_traffic_df.columns:
                if 'builder_id' in web_traffic_df.columns:
                    web_traffic_df['builder'] = web_traffic_df['builder_id'].str[-1].str.lower()
                else:
                    web_traffic_df['builder'] = ''
            
            # Try different traffic metric column names
            traffic_cols = ['sessions', 'visits', 'pageviews', 'users', 'traffic', 'count']
            traffic_col = None
            for col in traffic_cols:
                if col in web_traffic_df.columns:
                    traffic_col = col
                    break
            
            group_cols = ['year_month', 'community_name']
            if 'builder' in web_traffic_df.columns and web_traffic_df['builder'].notna().any():
                group_cols.append('builder')
            
            if traffic_col:
                web_traffic_agg = web_traffic_df.groupby(group_cols)[traffic_col].sum().reset_index()
                web_traffic_agg.columns = list(web_traffic_agg.columns[:-1]) + ['web_traffic']
            else:
                # If no traffic column found, count records
                web_traffic_agg = web_traffic_df.groupby(group_cols).size().reset_index(name='web_traffic')
            
            if 'builder' not in web_traffic_agg.columns:
                web_traffic_agg['builder'] = ''
        else:
            web_traffic_agg = pd.DataFrame(columns=['year_month', 'community_name', 'builder', 'web_traffic'])
        
        # 5. Merge all data
        # First merge sales and targets
        result = sales_agg.merge(
            targets_agg,
            on=['year_month', 'community_name', 'builder'],
            how='outer'
        )
        
        # Merge CRM data
        if not crm_agg.empty:
            result = result.merge(
                crm_agg,
                on=['year_month', 'community_name', 'builder'],
                how='left'
            )
        else:
            result['crm_lead_count'] = 0
        
        # Merge Web Traffic data
        if not web_traffic_agg.empty:
            result = result.merge(
                web_traffic_agg,
                on=['year_month', 'community_name', 'builder'],
                how='left'
            )
        else:
            result['web_traffic'] = 0
        
        # 6. Fill missing values
        result['estimated_revenue'] = result['estimated_revenue'].fillna(0)
        result['actual_sales_count'] = result['actual_sales_count'].fillna(0)
        result['target_sales'] = result['target_sales'].fillna(0)
        result['crm_lead_count'] = result['crm_lead_count'].fillna(0)
        result['web_traffic'] = result['web_traffic'].fillna(0)
        
        # 7. Calculate Variance (actual sales count - target sales count)
        result['variance'] = result['actual_sales_count'] - result['target_sales']
        
        # 8. Calculate additional metrics
        # Achievement rate
        result['achievement_rate'] = result.apply(
            lambda row: (row['actual_sales_count'] / row['target_sales'] * 100) 
            if row['target_sales'] > 0 else 0,
            axis=1
        )
        
        # Average sale price
        result['estimated_avg_sale_price'] = result.apply(
            lambda row: row['estimated_revenue'] / row['actual_sales_count'] 
            if row['actual_sales_count'] > 0 else 0,
            axis=1
        )
        
        # Conversion rate (CRM leads to sales)
        result['conversion_rate'] = result.apply(
            lambda row: (row['actual_sales_count'] / row['crm_lead_count'] * 100) 
            if row['crm_lead_count'] > 0 else 0,
            axis=1
        )
        # Performance note:
        # `apply(axis=1)` is fine for the current output size (hundreds of rows) and is easy to read.
        # If this ever needs to run on much larger tables, consider vectorizing to avoid Python loops.
        #
        # Example vectorized alternative:
        # import numpy as np
        # result['conversion_rate'] = np.where(
        #     result['crm_lead_count'] > 0,
        #     (result['actual_sales_count'] / result['crm_lead_count']) * 100,
        #     0
        # )
        
        # Traffic to sales conversion rate
        result['traffic_to_sales_rate'] = result.apply(
            lambda row: (row['actual_sales_count'] / row['web_traffic'] * 100) 
            if row['web_traffic'] > 0 else 0,
            axis=1
        )
        
        # 9. Rename and select final columns
        final_columns = [
            'year_month',
            'community_name',
            'builder',
            'actual_sales_count',  # Actual sales (count)
            'target_sales',  # Target sales
            'variance',  # Variance (actual - target)
            'crm_lead_count',  # CRM lead count
            'web_traffic',  # Web traffic
            'estimated_revenue',  # Additional: Estimated revenue
            'achievement_rate',  # Additional: Achievement rate
            'estimated_avg_sale_price',  # Additional: Estimated average sale price
            'conversion_rate',  # Additional: Conversion rate
            'traffic_to_sales_rate'  # Additional: Traffic to sales rate
        ]
        
        # Only select existing columns
        available_columns = [col for col in final_columns if col in result.columns]
        result = result[available_columns]
        
        # Rename to more friendly names
        result = result.rename(columns={
            'year_month': 'month',
            'actual_sales_count': 'actual_sales',
            'crm_lead_count': 'crm_leads',
            'web_traffic': 'web_traffic'
        })
        
        # Sort
        result = result.sort_values(['month', 'builder', 'community_name'])
        
        return result
