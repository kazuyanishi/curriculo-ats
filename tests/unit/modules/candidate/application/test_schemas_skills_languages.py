import pytest
from pydantic import ValidationError

from resume_ai.modules.candidate.application.schemas import (
    LanguageInput,
    SkillInput,
    TechnologyInput,
    ToolInput,
)
from resume_ai.modules.candidate.domain.entities import (
    Language,
    LanguageLevel,
    ProficiencyLevel,
    Skill,
    Technology,
    Tool,
)


@pytest.mark.parametrize("schema_type", [SkillInput, TechnologyInput, ToolInput])
@pytest.mark.parametrize("level", list(ProficiencyLevel))
def test_technical_inputs_accept_proficiency_levels(schema_type, level: ProficiencyLevel) -> None:
    schema = schema_type(name="Python", level=level.value)

    assert schema.level is level


@pytest.mark.parametrize("schema_type", [SkillInput, TechnologyInput, ToolInput])
def test_technical_inputs_preserve_none_level_and_convert_to_domain(schema_type) -> None:
    schema = schema_type(name="Python", level=None)
    domain = schema.to_domain()

    assert schema.level is None
    assert isinstance(domain, (Skill, Technology, Tool))
    assert domain.level is None


@pytest.mark.parametrize("schema_type", [SkillInput, TechnologyInput, ToolInput])
@pytest.mark.parametrize("name", ["", "   "])
def test_technical_inputs_reject_blank_names(schema_type, name: str) -> None:
    with pytest.raises(ValidationError):
        schema_type(name=name)


@pytest.mark.parametrize("schema_type", [SkillInput, TechnologyInput, ToolInput])
@pytest.mark.parametrize("level", ["senior", "fluent", ""])
def test_technical_inputs_reject_invalid_levels(schema_type, level: str) -> None:
    with pytest.raises(ValidationError):
        schema_type(name="Python", level=level)


@pytest.mark.parametrize("schema_type", [SkillInput, TechnologyInput, ToolInput])
def test_technical_inputs_reject_language_level_enum(schema_type) -> None:
    with pytest.raises(ValidationError):
        schema_type(name="Communication", level=LanguageLevel.ADVANCED)


def test_language_input_accepts_levels_and_converts_to_domain() -> None:
    schema = LanguageInput(name="  English  ", level="fluent")
    domain = schema.to_domain()

    assert schema.level is LanguageLevel.FLUENT
    assert isinstance(domain, Language)
    assert domain.name == "  English  "
    assert domain.level is LanguageLevel.FLUENT


@pytest.mark.parametrize("level", ["basic", "intermediate", "advanced", "fluent", "native"])
def test_language_input_accepts_language_levels(level: str) -> None:
    assert LanguageInput(name="English", level=level).level is LanguageLevel(level)


@pytest.mark.parametrize("level", ["expert", "C1", "beginner", ""])
def test_language_input_rejects_invalid_levels(level: str) -> None:
    with pytest.raises(ValidationError):
        LanguageInput(name="English", level=level)


def test_language_input_rejects_proficiency_level_enum() -> None:
    with pytest.raises(ValidationError):
        LanguageInput(name="English", level=ProficiencyLevel.ADVANCED)


def test_language_input_accepts_none_level() -> None:
    assert LanguageInput(name="English", level=None).level is None
