from dataclasses import FrozenInstanceError

import pytest

from resume_ai.core.exceptions import DomainError
from resume_ai.modules.candidate.domain.entities import Project, Technology
from resume_ai.modules.candidate.domain.value_objects import YearMonth


def test_project_accepts_minimum_data() -> None:
    project = Project("Example ERP", "Management system for small businesses.")

    assert project.start_date is None
    assert project.end_date is None
    assert project.technologies == ()
    assert project.url is None


def test_project_accepts_complete_data_and_preserves_values() -> None:
    start_date = YearMonth("2025-01")
    end_date = YearMonth("2026-01")
    technologies = ("Python", "FastAPI", "PostgreSQL")
    url = "https://Example.com/MyProject"
    project = Project(
        "Example ERP",
        "Management system for small businesses.",
        start_date,
        end_date,
        technologies,
        url,
    )

    assert project.name == "Example ERP"
    assert project.description == "Management system for small businesses."
    assert project.start_date == start_date
    assert project.end_date == end_date
    assert project.technologies == technologies
    assert project.url == url


@pytest.mark.parametrize("field", ["name", "description"])
@pytest.mark.parametrize("value", ["", "   "])
def test_project_rejects_empty_required_text(field: str, value: str) -> None:
    values = {"name": "Example Project", "description": "Example description"}
    values[field] = value

    with pytest.raises(DomainError, match=f"{field} cannot be empty"):
        Project(**values)


@pytest.mark.parametrize("field", ["start_date", "end_date"])
def test_project_rejects_string_dates(field: str) -> None:
    values = {"name": "Example Project", "description": "Example description"}
    values[field] = "2025-01"

    with pytest.raises(DomainError, match=f"{field} must be a YearMonth or None"):
        Project(**values)


def test_project_accepts_partial_dates_and_same_date() -> None:
    start_date = YearMonth("2025-01")

    only_start = Project("Example Project", "Example description", start_date=start_date)
    only_end = Project("Example Project", "Example description", end_date=start_date)
    same_date = Project(
        "Example Project", "Example description", start_date, start_date
    )

    assert only_start.start_date == start_date
    assert only_start.end_date is None
    assert only_end.start_date is None
    assert only_end.end_date == start_date
    assert same_date.start_date == same_date.end_date == start_date


def test_project_rejects_end_date_before_start_date() -> None:
    with pytest.raises(DomainError, match="end_date cannot be before start_date"):
        Project(
            "Example Project",
            "Example description",
            YearMonth("2026-01"),
            YearMonth("2025-01"),
        )


@pytest.mark.parametrize("technologies", [["Python"], ("Python", 123), ("Python", "")])
def test_project_rejects_invalid_technologies(technologies) -> None:
    with pytest.raises(DomainError):
        Project("Example Project", "Example description", technologies=technologies)


def test_project_rejects_technology_entity() -> None:
    with pytest.raises(DomainError, match="technologies must contain only strings"):
        Project(
            "Example Project",
            "Example description",
            technologies=(Technology("Python"),),
        )


def test_project_preserves_technology_order_and_format() -> None:
    technologies = ("  PostgreSQL  ", "Python", "python")
    project = Project("Example Project", "Example description", technologies=technologies)

    assert isinstance(project.technologies, tuple)
    assert project.technologies == technologies


@pytest.mark.parametrize("url", ["", "   "])
def test_project_rejects_empty_url(url: str) -> None:
    with pytest.raises(DomainError, match="url cannot be empty"):
        Project("Example Project", "Example description", url=url)


def test_project_is_immutable() -> None:
    project = Project("Example Project", "Example description")

    with pytest.raises(FrozenInstanceError):
        project.name = "Other Project"
