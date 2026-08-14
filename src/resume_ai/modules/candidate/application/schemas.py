from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from resume_ai.modules.candidate.domain.entities import (
    Achievement,
    Activity,
    Candidate,
    Certification,
    ContactInfo,
    Education,
    EducationStatus,
    Experience,
    Language,
    LanguageLevel,
    PersonalInfo,
    ProfessionalLinks,
    ProficiencyLevel,
    Project,
    Skill,
    Technology,
    Tool,
    YearMonth,
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


def _parse_year_month_input(value: object) -> YearMonth:
    if isinstance(value, YearMonth):
        return value
    if not isinstance(value, str):
        raise ValueError("date must use YYYY-MM format")
    try:
        return YearMonth(value)
    except Exception as error:
        raise ValueError("date must use YYYY-MM format") from error


def _parse_optional_year_month_input(value: object) -> YearMonth | None:
    if value is None:
        return None
    return _parse_year_month_input(value)


def _reject_language_level_for_proficiency(value: object) -> object:
    if isinstance(value, LanguageLevel):
        raise ValueError("language level is not a proficiency level")
    return value


def _reject_proficiency_level_for_language(value: object) -> object:
    if isinstance(value, ProficiencyLevel):
        raise ValueError("proficiency level is not a language level")
    return value


def _validate_non_blank_string_tuple(value: tuple[str, ...]) -> tuple[str, ...]:
    for item in value:
        if not isinstance(item, str):
            raise ValueError("items must be non-blank strings")
        _require_non_blank(item)
    return value


def _validate_email(value: str) -> str:
    _require_non_blank(value)
    local_part, separator, domain = value.partition("@")
    if not separator or not local_part or not domain or "@" in domain:
        raise ValueError("email is invalid")
    return value


class _InputSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        json_encoders={YearMonth: str},
    )


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
    start_date: YearMonth
    end_date: YearMonth | None = None
    activities: tuple[ActivityInput, ...] = ()
    achievements: tuple[AchievementInput, ...] = ()

    _validate_company = field_validator("company")(_require_non_blank)
    _validate_role = field_validator("role")(_require_non_blank)
    _parse_start_date = field_validator("start_date", mode="before")(_parse_year_month_input)
    _parse_end_date = field_validator("end_date", mode="before")(_parse_optional_year_month_input)

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
    start_date: YearMonth | None = None
    end_date: YearMonth | None = None

    _validate_institution = field_validator("institution")(_require_non_blank)
    _validate_course = field_validator("course")(_require_non_blank)
    _parse_start_date = field_validator("start_date", mode="before")(
        _parse_optional_year_month_input
    )
    _parse_end_date = field_validator("end_date", mode="before")(
        _parse_optional_year_month_input
    )

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


class SkillInput(_InputSchema):
    name: str
    level: ProficiencyLevel | None = None

    _validate_name = field_validator("name")(_require_non_blank)
    _validate_level_boundary = field_validator("level", mode="before")(
        _reject_language_level_for_proficiency
    )

    def to_domain(self) -> Skill:
        return Skill(name=self.name, level=self.level)


class TechnologyInput(_InputSchema):
    name: str
    level: ProficiencyLevel | None = None

    _validate_name = field_validator("name")(_require_non_blank)
    _validate_level_boundary = field_validator("level", mode="before")(
        _reject_language_level_for_proficiency
    )

    def to_domain(self) -> Technology:
        return Technology(name=self.name, level=self.level)


class ToolInput(_InputSchema):
    name: str
    level: ProficiencyLevel | None = None

    _validate_name = field_validator("name")(_require_non_blank)
    _validate_level_boundary = field_validator("level", mode="before")(
        _reject_language_level_for_proficiency
    )

    def to_domain(self) -> Tool:
        return Tool(name=self.name, level=self.level)


