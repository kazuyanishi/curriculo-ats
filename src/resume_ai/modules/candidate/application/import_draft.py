from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from resume_ai.modules.candidate.domain.entities import (
    EducationStatus,
    LanguageLevel,
    ProficiencyLevel,
)


class CandidateImportIssueCode(StrEnum):
    MISSING_REQUIRED_FIELD = "missing_required_field"
    UNSUPPORTED_DATE_FORMAT = "unsupported_date_format"
    UNSUPPORTED_EDUCATION_STATUS = "unsupported_education_status"
    UNSUPPORTED_PROFICIENCY_LEVEL = "unsupported_proficiency_level"
    UNSUPPORTED_LANGUAGE_LEVEL = "unsupported_language_level"


class _DraftSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class CandidateImportIssue(_DraftSchema):
    path: str
    code: CandidateImportIssueCode
    raw_value: str | None = None


class PersonalInfoDraft(_DraftSchema):
    full_name: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None


class ContactInfoDraft(_DraftSchema):
    email: str | None = None
    phone: str | None = None


class ProfessionalLinksDraft(_DraftSchema):
    linkedin: str | None = None
    github: str | None = None
    portfolio: str | None = None


class ExperienceDraft(_DraftSchema):
    company: str | None = None
    role: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    is_current: bool = False
    activities: tuple[str, ...] = ()
    achievements: tuple[str, ...] = ()


class EducationDraft(_DraftSchema):
    institution: str | None = None
    course: str | None = None
    status: EducationStatus | None = None
    start_date: str | None = None
    end_date: str | None = None


class NamedItemDraft(_DraftSchema):
    name: str
    level: ProficiencyLevel | None = None


class LanguageDraft(_DraftSchema):
    name: str
    level: LanguageLevel | None = None


class CertificationDraft(_DraftSchema):
    name: str | None = None
    issuer: str | None = None
    issue_date: str | None = None
    expiration_date: str | None = None
    credential_id: str | None = None
    credential_url: str | None = None


class ProjectDraft(_DraftSchema):
    name: str | None = None
    description: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    technologies: tuple[str, ...] = ()
    url: str | None = None


class CandidateImportDraft(_DraftSchema):
    personal_info: PersonalInfoDraft = Field(default_factory=PersonalInfoDraft)
    contact_info: ContactInfoDraft = Field(default_factory=ContactInfoDraft)
    professional_links: ProfessionalLinksDraft = Field(default_factory=ProfessionalLinksDraft)
    experiences: tuple[ExperienceDraft, ...] = ()
    education: tuple[EducationDraft, ...] = ()
    skills: tuple[NamedItemDraft, ...] = ()
    technologies: tuple[NamedItemDraft, ...] = ()
    tools: tuple[NamedItemDraft, ...] = ()
    languages: tuple[LanguageDraft, ...] = ()
    certifications: tuple[CertificationDraft, ...] = ()
    projects: tuple[ProjectDraft, ...] = ()
    issues: tuple[CandidateImportIssue, ...] = ()
