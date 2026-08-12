from dataclasses import FrozenInstanceError

import pytest

from resume_ai.core.exceptions import DomainError
from resume_ai.modules.jobs.domain.entities import (
    CriterionCategory,
    CriterionImportance,
    ExperienceDurationUnit,
    ExperienceMinimumDuration,
    ExperienceRequirement,
    JobCriterion,
)


def _criterion(
    *,
    category: CriterionCategory = CriterionCategory.EXPERIENCE,
    experience_requirement: ExperienceRequirement | None = None,
) -> JobCriterion:
    return JobCriterion(
        category=category,
        value="experience requirement",
        evidence="Experience required.",
        importance=CriterionImportance.REQUIRED,
        experience_requirement=experience_requirement,
    )


def test_experience_duration_unit_has_months_and_years() -> None:
    assert [unit.value for unit in ExperienceDurationUnit] == ["months", "years"]


@pytest.mark.parametrize(
    "unit",
    [ExperienceDurationUnit.MONTHS, ExperienceDurationUnit.YEARS],
)
def test_experience_minimum_duration_accepts_valid_units(
    unit: ExperienceDurationUnit,
) -> None:
    duration = ExperienceMinimumDuration(value=3, unit=unit)

    assert duration.value == 3
    assert duration.unit is unit


@pytest.mark.parametrize("value", [0, -1])
def test_experience_minimum_duration_rejects_non_positive_values(value: int) -> None:
    with pytest.raises(DomainError):
        ExperienceMinimumDuration(value=value, unit=ExperienceDurationUnit.YEARS)


@pytest.mark.parametrize("value", ["3", 3.0, True, None])
def test_experience_minimum_duration_rejects_invalid_value_types(value: object) -> None:
    with pytest.raises(DomainError):
        ExperienceMinimumDuration(value=value, unit=ExperienceDurationUnit.YEARS)  # type: ignore[arg-type]


def test_experience_minimum_duration_rejects_invalid_unit() -> None:
    with pytest.raises(DomainError):
        ExperienceMinimumDuration(value=3, unit="years")  # type: ignore[arg-type]


def test_experience_requirement_accepts_each_dimension_and_all_dimensions() -> None:
    duration = ExperienceMinimumDuration(18, ExperienceDurationUnit.MONTHS)

    assert ExperienceRequirement(role="Backend Developer")
    assert ExperienceRequirement(company="Example Corp")
    assert ExperienceRequirement(minimum_duration=duration)
    assert ExperienceRequirement(
        role="Backend Developer",
        company="Example Corp",
        minimum_duration=duration,
    )


def test_experience_requirement_minimum_duration_evidence_defaults_to_none() -> None:
    requirement = ExperienceRequirement(role="Backend Developer")

    assert requirement.minimum_duration_evidence is None


def test_experience_requirement_accepts_duration_with_evidence() -> None:
    duration = ExperienceMinimumDuration(3, ExperienceDurationUnit.YEARS)

    requirement = ExperienceRequirement(
        minimum_duration=duration,
        minimum_duration_evidence="3 years",
    )

    assert requirement.minimum_duration is duration
    assert requirement.minimum_duration_evidence == "3 years"


def test_experience_requirement_preserves_duration_evidence_exactly() -> None:
    evidence = "  3 Years of experience  "
    requirement = ExperienceRequirement(
        minimum_duration=ExperienceMinimumDuration(3, ExperienceDurationUnit.YEARS),
        minimum_duration_evidence=evidence,
    )

    assert requirement.minimum_duration_evidence == evidence


@pytest.mark.parametrize("value", ["", "   ", "\n\t"])
def test_experience_requirement_rejects_blank_duration_evidence(value: str) -> None:
    with pytest.raises(DomainError):
        ExperienceRequirement(
            minimum_duration=ExperienceMinimumDuration(3, ExperienceDurationUnit.YEARS),
            minimum_duration_evidence=value,
        )


