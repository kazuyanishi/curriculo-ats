from dataclasses import FrozenInstanceError
from enum import StrEnum

import pytest

from resume_ai.core.exceptions import DomainError
from resume_ai.modules.jobs.domain.entities import (
    CriterionCategory,
    CriterionImportance,
    JobCriteria,
    JobCriterion,
)


def test_criterion_enums_have_exact_values() -> None:
    assert [item.value for item in CriterionCategory] == [
        "skill",
        "technology",
        "tool",
        "language",
        "education",
        "experience",
        "certification",
        "other",
    ]
    assert [item.value for item in CriterionImportance] == [
        "required",
        "preferred",
        "unspecified",
    ]
    assert issubclass(CriterionCategory, StrEnum)
    assert issubclass(CriterionImportance, StrEnum)


def test_job_criterion_accepts_minimum_and_defaults_importance() -> None:
    criterion = JobCriterion(
        category=CriterionCategory.TECHNOLOGY,
        value="Python",
        evidence="Python",
    )

    assert criterion.importance is CriterionImportance.UNSPECIFIED


def test_job_criterion_accepts_complete_data() -> None:
    criterion = JobCriterion(
        category=CriterionCategory.SKILL,
        value="  PostgreSQL  ",
        evidence="  Requirements:\n- PostgreSQL  ",
        importance=CriterionImportance.REQUIRED,
    )

    assert criterion.value == "  PostgreSQL  "
    assert criterion.evidence == "  Requirements:\n- PostgreSQL  "
    assert criterion.importance is CriterionImportance.REQUIRED


@pytest.mark.parametrize("field", ["value", "evidence"])
@pytest.mark.parametrize("value", [None, 123, [], {}, "", "   ", "\n\t"])
def test_job_criterion_rejects_invalid_text(field: str, value: object) -> None:
    data = {
        "category": CriterionCategory.TECHNOLOGY,
        "value": "Python",
        "evidence": "Python required",
    }
    data[field] = value

    with pytest.raises(DomainError):
        JobCriterion(**data)


def test_job_criterion_rejects_raw_enum_strings() -> None:
    with pytest.raises(DomainError):
        JobCriterion(category="technology", value="Python", evidence="Python")

    with pytest.raises(DomainError):
        JobCriterion(
            category=CriterionCategory.TECHNOLOGY,
            value="Python",
            evidence="Python",
            importance="required",
        )


def test_job_criterion_rejects_crossed_enums() -> None:
    with pytest.raises(DomainError):
        JobCriterion(
            category=CriterionImportance.REQUIRED,
            value="Python",
            evidence="Python",
        )

    with pytest.raises(DomainError):
        JobCriterion(
            category=CriterionCategory.TECHNOLOGY,
            value="Python",
            evidence="Python",
            importance=CriterionCategory.SKILL,
        )


def test_job_criteria_accepts_empty_tuple() -> None:
    assert JobCriteria().criteria == ()


def test_job_criteria_accepts_tuple_and_preserves_order_and_duplicates() -> None:
    first = JobCriterion(CriterionCategory.TECHNOLOGY, "Python", "First")
    second = JobCriterion(CriterionCategory.SKILL, "Python", "Second")
    criteria = JobCriteria(criteria=(first, second, first))

    assert criteria.criteria == (first, second, first)


def test_job_criteria_rejects_list_and_invalid_items() -> None:
    criterion = JobCriterion(CriterionCategory.TECHNOLOGY, "Python", "Python")

    with pytest.raises(DomainError):
        JobCriteria(criteria=[criterion])

    with pytest.raises(DomainError):
        JobCriteria(criteria=("Python",))


def test_job_criteria_is_frozen_and_slotted() -> None:
    criteria = JobCriteria()

    with pytest.raises(FrozenInstanceError):
        criteria.criteria = ()

    assert not hasattr(criteria, "__dict__")
