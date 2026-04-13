from pathlib import Path

import pytest

from src.core.config import AppConfig, CommunityNamesConfig
from src.core.exceptions import ConfigurationError


def test_from_dict_uses_default_community_names_when_section_missing():
    config = AppConfig.from_dict(
        {
            "api": {"base_url": "https://example.com", "api_key": "secret"},
            "data": {"raw_path": "data/bronze", "processed_path": "data/silver", "output_path": "data/gold"},
            "logging": {"level": "INFO"},
        }
    )

    assert isinstance(config.community_names, CommunityNamesConfig)
    assert config.community_names.aliases["Riverbend TH"] == "Riverbend Townhomes"
    assert "fairview-estates" in config.community_names.path_slugs


def test_from_dict_rejects_invalid_community_names_shape():
    with pytest.raises(ConfigurationError, match="community_names.aliases must be a mapping"):
        AppConfig.from_dict(
            {
                "api": {"base_url": "https://example.com", "api_key": "secret"},
                "community_names": {"aliases": ["bad-shape"]},
            }
        )


def test_get_output_path_creates_directory(tmp_path: Path):
    config = AppConfig.from_dict(
        {
            "api": {"base_url": "https://example.com", "api_key": "secret"},
            "data": {"output_path": "artifacts/gold"},
        },
        project_root=tmp_path,
    )

    output_path = config.data.get_output_path(tmp_path)

    assert output_path == tmp_path / "artifacts" / "gold"
    assert output_path.exists()
    assert output_path.is_dir()


def test_validate_raises_for_invalid_logging_level():
    config = AppConfig.from_dict(
        {
            "api": {"base_url": "https://example.com", "api_key": "secret"},
            "logging": {"level": "TRACE"},
        }
    )

    with pytest.raises(ConfigurationError, match="Invalid logging level"):
        config.validate()


def test_get_supports_dot_notation_and_default():
    config = AppConfig.from_dict(
        {
            "api": {"base_url": "https://example.com", "api_key": "secret", "timeout": 12},
        }
    )

    assert config.get("api.timeout") == 12
    assert config.get("api.endpoints.crm", "missing") == "missing"
    assert config.get("does.not.exist", "fallback") == "fallback"
