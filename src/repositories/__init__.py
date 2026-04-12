"""
Repository pattern for data access abstraction.
"""
from .data_repository import DataRepository
from .file_repository import FileRepository
from .api_repository import APIRepository

__all__ = [
    'DataRepository',
    'FileRepository',
    'APIRepository',
]
