import pytest
from pydantic import ValidationError

from resume_ai.modules.jobs.application.schemas import (
    EducationRequirementInput,
    JobCriteriaInput,
    JobCriterionInput,
)
from resume_ai.modules.jobs.domain.entities import (
    CriterionCategory,
    CriterionImportance,
    EducationRequirement,
    EducationRequirementStatus,
    JobCriteria,
    JobCriterion,
)


def test_job_criterion_input_converts_external_enum_strings() -> None:
    schema = JobCriterionInput(
        category="technology", value="Python", evidence="Required in the stack"
    )

    assert schema.category is CriterionCategory.TECHNOLOGY
    assert schema.importance is CriterionImportance.UNSPECIFIED


def test_job_criterion_input_accepts_enum_objects_and_preserves_text() -> None:
    schema = JobCriterionInput(
        category=CriterionCategory.SKILL,
        value="  APIs  ",
        evidence="  Built production services  ",
        importance=CriterionImportance.REQUIRED,
    )

    assert schema.to_domain() == JobCriterion(
        category=CriterionCategory.SKILL,
        value="  APIs  ",
        evidence="  Built production services  ",
        importance=CriterionImportance.REQUIRED,
    )


@pytest.mark.parametrize("field", ["category", "importance"])
def test_job_criterion_input_rejects_invalid_enum_strings(field: str) -> None:
    data = {"category": "skill", "value": "Python", "evidence": "Experience"}
    data[field] = "invalid"

    with pytest.raises(ValidationError):
        JobCriterionInput(**data)


def test_job_criterion_input_rejects_cross_enum_values() -> None:
    with pytest.raises(ValidationError):
        JobCriterionInput(
            category=CriterionImportance.REQUIRED,
            value="Python",
            evidence="Experience",
        )
    with pytest.raises(ValidationError):
        JobCriterionInput(
            category=CriterionCategory.SKILL,
            value="Python",
            evidence="Experience",
            importance=CriterionCategory.TOOL,
        )


@pytest.mark.parametrize("field", ["value", "evidence"])
@pytest.mark.parametrize("value", ["", "  ", "\n\t", 42])
def test_job_criterion_text_fields_must_be_non_blank_strings(
    field: str, value: object
) -> None:
    data = {"category": "skill", "value": "Python", "evidence": "Experience"}
    data[field] = value

    with pytest.raises(ValidationError):
        JobCriterionInput(**data)


def test_job_criteria_input_defaults_to_empty_tuple() -> None:
    schema = JobCriteriaInput()

    assert schema.criteria == ()
    assert schema.to_domain() == JobCriteria()


def test_job_criteria_input_converts_list_and_dict_items_to_tuple() -> None:
    schema = JobCriteriaInput(
        criteria=[
            {"category": "skill", "value": "Python", "evidence": "Used daily"},
            {"category": "language", "value": "English", "evidence": "B2"},
        ]
    )

    assert isinstance(schema.criteria, tuple)
    assert all(isinstance(item, JobCriterionInput) for item in schema.criteria)
    assert schema.to_domain().criteria[0].value == "Python"


@pytest.mark.parametrize("criteria", [["invalid"], [1], [None]])
def test_job_criteria_input_rejects_primitive_items(criteria: object) -> None:
    with pytest.raises(ValidationError):
        JobCriteriaInput(criteria=criteria)


def test_job_criteria_input_rejects_nested_extra_fields() -> None:
    with pytest.raises(ValidationError):
        JobCriteriaInput(
            criteria=[
                {
                    "category": "skill",
                    "value": "Python",
                    "evidence": "Used daily",
                    "extra": True,
                }
            ]
        )


def test_job_criteria_input_preserves_order_and_duplicates() -> None:
    item = {"category": "skill", "value": "Python", "evidence": "Used daily"}
    schema = JobCriteriaInput(criteria=[item, item])

    domain = schema.to_domain()
    assert len(domain.criteria) == 2
    assert domain.criteria[0] == domain.criteria[1]


def test_job_criteria_input_rejects_domain_entities_as_items() -> None:
    criterion = JobCriterion(
        category=CriterionCategory.SKILL, value="Python", evidence="Used daily"
    )

    with pytest.raises(ValidationError):
        JobCriteriaInput(criteria=[criterion])


def test_education_requirement_input_converts_external_status_strings() -> None:
    schema = EducationRequirementInput(
        field_of_study="Computer Science",
        acceptable_statuses=["completed", "in_progress"],
    )

    assert schema.acceptable_statuses == (
        EducationRequirementStatus.COMPLETED,
        EducationRequirementStatus.IN_PROGRESS,
    )
    assert isinstance(schema.acceptable_statuses, tuple)


def test_education_requirement_input_converts_all_fields_to_domain() -> None:
    schema = EducationRequirementInput(
        degree_level="Bachelor's",
        field_of_study="Computer Science",
        institution="Example University",
        acceptable_statuses=["completed"],
    )

    domain = schema.to_domain()

    assert isinstance(domain, EducationRequirement)
    assert domain.degree_level == "Bachelor's"
    assert domain.field_of_study == "Computer Science"
    assert domain.institution == "Example University"
    assert domain.acceptable_statuses == (EducationRequirementStatus.COMPLETED,)


