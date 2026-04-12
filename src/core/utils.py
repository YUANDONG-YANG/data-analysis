"""
Utility functions module containing various helper functions.
"""
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration file.
    
    Args:
        config_path: Configuration file path (if None, automatically finds config.yaml in project root)
        
    Returns:
        Configuration dictionary
    """
    if config_path is None:
        # Automatically find config.yaml in project root
        # Get current file directory (src/core/utils.py)
        current_file = Path(__file__).resolve()
        # Project root should be parent of core directory
        project_root = current_file.parent.parent.parent
        config_path = project_root / "config.yaml"
    else:
        config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config


def setup_logging(level: str = "INFO"):
    """
    Setup logging configuration.
    
    Args:
        level: Logging level
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def ensure_directory(path: str):
    """
    Ensure directory exists.
    
    Args:
        path: Directory path
    """
    Path(path).mkdir(parents=True, exist_ok=True)
