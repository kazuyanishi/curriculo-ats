import pytest
from pydantic import ValidationError

from resume_ai.modules.jobs.application.schemas import (
    ExperienceMinimumDurationInput,
    ExperienceRequirementInput,
    JobCriterionInput,
)
from resume_ai.modules.jobs.domain.entities import (
    CriterionCategory,
    ExperienceDurationUnit,
    ExperienceMinimumDuration,
    ExperienceRequirement,
    JobCriterion,
)


def test_duration_converts_external_units_and_to_domain() -> None:
    years = ExperienceMinimumDurationInput(value=3, unit="years")
    months = ExperienceMinimumDurationInput(value=18, unit="months")

    assert years.unit is ExperienceDurationUnit.YEARS
    assert months.unit is ExperienceDurationUnit.MONTHS
    assert years.to_domain() == ExperienceMinimumDuration(
        value=3, unit=ExperienceDurationUnit.YEARS
    )


@pytest.mark.parametrize("value", [0, -1])
def test_duration_rejects_non_positive_values(value: int) -> None:
    with pytest.raises(ValidationError):
        ExperienceMinimumDurationInput(value=value, unit="years")


@pytest.mark.parametrize("value", ["3", 3.0, True, None])
def test_duration_rejects_non_strict_integer_values(value: object) -> None:
    with pytest.raises(ValidationError):
        ExperienceMinimumDurationInput(value=value, unit="years")


def test_duration_rejects_invalid_unit() -> None:
    with pytest.raises(ValidationError):
        ExperienceMinimumDurationInput(value=3, unit="weeks")


def test_requirement_accepts_each_dimension_and_all_dimensions() -> None:
    duration = {"value": 18, "unit": "months"}

    assert ExperienceRequirementInput(role="Backend Developer")
    assert ExperienceRequirementInput(company="Example Corp")
    assert ExperienceRequirementInput(minimum_duration=duration)
    assert ExperienceRequirementInput(
        role="Backend Developer", company="Example Corp", minimum_duration=duration
    )


def test_requirement_minimum_duration_evidence_defaults_to_none() -> None:
    requirement = ExperienceRequirementInput(role="Backend Developer")

    assert requirement.minimum_duration_evidence is None


def test_requirement_accepts_duration_with_evidence() -> None:
    requirement = ExperienceRequirementInput(
        minimum_duration={"value": 3, "unit": "years"},
        minimum_duration_evidence="3 years",
    )

    assert requirement.minimum_duration_evidence == "3 years"


def test_requirement_preserves_duration_evidence_exactly() -> None:
    evidence = "  3 Years of experience  "
    requirement = ExperienceRequirementInput(
        minimum_duration={"value": 3, "unit": "years"},
        minimum_duration_evidence=evidence,
    )

    assert requirement.minimum_duration_evidence == evidence


@pytest.mark.parametrize("value", ["", "   ", "\n\t"])
def test_requirement_rejects_blank_duration_evidence(value: str) -> None:
    with pytest.raises(ValidationError):
        ExperienceRequirementInput(
            minimum_duration={"value": 3, "unit": "years"},
            minimum_duration_evidence=value,
        )


@pytest.mark.parametrize("value", [3, True, []])
def test_requirement_rejects_non_string_duration_evidence(value: object) -> None:
    with pytest.raises(ValidationError):
        ExperienceRequirementInput(
            minimum_duration={"value": 3, "unit": "years"},
            minimum_duration_evidence=value,
        )


def test_requirement_rejects_evidence_without_duration() -> None:
    with pytest.raises(ValidationError):
        ExperienceRequirementInput(
            role="Backend Developer",
            minimum_duration_evidence="3 years",
        )


def test_requirement_accepts_duration_without_evidence() -> None:
    requirement = ExperienceRequirementInput(
        minimum_duration={"value": 3, "unit": "years"}
    )

    assert requirement.minimum_duration_evidence is None


def test_requirement_accepts_role_duration_and_evidence() -> None:
    requirement = ExperienceRequirementInput(
        role="Backend Developer",
        minimum_duration={"value": 3, "unit": "years"},
        minimum_duration_evidence="3 years",
    )

    assert requirement.role == "Backend Developer"


@pytest.mark.parametrize("field", ["role", "company"])
@pytest.mark.parametrize("value", ["", "   ", "\n\t"])
def test_requirement_rejects_blank_text(field: str, value: str) -> None:
    with pytest.raises(ValidationError):
        ExperienceRequirementInput(**{field: value})


def test_requirement_rejects_empty_payload() -> None:
    with pytest.raises(ValidationError):
        ExperienceRequirementInput()


def test_requirement_rejects_nested_and_top_level_extra_fields() -> None:
    with pytest.raises(ValidationError):
        ExperienceRequirementInput(
            minimum_duration={"value": 3, "unit": "years", "extra": True}
        )
    with pytest.raises(ValidationError):
        ExperienceRequirementInput(role="Backend Developer", extra=True)


def test_requirement_to_domain_preserves_text_and_duration() -> None:
    schema = ExperienceRequirementInput(
        role="  Backend Developer  ",
        company="  Example Corp  ",
        minimum_duration={"value": 3, "unit": "years"},
        minimum_duration_evidence="  3 years  ",
    )

    domain = schema.to_domain()

    assert isinstance(domain, ExperienceRequirement)
    assert domain.role == "  Backend Developer  "
    assert domain.company == "  Example Corp  "
    assert domain.minimum_duration == ExperienceMinimumDuration(
        value=3, unit=ExperienceDurationUnit.YEARS
    )
    assert domain.minimum_duration_evidence == "  3 years  "


def test_experience_criterion_accepts_nested_requirement_and_converts_to_domain() -> None:
    schema = JobCriterionInput(
        category="experience",
        value="Backend Developer",
        evidence="Backend Developer experience required.",
        experience_requirement={
            "role": "Backend Developer",
            "minimum_duration": {"value": 3, "unit": "years"},
        },
    )

    domain = schema.to_domain()

    assert schema.experience_requirement is not None
    assert isinstance(domain, JobCriterion)
    assert domain.category is CriterionCategory.EXPERIENCE
    assert domain.experience_requirement is not None
    assert domain.experience_requirement.role == "Backend Developer"
    assert domain.experience_requirement.minimum_duration == ExperienceMinimumDuration(
        value=3, unit=ExperienceDurationUnit.YEARS
    )


def test_non_experience_category_rejects_experience_requirement() -> None:
    with pytest.raises(ValidationError):
        JobCriterionInput(
            category="technology",
            value="Python",
            evidence="Python is required.",
            experience_requirement={"role": "Backend Developer"},
        )


def test_criterion_without_experience_requirement_remains_valid() -> None:
    schema = JobCriterionInput(
        category="experience",
        value="Backend Developer",
        evidence="Backend Developer experience required.",
    )

    assert schema.experience_requirement is None
    assert schema.to_domain().experience_requirement is None


def test_experience_schemas_are_frozen() -> None:
    duration = ExperienceMinimumDurationInput(value=3, unit="years")
    requirement = ExperienceRequirementInput(role="Backend Developer")

    with pytest.raises(ValidationError):
        duration.value = 4
    with pytest.raises(ValidationError):
        requirement.role = "Engineer"
    with pytest.raises(ValidationError):
        requirement.minimum_duration_evidence = "3 years"
