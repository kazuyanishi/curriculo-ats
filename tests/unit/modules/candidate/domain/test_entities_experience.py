from dataclasses import FrozenInstanceError

import pytest

from resume_ai.core.exceptions import DomainError
from resume_ai.modules.candidate.domain.entities import (
    Achievement,
    Activity,
    Experience,
)
from resume_ai.modules.candidate.domain.value_objects import YearMonth


@pytest.mark.parametrize("entity_type", [Activity, Achievement])
def test_activity_and_achievement_preserve_valid_description(entity_type) -> None:
    entity = entity_type("Implemented a new customer onboarding workflow")

    assert entity.description == "Implemented a new customer onboarding workflow"


@pytest.mark.parametrize("entity_type", [Activity, Achievement])
@pytest.mark.parametrize("description", ["", "   "])
def test_activity_and_achievement_reject_empty_description(entity_type, description: str) -> None:
    with pytest.raises(DomainError, match="description cannot be empty"):
        entity_type(description)


def test_experience_accepts_minimum_data_and_current_employment() -> None:
    experience = Experience(
        company="Example Systems",
        role="Support Analyst",
        start_date=YearMonth("2024-10"),
    )

    assert experience.end_date is None
    assert experience.activities == ()
    assert experience.achievements == ()


def test_experience_accepts_complete_data() -> None:
    activities = (
        Activity("Provided ERP technical support"),
        Activity("Documented recurring support procedures"),
    )
    achievements = (Achievement("Implemented a customer onboarding workflow"),)
    experience = Experience(
        company="Example Systems",
        role="Support Analyst",
        start_date=YearMonth("2024-10"),
        end_date=YearMonth("2025-10"),
        activities=activities,
        achievements=achievements,
    )

    assert experience.activities == activities
    assert experience.achievements == achievements
    assert isinstance(experience.activities, tuple)
    assert isinstance(experience.achievements, tuple)


@pytest.mark.parametrize("field", ["company", "role"])
@pytest.mark.parametrize("value", ["", "   "])
def test_experience_rejects_empty_company_or_role(field: str, value: str) -> None:
    values = {
        "company": "Example Systems",
        "role": "Support Analyst",
        "start_date": YearMonth("2024-10"),
    }
    values[field] = value

    with pytest.raises(DomainError, match=f"{field} cannot be empty"):
        Experience(**values)


@pytest.mark.parametrize("start_date", [None, "2024-10"])
def test_experience_rejects_invalid_start_date(start_date) -> None:
    with pytest.raises(DomainError, match="start_date must be a YearMonth"):
        Experience("Example Systems", "Support Analyst", start_date)


def test_experience_rejects_invalid_end_date() -> None:
    with pytest.raises(DomainError, match="end_date must be a YearMonth or None"):
        Experience("Example Systems", "Support Analyst", YearMonth("2024-10"), "2025-01")


def test_experience_rejects_end_date_before_start_date() -> None:
    with pytest.raises(DomainError, match="end_date cannot be before start_date"):
        Experience(
            "Example Systems",
            "Support Analyst",
            YearMonth("2025-01"),
            YearMonth("2024-12"),
        )


def test_experience_accepts_same_start_and_end_date() -> None:
    same_date = YearMonth("2025-01")

    experience = Experience("Example Systems", "Support Analyst", same_date, same_date)

    assert experience.start_date == experience.end_date == same_date


@pytest.mark.parametrize("activities", [[Activity("Support users")], ("Support users",)])
def test_experience_rejects_invalid_activities_collection(activities) -> None:
    with pytest.raises(DomainError):
        Experience(
            "Example Systems", "Support Analyst", YearMonth("2024-10"), activities=activities
        )


@pytest.mark.parametrize(
    "achievements", [[Achievement("Improved onboarding")], ("Improved onboarding",)]
)
def test_experience_rejects_invalid_achievements_collection(achievements) -> None:
    with pytest.raises(DomainError):
        Experience(
            "Example Systems",
            "Support Analyst",
            YearMonth("2024-10"),
            achievements=achievements,
        )


def test_experience_is_immutable() -> None:
    experience = Experience("Example Systems", "Support Analyst", YearMonth("2024-10"))

    with pytest.raises(FrozenInstanceError):
        experience.company = "Other Systems"
