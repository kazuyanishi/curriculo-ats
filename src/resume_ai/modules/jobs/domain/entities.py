from dataclasses import dataclass

from resume_ai.core.exceptions import DomainError


def _require_non_blank(field_name: str, value: object) -> None:
    if not isinstance(value, str):
        raise DomainError(f"{field_name} must be a string")
    if not value.strip():
        raise DomainError(f"{field_name} cannot be empty")


def _require_optional_non_blank_string(field_name: str, value: object) -> None:
    if value is not None:
        _require_non_blank(field_name, value)


@dataclass(frozen=True, slots=True)
class JobPosting:
    description: str
    title: str | None = None
    company: str | None = None
    location: str | None = None
    source_url: str | None = None

    def __post_init__(self) -> None:
        _require_non_blank("description", self.description)
        _require_optional_non_blank_string("title", self.title)
        _require_optional_non_blank_string("company", self.company)
        _require_optional_non_blank_string("location", self.location)
        _require_optional_non_blank_string("source_url", self.source_url)
