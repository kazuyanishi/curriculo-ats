import pytest
from pydantic import ValidationError

from resume_ai.modules.jobs.application.schemas import (
    JobCriteriaInput,
    JobCriterionInput,
)
from resume_ai.modules.jobs.domain.entities import (
    CriterionCategory,
    CriterionImportance,
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
