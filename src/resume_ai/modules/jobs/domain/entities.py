from dataclasses import dataclass
from enum import StrEnum

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


class CriterionCategory(StrEnum):
    SKILL = "skill"
    TECHNOLOGY = "technology"
    TOOL = "tool"
    LANGUAGE = "language"
    EDUCATION = "education"
    EXPERIENCE = "experience"
    CERTIFICATION = "certification"
    OTHER = "other"


class CriterionImportance(StrEnum):
    REQUIRED = "required"
    PREFERRED = "preferred"
    UNSPECIFIED = "unspecified"


def _require_enum(field_name: str, value: object, expected_type: type) -> None:
    if not isinstance(value, expected_type):
        raise DomainError(f"{field_name} must be a {expected_type.__name__}")


@dataclass(frozen=True, slots=True)
class JobCriterion:
    category: CriterionCategory
    value: str
    evidence: str
    importance: CriterionImportance = CriterionImportance.UNSPECIFIED

    def __post_init__(self) -> None:
        _require_enum("category", self.category, CriterionCategory)
        _require_non_blank("value", self.value)
        _require_non_blank("evidence", self.evidence)
        _require_enum("importance", self.importance, CriterionImportance)


@dataclass(frozen=True, slots=True)
class JobCriteria:
    criteria: tuple[JobCriterion, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.criteria, tuple):
            raise DomainError("criteria must be a tuple of JobCriterion")
        if not all(isinstance(criterion, JobCriterion) for criterion in self.criteria):
            raise DomainError("criteria must contain only JobCriterion")
