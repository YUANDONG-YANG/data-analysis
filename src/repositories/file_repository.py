"""
File-based data repository implementation.
"""
import pandas as pd
from pathlib import Path
from typing import Optional
from .data_repository import DataRepository
from ..core.exceptions import DataLoadError, ErrorSeverity


class FileRepository(DataRepository):
    """Repository for file-based data sources."""
    
    def __init__(self, base_path: Path):
        """
        Initialize file repository.
        
        Args:
            base_path: Base path for data files
        """
        if not base_path.exists():
            raise DataLoadError(f"Base path does not exist: {base_path}")
        self.base_path = base_path
    
    def load_csv(self, filename: str) -> pd.DataFrame:
        """
        Load CSV file.
        
        Args:
            filename: CSV filename
            
        Returns:
            DataFrame
            
        Raises:
            DataLoadError: If file not found or cannot be read
        """
        file_path = self.base_path / filename
        if not file_path.exists():
            raise DataLoadError(f"File not found: {file_path}")
        
        try:
            return pd.read_csv(file_path)
        except FileNotFoundError:
            raise DataLoadError(
                f"CSV file not found: {file_path}",
                file_path=str(file_path),
                error_code='FILE_NOT_FOUND',
                severity=ErrorSeverity.HIGH
            )
        except pd.errors.EmptyDataError:
            raise DataLoadError(
                f"CSV file is empty: {file_path}",
                file_path=str(file_path),
                error_code='EMPTY_FILE',
                severity=ErrorSeverity.MEDIUM,
                recoverable=True
            )
        except Exception as e:
            raise DataLoadError(
                f"Error reading CSV file {file_path}: {e}",
                file_path=str(file_path),
                error_code='CSV_READ_ERROR',
                context={'original_error': type(e).__name__}
            )
    
    def load_excel(self, filename: str, **kwargs) -> pd.DataFrame:
        """
        Load Excel file.
        
        Args:
            filename: Excel filename
            **kwargs: Additional arguments for pd.read_excel
            
        Returns:
            DataFrame
            
        Raises:
            DataLoadError: If file not found or cannot be read
        """
        file_path = self.base_path / filename
        if not file_path.exists():
            raise DataLoadError(f"File not found: {file_path}")
        
        try:
            return pd.read_excel(file_path, **kwargs)
        except Exception as e:
            raise DataLoadError(f"Error reading Excel file {file_path}: {e}")
    
    def load_sales_data(self, builder: str) -> pd.DataFrame:
        """Load sales data for builder."""
        filename = f"sales_builder_{builder}.csv"
        df = self.load_csv(filename)
        df['builder'] = builder
        return df
    
    def load_targets_data(self, builder: str) -> pd.DataFrame:
        """Load targets data for builder."""
        # Try Excel first, then CSV
        excel_file = f"target_sales_builder_{builder}.xlsx"
        csv_file1 = f"target_sales_builder_{builder}.csv"
        csv_file2 = f"targets_builder_{builder}.csv"
        
        if (self.base_path / excel_file).exists():
            return self._load_excel_targets(excel_file, builder)
        elif (self.base_path / csv_file1).exists():
            return self._load_csv_targets(csv_file1, builder)
        elif (self.base_path / csv_file2).exists():
            return self._load_csv_targets(csv_file2, builder)
        else:
            raise DataLoadError(
                f"Targets file not found for builder {builder}. "
                f"Tried: {excel_file}, {csv_file1}, {csv_file2}"
            )
    
    def _load_excel_targets(self, filename: str, builder: str) -> pd.DataFrame:
        """Load targets from Excel file."""
        # Excel parsing logic for matrix format with header in row 3
        df = self.load_excel(filename, header=2)
        
        # Find Subdivision column (usually index 3)
        subdivision_col = None
        for col in df.columns:
            col_str = str(col).lower()
            if 'subdivision' in col_str:
                subdivision_col = col
                break
        
        if subdivision_col is None and len(df.columns) > 3:
            subdivision_col = df.columns[3]
        
        if subdivision_col is None:
            raise DataLoadError("Cannot find Subdivision column in Excel file")
        
        # Extract month columns (from column 4 onwards)
        month_cols = []
        for i in range(4, len(df.columns)):
            col = df.columns[i]
            col_str = str(col).strip()
            if pd.isna(col) or 'total' in col_str.lower() or col_str == '':
                continue
            month_cols.append((i, col_str))
        
        # Build long format data
        result_rows = []
        for idx, row in df.iterrows():
            community = row[subdivision_col]
            if pd.isna(community) or str(community).strip() == '':
                continue
            
            community = str(community).strip()
            if community.lower() in ['subdivision', 'company', 'department']:
                continue
            
            for col_idx, month_str in month_cols:
                try:
                    value = row.iloc[col_idx]
                    if pd.isna(value) or value == '':
                        continue
                    
                    year_month = self._parse_excel_month(month_str)
                    if year_month:
                        result_rows.append({
                            'year_month': year_month,
                            'community_name': community,
                            'target_sales': float(value) if pd.notna(value) else 0,
                            'builder': builder
                        })
                except (ValueError, IndexError):
                    continue
        
        return pd.DataFrame(result_rows)
    
    def _parse_excel_month(self, month_str: str) -> Optional[str]:
        """Parse Excel month string to YYYY-MM format."""
        import re
        if pd.isna(month_str):
            return None
        
        month_str = str(month_str).strip()
        month_map = {
            'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
            'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
            'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
        }
        
        match = re.match(r'([A-Za-z]+)-(\d+)', month_str)
        if match:
            month_name = match.group(1).lower()[:3]
            year_str = match.group(2)
            
            if month_name in month_map:
                month_num = month_map[month_name]
                year = '20' + year_str if len(year_str) == 2 else year_str
                return f"{year}-{month_num}"
        
        return None
    
    def _load_csv_targets(self, filename: str, builder: str) -> pd.DataFrame:
        """Load targets from CSV file."""
        df = self.load_csv(filename)
        
        # If already in standard format, just ensure builder column exists
        if 'year_month' in df.columns and 'community_name' in df.columns and 'target_sales' in df.columns:
            if 'builder' not in df.columns:
                df['builder'] = builder
            return df[['year_month', 'community_name', 'target_sales', 'builder']]
        
        # Handle different CSV formats
        if 'year' in df.columns and 'month' in df.columns:
            df['year_month'] = df['year'].astype(str) + '-' + df['month'].astype(str).str.zfill(2)
            df['community_name'] = df['community']
            df['target_sales'] = df['sales_target']
        elif 'month' in df.columns:
            df['year_month'] = df['month']
            if 'community_name' not in df.columns and 'community' in df.columns:
                df['community_name'] = df['community']
            if 'target_sales' not in df.columns and 'sales_target' in df.columns:
                df['target_sales'] = df['sales_target']
        
        df['builder'] = builder
        return df[['year_month', 'community_name', 'target_sales', 'builder']]