class LanguageInput(_InputSchema):
    name: str
    level: LanguageLevel | None = None

    _validate_name = field_validator("name")(_require_non_blank)
    _validate_level_boundary = field_validator("level", mode="before")(
        _reject_proficiency_level_for_language
    )

    def to_domain(self) -> Language:
        return Language(name=self.name, level=self.level)


class CertificationInput(_InputSchema):
    name: str
    issuer: str
    issue_date: date | None = None
    expiration_date: date | None = None
    credential_id: str | None = None
    credential_url: str | None = None

    _validate_name = field_validator("name")(_require_non_blank)
    _validate_issuer = field_validator("issuer")(_require_non_blank)
    _parse_issue_date = field_validator("issue_date", mode="before")(
        _parse_optional_date_input
    )
    _parse_expiration_date = field_validator("expiration_date", mode="before")(
        _parse_optional_date_input
    )
    _validate_credential_id = field_validator("credential_id")(
        _require_non_blank_if_present
    )
    _validate_credential_url = field_validator("credential_url")(
        _require_non_blank_if_present
    )

    @model_validator(mode="after")
    def _validate_date_order(self) -> "CertificationInput":
        if (
            self.issue_date is not None
            and self.expiration_date is not None
            and self.expiration_date < self.issue_date
        ):
            raise ValueError("expiration_date cannot be before issue_date")
        return self

    def to_domain(self) -> Certification:
        return Certification(
            name=self.name,
            issuer=self.issuer,
            issue_date=self.issue_date,
            expiration_date=self.expiration_date,
            credential_id=self.credential_id,
            credential_url=self.credential_url,
        )


class ProjectInput(_InputSchema):
    name: str
    description: str
    start_date: YearMonth | None = None
    end_date: YearMonth | None = None
    technologies: tuple[str, ...] = ()
    url: str | None = None

    _validate_name = field_validator("name")(_require_non_blank)
    _validate_description = field_validator("description")(_require_non_blank)
    _parse_start_date = field_validator("start_date", mode="before")(
        _parse_optional_year_month_input
    )
    _parse_end_date = field_validator("end_date", mode="before")(
        _parse_optional_year_month_input
    )
    _validate_technologies = field_validator("technologies")(
        _validate_non_blank_string_tuple
    )
    _validate_url = field_validator("url")(_require_non_blank_if_present)

    @model_validator(mode="after")
    def _validate_date_order(self) -> "ProjectInput":
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("end_date cannot be before start_date")
        return self

    def to_domain(self) -> Project:
        return Project(
            name=self.name,
            description=self.description,
            start_date=self.start_date,
            end_date=self.end_date,
            technologies=self.technologies,
            url=self.url,
        )


class CandidateInput(_InputSchema):
    personal_info: PersonalInfoInput
    contact_info: ContactInfoInput
    professional_links: ProfessionalLinksInput = Field(
        default_factory=ProfessionalLinksInput
    )

    experiences: tuple[ExperienceInput, ...] = ()
    education: tuple[EducationInput, ...] = ()

    skills: tuple[SkillInput, ...] = ()
    technologies: tuple[TechnologyInput, ...] = ()
    tools: tuple[ToolInput, ...] = ()

    languages: tuple[LanguageInput, ...] = ()
    certifications: tuple[CertificationInput, ...] = ()
    projects: tuple[ProjectInput, ...] = ()

    def to_domain(self) -> Candidate:
        return Candidate(
            personal_info=self.personal_info.to_domain(),
            contact_info=self.contact_info.to_domain(),
            professional_links=self.professional_links.to_domain(),
            experiences=tuple(item.to_domain() for item in self.experiences),
            education=tuple(item.to_domain() for item in self.education),
            skills=tuple(item.to_domain() for item in self.skills),
            technologies=tuple(item.to_domain() for item in self.technologies),
            tools=tuple(item.to_domain() for item in self.tools),
            languages=tuple(item.to_domain() for item in self.languages),
            certifications=tuple(item.to_domain() for item in self.certifications),
            projects=tuple(item.to_domain() for item in self.projects),
        )