@pytest.mark.parametrize("value", [3, True, None])
def test_experience_requirement_rejects_non_string_duration_evidence(
    value: object,
) -> None:
    if value is None:
        return

    with pytest.raises(DomainError):
        ExperienceRequirement(
            minimum_duration=ExperienceMinimumDuration(3, ExperienceDurationUnit.YEARS),
            minimum_duration_evidence=value,  # type: ignore[arg-type]
        )


def test_experience_requirement_rejects_evidence_without_duration() -> None:
    with pytest.raises(DomainError):
        ExperienceRequirement(
            role="Backend Developer",
            minimum_duration_evidence="3 years",
        )


def test_experience_requirement_accepts_duration_without_evidence() -> None:
    duration = ExperienceMinimumDuration(3, ExperienceDurationUnit.YEARS)

    requirement = ExperienceRequirement(minimum_duration=duration)

    assert requirement.minimum_duration is duration
    assert requirement.minimum_duration_evidence is None


def test_experience_requirement_accepts_role_duration_and_evidence() -> None:
    requirement = ExperienceRequirement(
        role="Backend Developer",
        minimum_duration=ExperienceMinimumDuration(3, ExperienceDurationUnit.YEARS),
        minimum_duration_evidence="3 years",
    )

    assert requirement.role == "Backend Developer"


def test_experience_requirement_accepts_company_duration_and_evidence() -> None:
    requirement = ExperienceRequirement(
        company="Example Corp",
        minimum_duration=ExperienceMinimumDuration(3, ExperienceDurationUnit.YEARS),
        minimum_duration_evidence="3 years",
    )

    assert requirement.company == "Example Corp"


def test_duration_evidence_alone_does_not_define_requirement() -> None:
    with pytest.raises(DomainError):
        ExperienceRequirement(
            minimum_duration_evidence="3 years",
        )


@pytest.mark.parametrize("field", ["role", "company"])
@pytest.mark.parametrize("value", ["", "   ", "\n\t"])
def test_experience_requirement_rejects_blank_text(field: str, value: str) -> None:
    with pytest.raises(DomainError):
        ExperienceRequirement(**{field: value})


def test_experience_requirement_rejects_empty_requirement() -> None:
    with pytest.raises(DomainError):
        ExperienceRequirement()


def test_experience_requirement_rejects_invalid_minimum_duration() -> None:
    with pytest.raises(DomainError):
        ExperienceRequirement(minimum_duration="3 years")  # type: ignore[arg-type]


def test_job_criterion_experience_accepts_experience_requirement() -> None:
    requirement = ExperienceRequirement(role="Backend Developer")

    criterion = _criterion(experience_requirement=requirement)

    assert criterion.experience_requirement is requirement


def test_job_criterion_rejects_experience_requirement_for_other_category() -> None:
    with pytest.raises(DomainError):
        _criterion(
            category=CriterionCategory.TECHNOLOGY,
            experience_requirement=ExperienceRequirement(role="Python"),
        )


def test_job_criterion_without_experience_requirement_remains_valid() -> None:
    criterion = _criterion()

    assert criterion.experience_requirement is None


@pytest.mark.parametrize(
    "value",
    [
        ExperienceMinimumDuration(3, ExperienceDurationUnit.YEARS),
        "3 years",
        3,
        None,
    ],
)
def test_only_domain_duration_object_is_accepted(value: object) -> None:
    if isinstance(value, ExperienceMinimumDuration):
        assert ExperienceRequirement(minimum_duration=value)
    else:
        with pytest.raises(DomainError):
            ExperienceRequirement(minimum_duration=value)  # type: ignore[arg-type]


def test_experience_dataclasses_are_frozen_and_slotted() -> None:
    duration = ExperienceMinimumDuration(3, ExperienceDurationUnit.YEARS)
    requirement = ExperienceRequirement(role="Backend Developer")

    with pytest.raises(FrozenInstanceError):
        duration.value = 4
    with pytest.raises(FrozenInstanceError):
        requirement.role = "Engineer"
    with pytest.raises(FrozenInstanceError):
        requirement.minimum_duration_evidence = "3 years"
    assert not hasattr(duration, "__dict__")
    assert not hasattr(requirement, "__dict__")
