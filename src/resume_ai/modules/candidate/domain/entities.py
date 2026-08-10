from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum

from resume_ai.core.exceptions import DomainError


def _require_non_empty(field_name: str, value: str) -> None:
    if not value.strip():
        raise DomainError(f"{field_name} cannot be empty")


@dataclass(frozen=True, slots=True)
class PersonalInfo:
    """Identity and location information for a candidate."""

    full_name: str
    city: str
    state: str
    country: str

    def __post_init__(self) -> None:
        for field_name, value in (
            ("full_name", self.full_name),
            ("city", self.city),
            ("state", self.state),
            ("country", self.country),
        ):
            _require_non_empty(field_name, value)


@dataclass(frozen=True, slots=True)
class ContactInfo:
    """Contact information for a candidate."""

    email: str
    phone: str

    def __post_init__(self) -> None:
        _require_non_empty("email", self.email)
        _require_non_empty("phone", self.phone)
        local_part, separator, domain = self.email.partition("@")
        if not separator or not local_part or not domain or "@" in domain:
            raise DomainError("email is invalid")


@dataclass(frozen=True, slots=True)
class ProfessionalLinks:
    """Optional professional links for a candidate."""

    linkedin: str | None = None
    github: str | None = None
    portfolio: str | None = None

    def __post_init__(self) -> None:
        for field_name, value in (
            ("linkedin", self.linkedin),
            ("github", self.github),
            ("portfolio", self.portfolio),
        ):
            if value is not None and not value.strip():
                raise DomainError(f"{field_name} cannot be empty")


@dataclass(frozen=True, slots=True)
class Activity:
    """A responsibility performed during a professional experience."""

    description: str

    def __post_init__(self) -> None:
        _require_non_empty("description", self.description)


@dataclass(frozen=True, slots=True)
class Achievement:
    """A professional result or accomplishment."""

    description: str

    def __post_init__(self) -> None:
        _require_non_empty("description", self.description)


@dataclass(frozen=True, slots=True)
class Experience:
    """A professional experience held by a candidate."""

    company: str
    role: str
    start_date: date
    end_date: date | None = None
    activities: tuple[Activity, ...] = ()
    achievements: tuple[Achievement, ...] = ()

    def __post_init__(self) -> None:
        _require_non_empty("company", self.company)
        _require_non_empty("role", self.role)

        if not isinstance(self.start_date, date):
            raise DomainError("start_date must be a date")
        if self.end_date is not None and not isinstance(self.end_date, date):
            raise DomainError("end_date must be a date or None")
        if self.end_date is not None and self.end_date < self.start_date:
            raise DomainError("end_date cannot be before start_date")

        if not isinstance(self.activities, tuple):
            raise DomainError("activities must be a tuple of Activity")
        if not all(isinstance(activity, Activity) for activity in self.activities):
            raise DomainError("activities must contain only Activity")

        if not isinstance(self.achievements, tuple):
            raise DomainError("achievements must be a tuple of Achievement")
        if not all(isinstance(achievement, Achievement) for achievement in self.achievements):
            raise DomainError("achievements must contain only Achievement")


class EducationStatus(StrEnum):
    """Stable status values for an academic education record."""

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    INTERRUPTED = "interrupted"


@dataclass(frozen=True, slots=True)
class Education:
    """An academic education record for a candidate."""

    institution: str
    course: str
    status: EducationStatus
    start_date: date | None = None
    end_date: date | None = None

    def __post_init__(self) -> None:
        _require_non_empty("institution", self.institution)
        _require_non_empty("course", self.course)

        if not isinstance(self.status, EducationStatus):
            raise DomainError("status must be an EducationStatus")
        if self.start_date is not None and not isinstance(self.start_date, date):
            raise DomainError("start_date must be a date or None")
        if self.end_date is not None and not isinstance(self.end_date, date):
            raise DomainError("end_date must be a date or None")
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise DomainError("end_date cannot be before start_date")


class ProficiencyLevel(StrEnum):
    """Self-declared proficiency levels for skills and capabilities."""

    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


def _validate_proficiency_level(level: ProficiencyLevel | None) -> None:
    if level is not None and not isinstance(level, ProficiencyLevel):
        raise DomainError("level must be a ProficiencyLevel or None")


@dataclass(frozen=True, slots=True)
class Skill:
    """A professional skill or capability."""

    name: str
    level: ProficiencyLevel | None = None

    def __post_init__(self) -> None:
        _require_non_empty("name", self.name)
        _validate_proficiency_level(self.level)


@dataclass(frozen=True, slots=True)
class Technology:
    """A technical language, framework, platform, or technology."""

    name: str
    level: ProficiencyLevel | None = None

    def __post_init__(self) -> None:
        _require_non_empty("name", self.name)
        _validate_proficiency_level(self.level)


