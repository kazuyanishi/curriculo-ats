from pydantic import BaseModel, ConfigDict, Field, field_validator


def _require_non_blank(value: str) -> str:
    if not value.strip():
        raise ValueError("must not be blank")
    return value


class _ImportSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ResumeFieldEvidence(_ImportSchema):
    value: str
    evidence: str

    _validate_value = field_validator("value")(_require_non_blank)
    _validate_evidence = field_validator("evidence")(_require_non_blank)


class ExtractedPersonalInfo(_ImportSchema):
    full_name: ResumeFieldEvidence | None = None
    city: ResumeFieldEvidence | None = None
    state: ResumeFieldEvidence | None = None
    country: ResumeFieldEvidence | None = None


class ExtractedContactInfo(_ImportSchema):
    email: ResumeFieldEvidence | None = None
    phone: ResumeFieldEvidence | None = None


class ExtractedProfessionalLinks(_ImportSchema):
    linkedin: ResumeFieldEvidence | None = None
    github: ResumeFieldEvidence | None = None
    portfolio: ResumeFieldEvidence | None = None


class ExtractedExperience(_ImportSchema):
    company: ResumeFieldEvidence | None = None
    role: ResumeFieldEvidence | None = None
    start_date: ResumeFieldEvidence | None = None
    end_date: ResumeFieldEvidence | None = None
    activities: tuple[ResumeFieldEvidence, ...] = ()
    achievements: tuple[ResumeFieldEvidence, ...] = ()


class ExtractedEducation(_ImportSchema):
    institution: ResumeFieldEvidence | None = None
    course: ResumeFieldEvidence | None = None
    status: ResumeFieldEvidence | None = None
    start_date: ResumeFieldEvidence | None = None
    end_date: ResumeFieldEvidence | None = None


class ExtractedNamedItem(_ImportSchema):
    name: ResumeFieldEvidence
    level: ResumeFieldEvidence | None = None


class ExtractedLanguage(_ImportSchema):
    name: ResumeFieldEvidence
    level: ResumeFieldEvidence | None = None


class ExtractedCertification(_ImportSchema):
    name: ResumeFieldEvidence | None = None
    issuer: ResumeFieldEvidence | None = None
    issue_date: ResumeFieldEvidence | None = None
    expiration_date: ResumeFieldEvidence | None = None
    credential_id: ResumeFieldEvidence | None = None
    credential_url: ResumeFieldEvidence | None = None


class ExtractedProject(_ImportSchema):
    name: ResumeFieldEvidence | None = None
    description: ResumeFieldEvidence | None = None
    start_date: ResumeFieldEvidence | None = None
    end_date: ResumeFieldEvidence | None = None
    technologies: tuple[ResumeFieldEvidence, ...] = ()
    url: ResumeFieldEvidence | None = None


class CandidateResumeExtraction(_ImportSchema):
    personal_info: ExtractedPersonalInfo = Field(default_factory=ExtractedPersonalInfo)
    contact_info: ExtractedContactInfo = Field(default_factory=ExtractedContactInfo)
    professional_links: ExtractedProfessionalLinks = Field(
        default_factory=ExtractedProfessionalLinks
    )
    experiences: tuple[ExtractedExperience, ...] = ()
    education: tuple[ExtractedEducation, ...] = ()
    skills: tuple[ExtractedNamedItem, ...] = ()
    technologies: tuple[ExtractedNamedItem, ...] = ()
    tools: tuple[ExtractedNamedItem, ...] = ()
    languages: tuple[ExtractedLanguage, ...] = ()
    certifications: tuple[ExtractedCertification, ...] = ()
    projects: tuple[ExtractedProject, ...] = ()
