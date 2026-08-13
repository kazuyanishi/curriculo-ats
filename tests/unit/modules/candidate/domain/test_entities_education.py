from dataclasses import FrozenInstanceError

import pytest

from resume_ai.core.exceptions import DomainError
from resume_ai.modules.candidate.domain.entities import Education, EducationStatus
from resume_ai.modules.candidate.domain.value_objects import YearMonth


def test_education_status_values_are_stable() -> None:
    assert EducationStatus.IN_PROGRESS.value == "in_progress"
    assert EducationStatus.COMPLETED.value == "completed"
    assert EducationStatus.INTERRUPTED.value == "interrupted"


def test_education_accepts_minimum_data() -> None:
    education = Education(
        institution="Example University",
        course="Computer Science",
        status=EducationStatus.IN_PROGRESS,
    )

    assert education.start_date is None
    assert education.end_date is None


def test_education_accepts_complete_data() -> None:
    start = YearMonth("2020-01")
    end = YearMonth("2024-01")
    education = Education(
        institution="Example University",
        course="Computer Science",
        status=EducationStatus.COMPLETED,
        start_date=start,
        end_date=end,
    )

    assert education.institution == "Example University"
    assert education.course == "Computer Science"
    assert education.status is EducationStatus.COMPLETED
    assert education.start_date == start
    assert education.end_date == end


@pytest.mark.parametrize("field", ["institution", "course"])
@pytest.mark.parametrize("value", ["", "   "])
def test_education_rejects_empty_required_text(field: str, value: str) -> None:
    values = {
        "institution": "Example University",
        "course": "Computer Science",
        "status": EducationStatus.IN_PROGRESS,
    }
    values[field] = value

    with pytest.raises(DomainError, match=f"{field} cannot be empty"):
        Education(**values)


@pytest.mark.parametrize("status", ["completed", None, object()])
def test_education_rejects_non_enum_status(status) -> None:
    with pytest.raises(DomainError, match="status must be an EducationStatus"):
        Education("Example University", "Computer Science", status)


@pytest.mark.parametrize("field", ["start_date", "end_date"])
def test_education_rejects_string_dates(field: str) -> None:
    values = {
        "institution": "Example University",
        "course": "Computer Science",
        "status": EducationStatus.IN_PROGRESS,
        field: "2024-01",
    }

    with pytest.raises(DomainError, match=f"{field} must be a YearMonth or None"):
        Education(**values)


def test_education_rejects_end_date_before_start_date() -> None:
    with pytest.raises(DomainError, match="end_date cannot be before start_date"):
        Education(
            "Example University",
            "Computer Science",
            EducationStatus.INTERRUPTED,
            YearMonth("2024-01"),
            YearMonth("2023-01"),
        )


def test_education_accepts_same_date_and_missing_dates() -> None:
    same_date = YearMonth("2024-01")

    completed = Education(
        "Example University", "Computer Science", EducationStatus.COMPLETED
    )
    in_progress = Education(
        "Example University",
        "Computer Science",
        EducationStatus.IN_PROGRESS,
        same_date,
        same_date,
    )

    assert completed.start_date is None
    assert completed.end_date is None
    assert in_progress.start_date == same_date
    assert in_progress.end_date == same_date


def test_education_is_immutable() -> None:
    education = Education("Example University", "Computer Science", EducationStatus.COMPLETED)

    with pytest.raises(FrozenInstanceError):
        education.course = "Information Systems"
