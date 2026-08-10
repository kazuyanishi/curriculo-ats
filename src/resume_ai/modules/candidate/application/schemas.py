from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from resume_ai.modules.candidate.domain.entities import (
    Achievement,
    Activity,
    ContactInfo,
    Education,
    EducationStatus,
    Experience,
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


def _parse_date_input(value: object) -> date:
    if isinstance(value, datetime):
        raise ValueError("datetime is not accepted; use a date")
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        raise ValueError("date must be a date or YYYY-MM-DD string")
    if len(value) != 10 or value[4] != "-" or value[7] != "-":
        raise ValueError("date must use YYYY-MM-DD format")
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError("date must use YYYY-MM-DD format") from error


def _parse_optional_date_input(value: object) -> date | None:
    if value is None:
        return None
    return _parse_date_input(value)


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


class ActivityInput(_InputSchema):
    description: str

    _validate_description = field_validator("description")(_require_non_blank)

    def to_domain(self) -> Activity:
        return Activity(description=self.description)


class AchievementInput(_InputSchema):
    description: str

    _validate_description = field_validator("description")(_require_non_blank)

    def to_domain(self) -> Achievement:
        return Achievement(description=self.description)


class ExperienceInput(_InputSchema):
    company: str
    role: str
    start_date: date
    end_date: date | None = None
    activities: tuple[ActivityInput, ...] = ()
    achievements: tuple[AchievementInput, ...] = ()

    _validate_company = field_validator("company")(_require_non_blank)
    _validate_role = field_validator("role")(_require_non_blank)
    _parse_start_date = field_validator("start_date", mode="before")(_parse_date_input)
    _parse_end_date = field_validator("end_date", mode="before")(_parse_optional_date_input)

    @model_validator(mode="after")
    def _validate_date_order(self) -> "ExperienceInput":
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date")
        return self

    def to_domain(self) -> Experience:
        return Experience(
            company=self.company,
            role=self.role,
            start_date=self.start_date,
            end_date=self.end_date,
            activities=tuple(activity.to_domain() for activity in self.activities),
            achievements=tuple(achievement.to_domain() for achievement in self.achievements),
        )


class EducationInput(_InputSchema):
    institution: str
    course: str
    status: EducationStatus
    start_date: date | None = None
    end_date: date | None = None

    _validate_institution = field_validator("institution")(_require_non_blank)
    _validate_course = field_validator("course")(_require_non_blank)
    _parse_start_date = field_validator("start_date", mode="before")(_parse_optional_date_input)
    _parse_end_date = field_validator("end_date", mode="before")(_parse_optional_date_input)

    @model_validator(mode="after")
    def _validate_date_order(self) -> "EducationInput":
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("end_date cannot be before start_date")
        return self

    def to_domain(self) -> Education:
        return Education(
            institution=self.institution,
            course=self.course,
            status=self.status,
            start_date=self.start_date,
            end_date=self.end_date,
        )
