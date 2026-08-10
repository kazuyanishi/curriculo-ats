from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from resume_ai.core import config as config_module
from resume_ai.core.config import AppConfig, load_config


def test_paths_are_derived_from_package_location() -> None:
    expected_package_root = Path(config_module.__file__).resolve().parents[1]
    expected_project_root = expected_package_root.parents[1]
    config = load_config({})

    assert isinstance(config, AppConfig)
    assert isinstance(config.project_root, Path)
    assert isinstance(config.package_root, Path)
    assert isinstance(config.data_dir, Path)
    assert isinstance(config.output_dir, Path)
    assert config.package_root == expected_package_root
    assert config.project_root == expected_project_root
    assert config.data_dir == expected_project_root / "data"
    assert config.output_dir == expected_project_root / "output"


@pytest.mark.parametrize("value", [None, "", "   "])
def test_missing_or_empty_environment_defaults_to_development(value: str | None) -> None:
    environ = {} if value is None else {"RESUME_AI_ENV": value}

    assert load_config(environ).environment == "development"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("development", "development"),
        ("test", "test"),
        ("production", "production"),
        (" Production ", "production"),
    ],
)
def test_supported_environments_are_normalized(value: str, expected: str) -> None:
    assert load_config({"RESUME_AI_ENV": value}).environment == expected


def test_invalid_environment_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Invalid RESUME_AI_ENV"):
        load_config({"RESUME_AI_ENV": "banana"})


def test_config_is_immutable() -> None:
    config = load_config({})

    with pytest.raises(FrozenInstanceError):
        config.environment = "production"
