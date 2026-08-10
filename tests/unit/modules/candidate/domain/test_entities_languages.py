from dataclasses import FrozenInstanceError

import pytest

from resume_ai.core.exceptions import DomainError
from resume_ai.modules.candidate.domain.entities import (
    Language,
    LanguageLevel,
    ProficiencyLevel,
    Skill,
)


def test_language_level_values_are_stable() -> None:
    assert LanguageLevel.BASIC.value == "basic"
    assert LanguageLevel.INTERMEDIATE.value == "intermediate"
    assert LanguageLevel.ADVANCED.value == "advanced"
    assert LanguageLevel.FLUENT.value == "fluent"
    assert LanguageLevel.NATIVE.value == "native"


def test_language_accepts_name_without_level() -> None:
    language = Language("English")

    assert language.name == "English"
    assert language.level is None


@pytest.mark.parametrize("level", list(LanguageLevel))
def test_language_accepts_all_language_levels(level: LanguageLevel) -> None:
    language = Language("English", level)

    assert language.level is level


@pytest.mark.parametrize("name", ["", "   "])
def test_language_rejects_empty_name(name: str) -> None:
    with pytest.raises(DomainError, match="name cannot be empty"):
        Language(name)


@pytest.mark.parametrize("level", ["intermediate", object(), ProficiencyLevel.ADVANCED])
def test_language_rejects_non_language_level(level) -> None:
    with pytest.raises(DomainError, match="level must be a LanguageLevel or None"):
        Language("English", level)


def test_skill_rejects_language_level() -> None:
    with pytest.raises(DomainError, match="level must be a ProficiencyLevel or None"):
        Skill("Communication", LanguageLevel.ADVANCED)


def test_language_preserves_name_without_normalization() -> None:
    language = Language("  English  ")

    assert language.name == "  English  "


def test_language_is_immutable() -> None:
    language = Language("English")

    with pytest.raises(FrozenInstanceError):
        language.name = "Spanish"
