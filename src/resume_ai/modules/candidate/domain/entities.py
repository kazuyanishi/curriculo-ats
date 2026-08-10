from dataclasses import dataclass
from datetime import date

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
