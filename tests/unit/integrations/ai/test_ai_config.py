from dataclasses import FrozenInstanceError

import pytest

from resume_ai.integrations.ai.config import AIConfig, load_ai_config


def test_load_ai_config_reads_values_from_the_provided_environment() -> None:
    config = load_ai_config(
        {
            "RESUME_AI_API_KEY": "test-key",
            "RESUME_AI_MODEL": "test-model",
        }
    )

    assert config.api_key == "test-key"
    assert config.model == "test-model"


def test_ai_config_is_frozen_and_slotted() -> None:
    config = AIConfig(api_key="test-key", model="test-model")

    with pytest.raises(FrozenInstanceError):
        config.model = "other-model"
    assert not hasattr(config, "__dict__")


def test_ai_config_repr_does_not_expose_api_key() -> None:
    config = AIConfig(api_key="secret-test-key", model="test-model")

    assert "secret-test-key" not in repr(config)
    assert "test-model" in repr(config)


@pytest.mark.parametrize(
    "key, value",
    [
        ("RESUME_AI_API_KEY", None),
        ("RESUME_AI_API_KEY", ""),
        ("RESUME_AI_API_KEY", "   "),
    ],
)
def test_missing_or_blank_api_key_raises_value_error(
    key: str, value: str | None
) -> None:
    environ = {"RESUME_AI_MODEL": "test-model"}
    if value is not None:
        environ[key] = value

    with pytest.raises(ValueError, match="RESUME_AI_API_KEY is required"):
        load_ai_config(environ)


@pytest.mark.parametrize("value", [None, "", "   "])
def test_missing_or_blank_model_raises_value_error(value: str | None) -> None:
    environ = {"RESUME_AI_API_KEY": "test-key"}
    if value is not None:
        environ["RESUME_AI_MODEL"] = value

    with pytest.raises(ValueError, match="RESUME_AI_MODEL is required"):
        load_ai_config(environ)


def test_valid_values_are_preserved_exactly() -> None:
    config = load_ai_config(
        {
            "RESUME_AI_API_KEY": "  test-key  ",
            "RESUME_AI_MODEL": "  test-model  ",
        }
    )

    assert config.api_key == "  test-key  "
    assert config.model == "  test-model  "
