from dataclasses import FrozenInstanceError

import pytest

from resume_ai.core.exceptions import DomainError
from resume_ai.modules.candidate.domain.entities import (
    ProficiencyLevel,
    Skill,
    Technology,
    Tool,
)


def test_proficiency_level_values_are_stable() -> None:
    assert ProficiencyLevel.BASIC.value == "basic"
    assert ProficiencyLevel.INTERMEDIATE.value == "intermediate"
    assert ProficiencyLevel.ADVANCED.value == "advanced"
    assert ProficiencyLevel.EXPERT.value == "expert"


def test_skill_accepts_name_without_level() -> None:
    skill = Skill("Problem solving")

    assert skill.name == "Problem solving"
    assert skill.level is None


def test_skill_accepts_valid_level() -> None:
    skill = Skill("Communication", ProficiencyLevel.ADVANCED)

    assert skill.name == "Communication"
    assert skill.level is ProficiencyLevel.ADVANCED


def test_technology_and_tool_accept_valid_values() -> None:
    technology = Technology("Python", ProficiencyLevel.INTERMEDIATE)
    tool = Tool("Docker", ProficiencyLevel.BASIC)

    assert technology.name == "Python"
    assert technology.level is ProficiencyLevel.INTERMEDIATE
    assert tool.name == "Docker"
    assert tool.level is ProficiencyLevel.BASIC


@pytest.mark.parametrize("entity_type", [Skill, Technology, Tool])
def test_named_entities_accept_missing_level(entity_type) -> None:
    entity = entity_type("Python")

    assert entity.level is None


@pytest.mark.parametrize("entity_type", [Skill, Technology, Tool])
@pytest.mark.parametrize("name", ["", "   "])
def test_named_entities_reject_empty_name(entity_type, name: str) -> None:
    with pytest.raises(DomainError, match="name cannot be empty"):
        entity_type(name)


@pytest.mark.parametrize("entity_type", [Skill, Technology, Tool])
@pytest.mark.parametrize("level", ["advanced", object()])
def test_named_entities_reject_non_enum_level(entity_type, level) -> None:
    with pytest.raises(DomainError, match="level must be a ProficiencyLevel or None"):
        entity_type("Python", level)


def test_names_are_preserved_without_normalization() -> None:
    technology = Technology("  PostgreSQL  ")

    assert technology.name == "  PostgreSQL  "


def test_named_entities_are_immutable() -> None:
    technology = Technology("Python")

    with pytest.raises(FrozenInstanceError):
        technology.name = "Java"
