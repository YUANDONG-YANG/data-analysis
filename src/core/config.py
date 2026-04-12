"""
Configuration management using dataclasses for type safety and validation.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml
from .exceptions import ConfigurationError
from .interfaces import IConfiguration

# Defaults used when `community_names` is absent or a key is omitted in YAML.
_DEFAULT_COMMUNITY_ALIASES: Dict[str, str] = {
    "Riverbend TH": "Riverbend Townhomes",
    "FairviewEstates": "Fairview Estates",
    "Fairview Est.": "Fairview Estates",
    "Maplewood-Heights": "Maplewood Heights",
    "Maplewood Heights - Phase 2": "Maplewood Heights",
    "Fairview Estates - Phase 2": "Fairview Estates",
}

_DEFAULT_PATH_SLUGS: List[str] = [
    "fairview-estates",
    "riverbend-townhomes",
    "glenview-meadows",
    "cedar-creek",
    "willow-creek-meadows",
    "maplewood-heights",
    "oakridge-villas",
    "sunset-pines",
]


@dataclass
class CommunityNamesConfig:
    """Variant-to-canonical community names and URL path slugs for traffic parsing."""
    aliases: Dict[str, str] = field(
        default_factory=lambda: dict(_DEFAULT_COMMUNITY_ALIASES)
    )
    path_slugs: List[str] = field(
        default_factory=lambda: list(_DEFAULT_PATH_SLUGS)
    )


def _community_names_from_dict(raw: Any) -> CommunityNamesConfig:
    """Build CommunityNamesConfig from YAML `community_names` section."""
    if not raw:
        return CommunityNamesConfig()
    if not isinstance(raw, dict):
        raise ConfigurationError("community_names must be a mapping")
    aliases_raw = raw.get("aliases")
    if aliases_raw is None:
        aliases = dict(_DEFAULT_COMMUNITY_ALIASES)
    elif not isinstance(aliases_raw, dict):
        raise ConfigurationError("community_names.aliases must be a mapping")
    else:
        aliases = {str(k): str(v) for k, v in aliases_raw.items()}
    slugs_raw = raw.get("path_slugs")
    if slugs_raw is None:
        path_slugs = list(_DEFAULT_PATH_SLUGS)
    elif not isinstance(slugs_raw, list):
        raise ConfigurationError("community_names.path_slugs must be a list")
    else:
        path_slugs = [str(s) for s in slugs_raw]
    return CommunityNamesConfig(aliases=aliases, path_slugs=path_slugs)


@dataclass
class APIConfig:
    """API configuration."""
    base_url: str
    api_key: str
    timeout: int = 30
    endpoints: Dict[str, str] = field(default_factory=dict)
    
    def validate(self) -> None:
        """Validate API configuration."""
        if not self.base_url:
            raise ConfigurationError("API base_url is required")
        if not self.api_key:
            raise ConfigurationError("API api_key is required")
        if self.timeout <= 0:
            raise ConfigurationError("API timeout must be positive")


@dataclass
class DataConfig:
    """Data paths configuration."""
    raw_path: str = "data/raw"
    processed_path: str = "data/processed"
    output_path: str = "data/output"
    
    def get_raw_path(self, project_root: Path) -> Path:
        """Get absolute path for raw data."""
        path = Path(self.raw_path)
        return project_root / path if not path.is_absolute() else path
    
    def get_processed_path(self, project_root: Path) -> Path:
        """Get absolute path for processed data."""
        path = Path(self.processed_path)
        return project_root / path if not path.is_absolute() else path
    
    def get_output_path(self, project_root: Path) -> Path:
        """Get absolute path for output data."""
        path = Path(self.output_path)
        result = project_root / path if not path.is_absolute() else path
        result.mkdir(parents=True, exist_ok=True)
        return result


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    datefmt: str = "%Y-%m-%d %H:%M:%S"
    
    def validate(self) -> None:
        """Validate logging configuration."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.level.upper() not in valid_levels:
            raise ConfigurationError(f"Invalid logging level: {self.level}")


@dataclass
class AppConfig(IConfiguration):
    """Application configuration container."""
    api: APIConfig
    data: DataConfig
    logging: LoggingConfig
    community_names: CommunityNamesConfig = field(default_factory=CommunityNamesConfig)
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent)
    
    @classmethod
    def from_yaml(cls, config_path: Optional[str] = None) -> 'AppConfig':
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to config file. If None, auto-detect.
            
        Returns:
            AppConfig instance
        """
        if config_path is None:
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config.yaml"
        else:
            config_path = Path(config_path)
        
        if not config_path.exists():
            raise ConfigurationError(f"Config file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f)
        
        return cls.from_dict(config_dict, config_path.parent)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any], project_root: Optional[Path] = None) -> 'AppConfig':
        """Create AppConfig from dictionary."""
        if project_root is None:
            project_root = Path(__file__).parent.parent.parent
        
        api_config = APIConfig(
            base_url=config_dict.get('api', {}).get('base_url', ''),
            api_key=config_dict.get('api', {}).get('api_key', ''),
            timeout=config_dict.get('api', {}).get('timeout', 30),
            endpoints=config_dict.get('api', {}).get('endpoints', {})
        )
        
        data_config = DataConfig(
            raw_path=config_dict.get('data', {}).get('raw_path', 'data/raw'),
            processed_path=config_dict.get('data', {}).get('processed_path', 'data/processed'),
            output_path=config_dict.get('data', {}).get('output_path', 'data/output')
        )
        
        logging_config = LoggingConfig(
            level=config_dict.get('logging', {}).get('level', 'INFO'),
            format=config_dict.get('logging', {}).get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            datefmt=config_dict.get('logging', {}).get('datefmt', '%Y-%m-%d %H:%M:%S')
        )
        
        community_names = _community_names_from_dict(config_dict.get('community_names'))
        
        return cls(
            api=api_config,
            data=data_config,
            logging=logging_config,
            community_names=community_names,
            project_root=project_root
        )
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports dot notation)."""
        keys = key.split('.')
        value = self
        
        for k in keys:
            if hasattr(value, k):
                value = getattr(value, k)
            elif isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        
        return value if value is not None else default
    
    def validate(self) -> bool:
        """Validate all configuration."""
        try:
            self.api.validate()
            self.logging.validate()
            return True
        except ConfigurationError:
            raise
