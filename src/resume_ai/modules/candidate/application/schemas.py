from pydantic import BaseModel, ConfigDict, field_validator

from resume_ai.modules.candidate.domain.entities import (
    ContactInfo,
    PersonalInfo,
    ProfessionalLinks,
)


def _require_non_blank(value: str) -> str:
    if not value.strip():
        raise ValueError("must not be blank")
    return value


def _require_non_blank_if_present(value: str | None) -> str | None:
    if value is None:
        return None
    return _require_non_blank(value)


def _validate_email(value: str) -> str:
    _require_non_blank(value)
    local_part, separator, domain = value.partition("@")
    if not separator or not local_part or not domain or "@" in domain:
        raise ValueError("email is invalid")
    return value


class _InputSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class PersonalInfoInput(_InputSchema):
    full_name: str
    city: str
    state: str
    country: str

    _validate_full_name = field_validator("full_name")(_require_non_blank)
    _validate_city = field_validator("city")(_require_non_blank)
    _validate_state = field_validator("state")(_require_non_blank)
    _validate_country = field_validator("country")(_require_non_blank)

    def to_domain(self) -> PersonalInfo:
        return PersonalInfo(
            full_name=self.full_name,
            city=self.city,
            state=self.state,
            country=self.country,
        )


class ContactInfoInput(_InputSchema):
    email: str
    phone: str

    _validate_email_field = field_validator("email")(_validate_email)
    _validate_phone = field_validator("phone")(_require_non_blank)

    def to_domain(self) -> ContactInfo:
        return ContactInfo(email=self.email, phone=self.phone)


class ProfessionalLinksInput(_InputSchema):
    linkedin: str | None = None
    github: str | None = None
    portfolio: str | None = None

    _validate_linkedin = field_validator("linkedin")(_require_non_blank_if_present)
    _validate_github = field_validator("github")(_require_non_blank_if_present)
    _validate_portfolio = field_validator("portfolio")(_require_non_blank_if_present)

    def to_domain(self) -> ProfessionalLinks:
        return ProfessionalLinks(
            linkedin=self.linkedin,
            github=self.github,
            portfolio=self.portfolio,
        )
