from datetime import date, datetime

import pytest
from pydantic import ValidationError

from resume_ai.modules.candidate.application.schemas import (
    AchievementInput,
    ActivityInput,
    ExperienceInput,
)
from resume_ai.modules.candidate.domain.entities import Achievement, Activity


@pytest.mark.parametrize("schema_type", [ActivityInput, AchievementInput])
def test_description_input_accepts_valid_text_and_converts_to_domain(schema_type) -> None:
    schema = schema_type(description="  Provided ERP support  ")
    domain = schema.to_domain()

    assert isinstance(domain, (Activity, Achievement))
    assert domain.description == "  Provided ERP support  "


@pytest.mark.parametrize("schema_type", [ActivityInput, AchievementInput])
@pytest.mark.parametrize("description", ["", "   "])
def test_description_input_rejects_blank_text(schema_type, description: str) -> None:
    with pytest.raises(ValidationError):
        schema_type(description=description)


def test_nested_input_forbids_extra_fields() -> None:
    with pytest.raises(ValidationError):
        ActivityInput(description="Support", unknown="value")


def test_experience_accepts_iso_string_date_and_defaults() -> None:
    schema = ExperienceInput(
        company="Example Systems",
        role="Support Analyst",
        start_date="2024-10-01",
    )

    assert schema.start_date == date(2024, 10, 1)
    assert schema.end_date is None
    assert schema.activities == ()
    assert schema.achievements == ()


def test_experience_accepts_native_date() -> None:
    schema = ExperienceInput(
        company="Example Systems",
        role="Support Analyst",
        start_date=date(2024, 10, 1),
    )

    assert schema.start_date == date(2024, 10, 1)


@pytest.mark.parametrize(
    "value",
    ["2024-10", "10/01/2024", "20241001", "not-a-date", 0, 123, 123.45, datetime(2024, 10, 1)],
)
def test_experience_rejects_invalid_start_date(value) -> None:
    with pytest.raises(ValidationError):
        ExperienceInput(company="Example", role="Analyst", start_date=value)


@pytest.mark.parametrize("field", ["company", "role"])
@pytest.mark.parametrize("value", ["", "   "])
def test_experience_rejects_blank_text(field: str, value: str) -> None:
    values = {"company": "Example", "role": "Analyst", "start_date": "2024-10-01"}
    values[field] = value

    with pytest.raises(ValidationError):
        ExperienceInput(**values)


def test_experience_rejects_end_date_before_start_date() -> None:
    with pytest.raises(ValidationError):
        ExperienceInput(
            company="Example",
            role="Analyst",
            start_date="2024-10-02",
            end_date="2024-10-01",
        )


def test_experience_accepts_same_date() -> None:
    schema = ExperienceInput(
        company="Example",
        role="Analyst",
        start_date="2024-10-01",
        end_date="2024-10-01",
    )

    assert schema.end_date == schema.start_date


def test_experience_accepts_external_lists_as_tuples() -> None:
    schema = ExperienceInput(
        company="Example",
        role="Analyst",
        start_date="2024-10-01",
        activities=[{"description": "First"}, {"description": "Second"}],
        achievements=[{"description": "Won award"}, {"description": "Saved time"}],
    )

    assert isinstance(schema.activities, tuple)
    assert all(isinstance(item, ActivityInput) for item in schema.activities)
    assert isinstance(schema.achievements, tuple)
    assert all(isinstance(item, AchievementInput) for item in schema.achievements)

    domain = schema.to_domain()
    assert [item.description for item in domain.activities] == ["First", "Second"]
    assert [item.description for item in domain.achievements] == ["Won award", "Saved time"]
    assert all(isinstance(item, Activity) for item in domain.activities)
    assert all(isinstance(item, Achievement) for item in domain.achievements)


def test_experience_rejects_string_activity() -> None:
    with pytest.raises(ValidationError):
        ExperienceInput(
            company="Example", role="Analyst", start_date="2024-10-01", activities=["Support"]
        )


def test_experience_rejects_extra_nested_activity_field() -> None:
    with pytest.raises(ValidationError):
        ExperienceInput(
            company="Example",
            role="Analyst",
            start_date="2024-10-01",
            activities=[{"description": "Support", "score": 100}],
        )
