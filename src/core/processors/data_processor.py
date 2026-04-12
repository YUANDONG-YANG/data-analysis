"""
Data processing module for processing and transforming data.
"""
import pandas as pd
from typing import List, Optional, TYPE_CHECKING
import re

if TYPE_CHECKING:
    from ..config import AppConfig

from ..config import CommunityNamesConfig


class DataProcessor:
    """Data processor class for data transformation operations."""
    
    def __init__(self, community_names: Optional[CommunityNamesConfig] = None):
        """
        Initialize data processor.
        
        Args:
            community_names: Optional alias and path-slug rules; defaults match built-in demo data.
        """
        cn = community_names if community_names is not None else CommunityNamesConfig()
        self._community_aliases = dict(cn.aliases)
        self._path_slugs_sorted = sorted(
            (s.strip() for s in cn.path_slugs if s and str(s).strip()),
            key=lambda s: len(str(s)),
            reverse=True,
        )
    
    @classmethod
    def from_config(cls, config: "AppConfig") -> "DataProcessor":
        """Build processor using application config (including YAML `community_names`)."""
        return cls(config.community_names)
    
    def standardize_date(self, date_str: str) -> str:
        """
        Standardize date format to YYYY-MM-DD.
        
        Args:
            date_str: Date string (may be in various formats)
            
        Returns:
            Standardized date string in YYYY-MM-DD format
        """
        if pd.isna(date_str):
            return None
        
        date_str = str(date_str).strip()
        
        # Handle ISO 8601 format first (e.g., "2025-09-21T08:38:53Z")
        if 'T' in date_str:
            try:
                date_obj = pd.to_datetime(date_str, errors='coerce')
                if pd.notna(date_obj):
                    return date_obj.strftime('%Y-%m-%d')
            except:
                pass
        
        # Try multiple date formats
        date_formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%m-%d-%Y',
            '%d/%m/%Y',
            '%d-%m-%Y',
            '%Y/%m/%d',
        ]
        
        for fmt in date_formats:
            try:
                date_obj = pd.to_datetime(date_str, format=fmt)
                return date_obj.strftime('%Y-%m-%d')
            except:
                continue
        
        # If none match, try pandas auto-parsing
        try:
            date_obj = pd.to_datetime(date_str, errors='coerce')
            if pd.notna(date_obj):
                return date_obj.strftime('%Y-%m-%d')
        except:
            pass
        
        return None
    
    def standardize_community_name(self, name: str) -> str:
        """
        Standardize community name (remove variants).
        
        Args:
            name: Community name
            
        Returns:
            Standardized community name
        """
        if pd.isna(name):
            return None
        
        name = str(name).strip()
        
        # Remove "Community" suffix (e.g., "Fairview Estates Community" -> "Fairview Estates")
        name = re.sub(r'\s+Community\s*$', '', name, flags=re.IGNORECASE)
        
        # Handle common variants
        name = re.sub(r'\s*-\s*Phase\s*\d+', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\s*\([^)]*\)', '', name)
        name = re.sub(r'\s*-\s*[^-]*$', '', name)
        
        for variant, canonical in self._community_aliases.items():
            if variant in name:
                name = name.replace(variant, canonical)
        
        return name.strip()
    
    def merge_dataframes(self, dataframes: List[pd.DataFrame], 
                        how: str = 'outer', on: Optional[str] = None) -> pd.DataFrame:
        """
        Merge multiple DataFrames.
        
        Args:
            dataframes: List of DataFrames
            how: Merge method ('inner', 'outer', 'left', 'right')
            on: Merge key
            
        Returns:
            Merged DataFrame
        """
        if not dataframes:
            return pd.DataFrame()
        
        result = dataframes[0]
        for df in dataframes[1:]:
            if on:
                result = result.merge(df, how=how, on=on, suffixes=('', '_dup'))
                # Handle duplicate columns
                dup_cols = [col for col in result.columns if col.endswith('_dup')]
                for col in dup_cols:
                    orig_col = col.replace('_dup', '')
                    if orig_col in result.columns:
                        result[orig_col] = result[orig_col].fillna(result[col])
                        result = result.drop(columns=[col])
            else:
                result = pd.concat([result, df], ignore_index=True)
        
        return result
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean data by removing duplicates and outliers.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        df = df.copy()
        
        # Remove duplicate rows
        df = df.drop_duplicates()
        
        # Handle outliers in sales data
        if 'total_sale_price' in df.columns:
            # Remove negative and extremely large values
            df = df[df['total_sale_price'] > 0]
            df = df[df['total_sale_price'] < 10000000]  # Remove extremely large values
            # If these thresholds need to change per environment, you can move them into `config.yaml`,
            # e.g.
            # data_quality:
            #   price_range: [100000, 10000000]
            # and read/apply them here.
        
        if 'sqft' in df.columns:
            # Remove extremely small sqft values (likely data errors)
            df = df[df['sqft'] > 50]
            df = df[df['sqft'] < 50000]  # Remove extremely large values
            # Same idea for sqft thresholds, e.g.
            # data_quality:
            #   sqft_range: [500, 10000]
        
        return df
    
    def process_sales_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process sales data: standardize dates and community names.
        
        Args:
            df: Sales data DataFrame
            
        Returns:
            Processed DataFrame
        """
        df = df.copy()
        
        # Standardize dates
        if 'sale_contract_date' in df.columns:
            df['sale_contract_date'] = df['sale_contract_date'].apply(self.standardize_date)
            df = df[df['sale_contract_date'].notna()]
        
        # Standardize community names
        if 'community_name' in df.columns:
            df['community_name'] = df['community_name'].apply(self.standardize_community_name)
            df = df[df['community_name'].notna()]
        
        # Add year_month column
        if 'sale_contract_date' in df.columns:
            df['date'] = pd.to_datetime(df['sale_contract_date'])
            df['year_month'] = df['date'].dt.to_period('M').astype(str)
        
        return df
    
    def process_targets_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process targets data.
        
        Args:
            df: Targets data DataFrame
            
        Returns:
            Processed DataFrame containing month, community_name, target_sales, builder
        """
        df = df.copy()
        
        # Standardize community names
        if 'community_name' in df.columns:
            df['community_name'] = df['community_name'].apply(self.standardize_community_name)
            df = df[df['community_name'].notna()]
        
        # Ensure month column exists (convert from year_month if needed)
        if 'year_month' in df.columns and 'month' not in df.columns:
            df['month'] = df['year_month']
        
        # Ensure target_sales is numeric
        if 'target_sales' in df.columns:
            df['target_sales'] = pd.to_numeric(df['target_sales'], errors='coerce').fillna(0)
        
        return df
    
    def process_crm_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process CRM data: standardize dates and community names.
        
        Args:
            df: CRM data DataFrame (columns should be standardized by API client)
            
        Returns:
            Processed DataFrame
        """
        df = df.copy()
        
        # Process date field - check for standardized column first, then fallback to original columns
        date_cols = ['create_date', 'createdate', 'create_at', 'date', 'created_date', 'lead_date', 'timestamp']
        for col in date_cols:
            if col in df.columns:
                df[col] = df[col].apply(self.standardize_date)
                df = df[df[col].notna()]
                df['date'] = pd.to_datetime(df[col])
                df['year_month'] = df['date'].dt.to_period('M').astype(str)
                break
        
        # Standardize community names
        community_cols = ['community_name', 'community', 'communityName']
        for col in community_cols:
            if col in df.columns:
                df['community_name'] = df[col].apply(self.standardize_community_name)
                df = df[df['community_name'].notna()]
                break
        
        return df
    
    def process_web_traffic_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process Web Traffic data: standardize dates and community names.
        
        Args:
            df: Web Traffic data DataFrame
            
        Returns:
            Processed DataFrame
        """
        df = df.copy()
        
        # Process based on actual API response structure
        date_cols = ['date', 'visit_date', 'timestamp', 'event_date']
        for col in date_cols:
            if col in df.columns:
                df[col] = df[col].apply(self.standardize_date)
                df = df[df[col].notna()]
                df['date'] = pd.to_datetime(df[col])
                df['year_month'] = df['date'].dt.to_period('M').astype(str)
                break
        
        # Standardize community names
        community_cols = ['community_name', 'community', 'communityName', 'page_path']
        for col in community_cols:
            if col in df.columns:
                if col == 'page_path':
                    # Extract community name from URL path
                    df['community_name'] = df[col].apply(
                        lambda x: self._extract_community_from_path(x) if pd.notna(x) else None
                    )
                else:
                    df['community_name'] = df[col].apply(self.standardize_community_name)
                df = df[df['community_name'].notna()]
                break
        
        return df
    
    def _extract_community_from_path(self, path: str) -> Optional[str]:
        """
        Extract community name from URL path.
        
        Args:
            path: URL path
            
        Returns:
            Community name or None
        """
        if pd.isna(path):
            return None
        
        path = str(path).lower()
        for slug in self._path_slugs_sorted:
            slug_norm = str(slug).strip().lower()
            if slug_norm and slug_norm in path:
                return str(slug).replace('-', ' ').title()
        
        return None
    
    def aggregate_data(self, df: pd.DataFrame, 
                      group_by: List[str], 
                      agg_dict: dict) -> pd.DataFrame:
        """
        Aggregate data by grouping columns.
        
        Args:
            df: Input DataFrame
            group_by: Grouping columns
            agg_dict: Aggregation dictionary
            
        Returns:
            Aggregated DataFrame
        """
        return df.groupby(group_by).agg(agg_dict).reset_index()
    
    def filter_data(self, df: pd.DataFrame, condition: str) -> pd.DataFrame:
        """
        Filter data by condition.
        
        Args:
            df: Input DataFrame
            condition: Filter condition (pandas query string)
            
        Returns:
            Filtered DataFrame
        """
        return df.query(condition)
