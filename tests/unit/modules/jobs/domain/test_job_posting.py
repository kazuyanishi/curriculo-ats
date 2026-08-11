from dataclasses import FrozenInstanceError, fields

import pytest

from resume_ai.core.exceptions import DomainError
from resume_ai.modules.jobs.domain.entities import JobPosting


def test_job_posting_accepts_minimum_data() -> None:
    job = JobPosting(description="Example job description")

    assert job.description == "Example job description"
    assert job.title is None
    assert job.company is None
    assert job.location is None
    assert job.source_url is None


def test_job_posting_accepts_complete_data() -> None:
    job = JobPosting(
        description="Example description",
        title="Software Engineer",
        company="Example Systems",
        location="Curitiba, PR",
        source_url="https://example.com/jobs/123",
    )

    assert job.title == "Software Engineer"
    assert job.company == "Example Systems"
    assert job.location == "Curitiba, PR"
    assert job.source_url == "https://example.com/jobs/123"


@pytest.mark.parametrize("value", [None, 123, [], {}])
def test_job_posting_rejects_non_string_description(value: object) -> None:
    with pytest.raises(DomainError):
        JobPosting(description=value)


@pytest.mark.parametrize("value", ["", "   ", "\n", "\t", " \n\t "])
def test_job_posting_rejects_blank_description(value: str) -> None:
    with pytest.raises(DomainError):
        JobPosting(description=value)


@pytest.mark.parametrize("field", ["title", "company", "location", "source_url"])
def test_job_posting_accepts_explicit_none_for_optional_fields(field: str) -> None:
    job = JobPosting(description="Example", **{field: None})

    assert getattr(job, field) is None


@pytest.mark.parametrize("field", ["title", "company", "location", "source_url"])
def test_job_posting_rejects_non_string_optional_fields(field: str) -> None:
    with pytest.raises(DomainError):
        JobPosting(description="Example", **{field: 123})


@pytest.mark.parametrize("field", ["title", "company", "location", "source_url"])
@pytest.mark.parametrize("value", ["", "   "])
def test_job_posting_rejects_blank_optional_fields(field: str, value: str) -> None:
    with pytest.raises(DomainError):
        JobPosting(description="Example", **{field: value})


def test_job_posting_preserves_text_and_line_breaks_exactly() -> None:
    description = (
        "  Senior Python Developer\n"
        "\n"
        "Requirements:\n"
        "- Python\n"
        "- PostgreSQL  "
    )
    job = JobPosting(
        description=description,
        title="  Senior Developer  ",
        company="  Example Systems  ",
        location="  Curitiba, PR  ",
        source_url="  internal-job-reference  ",
    )

    assert job.description == description
    assert job.title == "  Senior Developer  "
    assert job.company == "  Example Systems  "
    assert job.location == "  Curitiba, PR  "
    assert job.source_url == "  internal-job-reference  "


def test_job_posting_does_not_validate_url_deeply() -> None:
    job = JobPosting(description="Example", source_url="internal-job-reference")

    assert job.source_url == "internal-job-reference"


def test_job_posting_is_frozen_and_slotted() -> None:
    job = JobPosting(description="Example")

    with pytest.raises(FrozenInstanceError):
        job.description = "Other"

    assert not hasattr(job, "__dict__")
    assert [field.name for field in fields(JobPosting)] == [
        "description",
        "title",
        "company",
        "location",
        "source_url",
    ]