@pytest.mark.parametrize(
    "payload",
    [
        {"degree_level": "Bachelor's"},
        {"field_of_study": "Computer Science"},
        {"institution": "Example University"},
        {"acceptable_statuses": ["in_progress"]},
    ],
)
def test_education_requirement_input_accepts_each_requirement_field(
    payload: dict[str, object],
) -> None:
    assert EducationRequirementInput(**payload)


def test_education_requirement_input_rejects_empty_requirement() -> None:
    with pytest.raises(ValidationError, match="at least one requirement"):
        EducationRequirementInput()


@pytest.mark.parametrize("field", ["degree_level", "field_of_study", "institution"])
@pytest.mark.parametrize("value", ["", "   ", "\n\t"])
def test_education_requirement_input_rejects_blank_text(field: str, value: str) -> None:
    with pytest.raises(ValidationError):
        EducationRequirementInput(**{field: value})


def test_education_requirement_input_preserves_text_through_domain_conversion() -> None:
    schema = EducationRequirementInput(
        degree_level="  Bachelor's  ",
        field_of_study="  Computer Science  ",
        institution="  Example University  ",
    )

    domain = schema.to_domain()

    assert schema.degree_level == "  Bachelor's  "
    assert schema.field_of_study == "  Computer Science  "
    assert schema.institution == "  Example University  "
    assert domain.degree_level == schema.degree_level
    assert domain.field_of_study == schema.field_of_study
    assert domain.institution == schema.institution


@pytest.mark.parametrize("status", ["finished", "graduated", "studying", "invalid"])
def test_education_requirement_input_rejects_invalid_status(status: str) -> None:
    with pytest.raises(ValidationError):
        EducationRequirementInput(
            field_of_study="Computer Science",
            acceptable_statuses=[status],
        )


def test_education_requirement_input_rejects_nested_extra_fields() -> None:
    with pytest.raises(ValidationError):
        EducationRequirementInput(field_of_study="Computer Science", unknown=True)


def test_education_requirement_input_is_frozen() -> None:
    schema = EducationRequirementInput(field_of_study="Computer Science")

    with pytest.raises(ValidationError):
        schema.field_of_study = "Physics"


def test_job_criterion_input_converts_structured_education_requirement() -> None:
    schema = JobCriterionInput(
        category="education",
        value="Bachelor's degree in Computer Science",
        evidence="Bachelor's degree in Computer Science required.",
        importance="required",
        education_requirement={
            "degree_level": "Bachelor's",
            "field_of_study": "Computer Science",
            "acceptable_statuses": ["completed"],
        },
    )

    domain = schema.to_domain()

    assert isinstance(schema.education_requirement, EducationRequirementInput)
    assert isinstance(domain.education_requirement, EducationRequirement)
    assert domain.category is CriterionCategory.EDUCATION
    assert domain.education_requirement.degree_level == "Bachelor's"
    assert domain.education_requirement.field_of_study == "Computer Science"
    assert domain.education_requirement.acceptable_statuses == (
        EducationRequirementStatus.COMPLETED,
    )


def test_job_criterion_input_legacy_education_without_requirement_is_valid() -> None:
    schema = JobCriterionInput(
        category="education",
        value="Bachelor's degree",
        evidence="Bachelor's degree required.",
    )

    assert schema.education_requirement is None
    assert schema.to_domain().education_requirement is None


def test_job_criterion_input_rejects_education_requirement_in_wrong_category() -> None:
    with pytest.raises(ValidationError, match="education criterion category"):
        JobCriterionInput(
            category="technology",
            value="Python",
            evidence="Python required.",
            education_requirement={"field_of_study": "Computer Science"},
        )


def test_education_category_without_requirement_remains_valid() -> None:
    schema = JobCriterionInput(
        category=CriterionCategory.EDUCATION,
        value="Computer Science",
        evidence="Computer Science required.",
    )

    assert schema.education_requirement is None


def test_job_criteria_input_converts_structured_and_legacy_items_in_order() -> None:
    schema = JobCriteriaInput(
        criteria=[
            {
                "category": "education",
                "value": "Computer Science degree",
                "evidence": "Computer Science degree required.",
                "education_requirement": {"field_of_study": "Computer Science"},
            },
            {
                "category": "technology",
                "value": "Python",
                "evidence": "Python required.",
            },
        ]
    )

    domain = schema.to_domain()

    assert domain.criteria[0].education_requirement is not None
    assert domain.criteria[0].education_requirement.field_of_study == "Computer Science"
    assert domain.criteria[1].education_requirement is None


def test_job_criterion_input_type_hints_remain_domain_typed() -> None:
    from typing import get_type_hints

    assert (
        get_type_hints(EducationRequirementInput.to_domain)["return"]
        is EducationRequirement
    )
    assert get_type_hints(JobCriterionInput.to_domain)["return"] is JobCriterion