@dataclass(frozen=True, slots=True)
class Tool:
    """A software, service, or tool used to perform work."""

    name: str
    level: ProficiencyLevel | None = None

    def __post_init__(self) -> None:
        _require_non_empty("name", self.name)
        _validate_proficiency_level(self.level)


class LanguageLevel(StrEnum):
    """Self-declared proficiency levels for languages."""

    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    FLUENT = "fluent"
    NATIVE = "native"


def _validate_language_level(level: LanguageLevel | None) -> None:
    if level is not None and not isinstance(level, LanguageLevel):
        raise DomainError("level must be a LanguageLevel or None")


@dataclass(frozen=True, slots=True)
class Language:
    """A language declared by a candidate."""

    name: str
    level: LanguageLevel | None = None

    def __post_init__(self) -> None:
        _require_non_empty("name", self.name)
        _validate_language_level(self.level)


@dataclass(frozen=True, slots=True)
class Certification:
    """A professional certification declared by a candidate."""

    name: str
    issuer: str
    issue_date: date | None = None
    expiration_date: date | None = None
    credential_id: str | None = None
    credential_url: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty("name", self.name)
        _require_non_empty("issuer", self.issuer)

        if self.issue_date is not None and not isinstance(self.issue_date, date):
            raise DomainError("issue_date must be a date or None")
        if self.expiration_date is not None and not isinstance(self.expiration_date, date):
            raise DomainError("expiration_date must be a date or None")
        if (
            self.issue_date is not None
            and self.expiration_date is not None
            and self.expiration_date < self.issue_date
        ):
            raise DomainError("expiration_date cannot be before issue_date")

        for field_name, value in (
            ("credential_id", self.credential_id),
            ("credential_url", self.credential_url),
        ):
            if value is not None:
                _require_non_empty(field_name, value)


@dataclass(frozen=True, slots=True)
class Project:
    """A professional, academic, or personal project declared by a candidate."""

    name: str
    description: str
    start_date: date | None = None
    end_date: date | None = None
    technologies: tuple[str, ...] = ()
    url: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.name, str):
            raise DomainError("name must be a string")
        if not isinstance(self.description, str):
            raise DomainError("description must be a string")
        _require_non_empty("name", self.name)
        _require_non_empty("description", self.description)

        if self.start_date is not None and not isinstance(self.start_date, date):
            raise DomainError("start_date must be a date or None")
        if self.end_date is not None and not isinstance(self.end_date, date):
            raise DomainError("end_date must be a date or None")
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise DomainError("end_date cannot be before start_date")

        if not isinstance(self.technologies, tuple):
            raise DomainError("technologies must be a tuple of strings")
        for technology in self.technologies:
            if not isinstance(technology, str):
                raise DomainError("technologies must contain only strings")
            _require_non_empty("technology", technology)

        if self.url is not None:
            if not isinstance(self.url, str):
                raise DomainError("url must be a string or None")
            _require_non_empty("url", self.url)


def _require_tuple_of(field_name: str, value: object, expected_type: type) -> None:
    if not isinstance(value, tuple):
        raise DomainError(f"{field_name} must be a tuple")
    if not all(isinstance(item, expected_type) for item in value):
        raise DomainError(f"{field_name} contains an invalid item type")


@dataclass(frozen=True, slots=True)
class Candidate:
    """Aggregate root for the candidate domain model."""

    personal_info: PersonalInfo
    contact_info: ContactInfo
    professional_links: ProfessionalLinks = field(default_factory=ProfessionalLinks)

    experiences: tuple[Experience, ...] = ()
    education: tuple[Education, ...] = ()

    skills: tuple[Skill, ...] = ()
    technologies: tuple[Technology, ...] = ()
    tools: tuple[Tool, ...] = ()

    languages: tuple[Language, ...] = ()
    certifications: tuple[Certification, ...] = ()
    projects: tuple[Project, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.personal_info, PersonalInfo):
            raise DomainError("personal_info must be a PersonalInfo")
        if not isinstance(self.contact_info, ContactInfo):
            raise DomainError("contact_info must be a ContactInfo")
        if not isinstance(self.professional_links, ProfessionalLinks):
            raise DomainError("professional_links must be a ProfessionalLinks")

        collection_types = (
            ("experiences", self.experiences, Experience),
            ("education", self.education, Education),
            ("skills", self.skills, Skill),
            ("technologies", self.technologies, Technology),
            ("tools", self.tools, Tool),
            ("languages", self.languages, Language),
            ("certifications", self.certifications, Certification),
            ("projects", self.projects, Project),
        )
        for field_name, value, expected_type in collection_types:
            _require_tuple_of(field_name, value, expected_type)
