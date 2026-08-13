
import pytest
from pydantic import ValidationError

from resume_ai.modules.candidate.application.schemas import EducationInput
from resume_ai.modules.candidate.domain.entities import Education, EducationStatus
from resume_ai.modules.candidate.domain.value_objects import YearMonth


@pytest.mark.parametrize("status", ["in_progress", "completed", "interrupted"])
def test_education_accepts_status_strings(status: str) -> None:
    schema = EducationInput(
        institution="Example University",
        course="Computer Science",
        status=status,
    )

    assert schema.status is EducationStatus(status)


def test_education_accepts_status_enum() -> None:
    schema = EducationInput(
        institution="Example University",
        course="Computer Science",
        status=EducationStatus.COMPLETED,
    )

    assert schema.status is EducationStatus.COMPLETED


@pytest.mark.parametrize("status", ["graduated", "finished", "studying", ""])
def test_education_rejects_invalid_status(status: str) -> None:
    with pytest.raises(ValidationError):
        EducationInput(institution="Example University", course="Computer Science", status=status)


def test_education_accepts_string_dates_and_converts_to_domain() -> None:
    schema = EducationInput(
        institution="Example University",
        course="Computer Science",
        status="completed",
        start_date="2020-01",
        end_date="2024-01",
    )
    domain = schema.to_domain()

    assert isinstance(domain, Education)
    assert domain.status is EducationStatus.COMPLETED
    assert domain.start_date == YearMonth("2020-01")
    assert domain.end_date == YearMonth("2024-01")


def test_education_allows_missing_dates_and_completed_without_end() -> None:
    schema = EducationInput(
        institution="Example University",
        course="Computer Science",
        status="completed",
    )

    assert schema.start_date is None
    assert schema.end_date is None


def test_education_allows_in_progress_with_end_date() -> None:
    schema = EducationInput(
        institution="Example University",
        course="Computer Science",
        status="in_progress",
        end_date="2026-01",
    )

    assert schema.end_date == YearMonth("2026-01")


@pytest.mark.parametrize("field", ["institution", "course"])
@pytest.mark.parametrize("value", ["", "   "])
def test_education_rejects_blank_text(field: str, value: str) -> None:
    values = {
        "institution": "Example University",
        "course": "Computer Science",
        "status": "completed",
    }
    values[field] = value

    with pytest.raises(ValidationError):
        EducationInput(**values)


def test_education_rejects_end_date_before_start_date() -> None:
    with pytest.raises(ValidationError):
        EducationInput(
            institution="Example University",
            course="Computer Science",
            status="completed",
            start_date="2024-01",
            end_date="2023-12",
        )


def test_education_allows_same_date() -> None:
    schema = EducationInput(
        institution="Example University",
        course="Computer Science",
        status="completed",
        start_date="2024-01",
        end_date="2024-01",
    )

    assert schema.start_date == schema.end_date
