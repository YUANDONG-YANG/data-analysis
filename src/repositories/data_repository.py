"""
Repository pattern for data access - abstract base class.
"""
from abc import ABC, abstractmethod
from typing import List
import pandas as pd
from pathlib import Path


class DataRepository(ABC):
    """Abstract base class for data repositories."""
    
    @abstractmethod
    def load_sales_data(self, builder: str) -> pd.DataFrame:
        """Load sales data."""
        pass
    
    @abstractmethod
    def load_targets_data(self, builder: str) -> pd.DataFrame:
        """Load targets data."""
        pass
    
    def load_all_sales_data(self) -> List[pd.DataFrame]:
        """Load all sales data."""
        return [
            self.load_sales_data('a'),
            self.load_sales_data('b')
        ]
    
    def load_all_targets_data(self) -> List[pd.DataFrame]:
        """Load all targets data."""
        return [
            self.load_targets_data('a'),
            self.load_targets_data('b')
        ]
