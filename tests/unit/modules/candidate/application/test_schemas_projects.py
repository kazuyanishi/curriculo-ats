from datetime import date, datetime

import pytest
from pydantic import ValidationError

from resume_ai.modules.candidate.application.schemas import ProjectInput
from resume_ai.modules.candidate.domain.entities import Project, Technology


def test_project_minimum_defaults_optional_fields() -> None:
    schema = ProjectInput(name="Example Project", description="Example description")

    assert schema.start_date is None
    assert schema.end_date is None
    assert schema.technologies == ()
    assert schema.url is None


def test_project_accepts_external_technology_list_and_preserves_stack() -> None:
    stack = ["  PostgreSQL  ", "Python", "python"]
    schema = ProjectInput(
        name="Example Project",
        description="Example description",
        start_date="2024-01-01",
        end_date="2025-01-01",
        technologies=stack,
        url="https://Example.com/MyProject",
    )
    domain = schema.to_domain()

    assert schema.technologies == tuple(stack)
    assert isinstance(domain, Project)
    assert domain.technologies == tuple(stack)
    assert domain.start_date == date(2024, 1, 1)
    assert domain.end_date == date(2025, 1, 1)
    assert domain.url == "https://Example.com/MyProject"


@pytest.mark.parametrize("field", ["name", "description"])
@pytest.mark.parametrize("value", ["", "   "])
def test_project_rejects_blank_required_text(field: str, value: str) -> None:
    values = {"name": "Project", "description": "Description"}
    values[field] = value

    with pytest.raises(ValidationError):
        ProjectInput(**values)


@pytest.mark.parametrize(
    "value",
    ["2025-01", "01/2025", "20250101", 123, datetime(2025, 1, 1)],
)
def test_project_rejects_invalid_dates(value) -> None:
    with pytest.raises(ValidationError):
        ProjectInput(name="Project", description="Description", start_date=value)


def test_project_rejects_end_date_before_start_date() -> None:
    with pytest.raises(ValidationError):
        ProjectInput(
            name="Project",
            description="Description",
            start_date="2025-01-02",
            end_date="2025-01-01",
        )


@pytest.mark.parametrize("value", [123, None, "", "   ", {}, []])
def test_project_rejects_invalid_technology_items(value) -> None:
    with pytest.raises(ValidationError):
        ProjectInput(name="Project", description="Description", technologies=[value])


def test_project_rejects_technology_entity_items() -> None:
    with pytest.raises(ValidationError):
        ProjectInput(
            name="Project",
            description="Description",
            technologies=[Technology("Python")],
        )


def test_project_rejects_blank_url_and_accepts_explicit_none() -> None:
    assert ProjectInput(name="Project", description="Description", url=None).url is None

    with pytest.raises(ValidationError):
        ProjectInput(name="Project", description="Description", url="   ")


def test_project_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        ProjectInput(name="Project", description="Description", score=100)
