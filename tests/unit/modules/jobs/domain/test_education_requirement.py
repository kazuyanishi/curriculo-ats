from dataclasses import FrozenInstanceError

import pytest

from resume_ai.core.exceptions import DomainError
from resume_ai.modules.jobs.domain.entities import (
    CriterionCategory,
    EducationRequirement,
    EducationRequirementStatus,
    JobCriterion,
)


def _criterion_with_requirement(requirement: EducationRequirement) -> JobCriterion:
    return JobCriterion(
        category=CriterionCategory.EDUCATION,
        value="Bachelor's degree in Computer Science",
        evidence="Bachelor's degree in Computer Science is required.",
        education_requirement=requirement,
    )


def test_education_requirement_status_has_exact_values() -> None:
    assert [status.value for status in EducationRequirementStatus] == [
        "completed",
        "in_progress",
    ]


@pytest.mark.parametrize(
    "requirement",
    [
        EducationRequirement(degree_level="Bachelor's"),
        EducationRequirement(field_of_study="Computer Science"),
        EducationRequirement(institution="Example University"),
        EducationRequirement(
            acceptable_statuses=(EducationRequirementStatus.IN_PROGRESS,)
        ),
    ],
)
def test_single_education_requirement_fields_are_valid(
    requirement: EducationRequirement,
) -> None:
    assert requirement


def test_education_requirement_accepts_all_fields() -> None:
    requirement = EducationRequirement(
        degree_level="Bachelor's",
        field_of_study="Computer Science",
        institution="Example University",
        acceptable_statuses=(EducationRequirementStatus.COMPLETED,),
    )

    assert requirement.degree_level == "Bachelor's"
    assert requirement.field_of_study == "Computer Science"
    assert requirement.institution == "Example University"
    assert requirement.acceptable_statuses == (EducationRequirementStatus.COMPLETED,)


def test_education_requirement_preserves_status_order_and_identity() -> None:
    statuses = (
        EducationRequirementStatus.COMPLETED,
        EducationRequirementStatus.IN_PROGRESS,
    )

    requirement = EducationRequirement(acceptable_statuses=statuses)

    assert requirement.acceptable_statuses is statuses


def test_empty_education_requirement_is_rejected() -> None:
    with pytest.raises(DomainError, match="at least one requirement"):
        EducationRequirement()


@pytest.mark.parametrize("field_name", ["degree_level", "field_of_study", "institution"])
@pytest.mark.parametrize("value", ["", "   "])
def test_optional_text_fields_reject_blank_values(field_name: str, value: str) -> None:
    with pytest.raises(DomainError):
        EducationRequirement(**{field_name: value})


def test_optional_text_fields_allow_none() -> None:
    requirement = EducationRequirement(
        degree_level=None,
        field_of_study="Computer Science",
        institution=None,
    )

    assert requirement.degree_level is None
    assert requirement.institution is None


def test_optional_text_fields_reject_non_strings() -> None:
    with pytest.raises(DomainError):
        EducationRequirement(field_of_study=42)  # type: ignore[arg-type]


def test_statuses_must_be_a_tuple_of_real_enums() -> None:
    with pytest.raises(DomainError):
        EducationRequirement(
            field_of_study="Computer Science",
            acceptable_statuses=[EducationRequirementStatus.COMPLETED],  # type: ignore[arg-type]
        )
    with pytest.raises(DomainError):
        EducationRequirement(
            field_of_study="Computer Science",
            acceptable_statuses=("completed",),  # type: ignore[arg-type]
        )
    with pytest.raises(DomainError):
        EducationRequirement(
            field_of_study="Computer Science",
            acceptable_statuses=(None,),  # type: ignore[arg-type]
        )


def test_education_requirement_is_frozen_and_slotted() -> None:
    requirement = EducationRequirement(field_of_study="Computer Science")

    with pytest.raises(FrozenInstanceError):
        requirement.field_of_study = "Physics"
    assert not hasattr(requirement, "__dict__")


def test_job_criterion_accepts_structured_education_requirement() -> None:
    requirement = EducationRequirement(field_of_study="Computer Science")

    criterion = _criterion_with_requirement(requirement)

    assert criterion.education_requirement is requirement


def test_job_criterion_education_requirement_is_optional_for_legacy_data() -> None:
    criterion = JobCriterion(
        category=CriterionCategory.EDUCATION,
        value="Bachelor's degree",
        evidence="Bachelor's degree required.",
    )

    assert criterion.education_requirement is None


def test_normal_job_criterion_keeps_education_requirement_none() -> None:
    criterion = JobCriterion(
        category=CriterionCategory.TECHNOLOGY,
        value="Python",
        evidence="Python required.",
    )

    assert criterion.education_requirement is None


def test_education_requirement_is_rejected_for_non_education_category() -> None:
    requirement = EducationRequirement(field_of_study="Computer Science")

    with pytest.raises(DomainError, match="education criterion category"):
        JobCriterion(
            category=CriterionCategory.TECHNOLOGY,
            value="Python",
            evidence="Python required.",
            education_requirement=requirement,
        )


def test_job_criterion_rejects_invalid_education_requirement_type() -> None:
    with pytest.raises(DomainError, match="EducationRequirement"):
        JobCriterion(
            category=CriterionCategory.EDUCATION,
            value="Computer Science",
            evidence="Computer Science required.",
            education_requirement="invalid",  # type: ignore[arg-type]
        )
