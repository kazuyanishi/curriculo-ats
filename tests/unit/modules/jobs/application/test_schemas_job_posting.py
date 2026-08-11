import pytest
from pydantic import ValidationError

from resume_ai.modules.jobs.application.schemas import JobPostingInput
from resume_ai.modules.jobs.domain.entities import JobPosting


def test_job_posting_input_accepts_required_description_only() -> None:
    schema = JobPostingInput(description="Backend developer")

    assert schema.description == "Backend developer"
    assert schema.title is None
    assert schema.to_domain() == JobPosting(description="Backend developer")


def test_job_posting_input_preserves_text_and_optional_metadata() -> None:
    schema = JobPostingInput(
        description="  Build APIs\nwith Python  ",
        title=" Senior Backend ",
        company=" Acme ",
        location=" Remote ",
        source_url="not validated here",
    )

    assert schema.to_domain().description == "  Build APIs\nwith Python  "
    assert schema.title == " Senior Backend "
    assert schema.source_url == "not validated here"


@pytest.mark.parametrize("value", ["", "   ", "\n\t", 123, None])
def test_job_posting_description_must_be_a_non_blank_string(value: object) -> None:
    with pytest.raises(ValidationError):
        JobPostingInput(description=value)


@pytest.mark.parametrize("field", ["title", "company", "location", "source_url"])
@pytest.mark.parametrize("value", ["", "   ", "\n", 123])
def test_job_posting_optional_metadata_must_be_non_blank_strings(
    field: str, value: object
) -> None:
    with pytest.raises(ValidationError):
        JobPostingInput(description="Description", **{field: value})


def test_job_posting_input_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        JobPostingInput(description="Description", unknown="value")


def test_job_posting_input_is_frozen() -> None:
    schema = JobPostingInput(description="Description")

    with pytest.raises(ValidationError):
        schema.description = "Changed"
