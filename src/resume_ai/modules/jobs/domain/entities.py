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


class EducationRequirementStatus(StrEnum):
    COMPLETED = "completed"
    IN_PROGRESS = "in_progress"


def _require_enum(field_name: str, value: object, expected_type: type) -> None:
    if not isinstance(value, expected_type):
        raise DomainError(f"{field_name} must be a {expected_type.__name__}")


@dataclass(frozen=True, slots=True)
class EducationRequirementStatusEvidence:
    status: EducationRequirementStatus
    evidence: str

    def __post_init__(self) -> None:
        _require_enum("status", self.status, EducationRequirementStatus)
        _require_non_blank("evidence", self.evidence)


@dataclass(frozen=True, slots=True)
class EducationRequirement:
    degree_level: str | None = None
    field_of_study: str | None = None
    institution: str | None = None
    acceptable_statuses: tuple[EducationRequirementStatus, ...] = ()
    status_evidence: tuple[EducationRequirementStatusEvidence, ...] = ()

    def __post_init__(self) -> None:
        for field_name, value in (
            ("degree_level", self.degree_level),
            ("field_of_study", self.field_of_study),
            ("institution", self.institution),
        ):
            if value is not None:
                _require_non_blank(field_name, value)

        if not isinstance(self.acceptable_statuses, tuple):
            raise DomainError("acceptable_statuses must be a tuple")
        if not all(
            isinstance(status, EducationRequirementStatus)
            for status in self.acceptable_statuses
        ):
            raise DomainError(
                "acceptable_statuses must contain only EducationRequirementStatus"
            )
        if not isinstance(self.status_evidence, tuple):
            raise DomainError("status_evidence must be a tuple")
        if not all(
            isinstance(item, EducationRequirementStatusEvidence)
            for item in self.status_evidence
        ):
            raise DomainError(
                "status_evidence must contain only EducationRequirementStatusEvidence"
            )
        if any(item.status not in self.acceptable_statuses for item in self.status_evidence):
            raise DomainError(
                "status_evidence status must be an acceptable education status"
            )
        if (
            self.degree_level is None
            and self.field_of_study is None
            and self.institution is None
            and not self.acceptable_statuses
        ):
            raise DomainError("education requirement must define at least one requirement")


@dataclass(frozen=True, slots=True)
class JobCriterion:
    category: CriterionCategory
    value: str
    evidence: str
    importance: CriterionImportance = CriterionImportance.UNSPECIFIED
    education_requirement: EducationRequirement | None = None

    def __post_init__(self) -> None:
        _require_enum("category", self.category, CriterionCategory)
        _require_non_blank("value", self.value)
        _require_non_blank("evidence", self.evidence)
        _require_enum("importance", self.importance, CriterionImportance)
        if self.education_requirement is not None:
            if not isinstance(self.education_requirement, EducationRequirement):
                raise DomainError("education_requirement must be an EducationRequirement")
            if self.category is not CriterionCategory.EDUCATION:
                raise DomainError(
                    "education_requirement requires education criterion category"
                )


@dataclass(frozen=True, slots=True)
class JobCriteria:
    criteria: tuple[JobCriterion, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.criteria, tuple):
            raise DomainError("criteria must be a tuple of JobCriterion")
        if not all(isinstance(criterion, JobCriterion) for criterion in self.criteria):
            raise DomainError("criteria must contain only JobCriterion")
