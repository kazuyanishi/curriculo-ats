from dataclasses import dataclass

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
