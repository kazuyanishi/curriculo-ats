from datetime import date

from resume_ai.modules.candidate.application.import_draft import (
    CandidateImportDraft,
    CandidateImportIssue,
    CandidateImportIssueCode,
    CertificationDraft,
    ContactInfoDraft,
    EducationDraft,
    ExperienceDraft,
    LanguageDraft,
    NamedItemDraft,
    PersonalInfoDraft,
    ProfessionalLinksDraft,
    ProjectDraft,
)
from resume_ai.modules.candidate.application.import_schemas import (
    CandidateResumeExtraction,
    ExtractedCertification,
    ExtractedEducation,
    ExtractedExperience,
    ExtractedLanguage,
    ExtractedNamedItem,
    ExtractedProject,
    ResumeFieldEvidence,
)
from resume_ai.modules.candidate.domain.entities import (
    EducationStatus,
    LanguageLevel,
    ProficiencyLevel,
)


def _value(field: ResumeFieldEvidence | None) -> str | None:
    return None if field is None else field.value


def _issue(
    issues: list[CandidateImportIssue],
    path: str,
    code: CandidateImportIssueCode,
    raw_value: str | None = None,
) -> None:
    issues.append(CandidateImportIssue(path=path, code=code, raw_value=raw_value))


def _required_value(
    field: ResumeFieldEvidence | None,
    path: str,
    issues: list[CandidateImportIssue],
) -> str | None:
    value = _value(field)
    if field is None:
        _issue(issues, path, CandidateImportIssueCode.MISSING_REQUIRED_FIELD)
    return value


def _try_iso_date(
    field: ResumeFieldEvidence | None,
    path: str,
    issues: list[CandidateImportIssue],
    *,
    allow_current: bool = False,
) -> str | None:
    value = _value(field)
    if value is None:
        return None

    marker = value.strip().casefold()
    if allow_current and marker in {"atual", "present", "current"}:
        return None

    try:
        date.fromisoformat(value)
    except ValueError:
        _issue(issues, path, CandidateImportIssueCode.UNSUPPORTED_DATE_FORMAT, value)
        return None
    return value


def _map_closed(
    field: ResumeFieldEvidence | None,
    path: str,
    issues: list[CandidateImportIssue],
    mapping: dict[str, object],
    code: CandidateImportIssueCode,
) -> object | None:
    value = _value(field)
    if value is None:
        return None
    mapped = mapping.get(value.strip().casefold())
    if mapped is None:
        _issue(issues, path, code, value)
    return mapped


_EDUCATION_STATUS_MAP: dict[str, EducationStatus] = {
    "in_progress": EducationStatus.IN_PROGRESS,
    "in progress": EducationStatus.IN_PROGRESS,
    "em andamento": EducationStatus.IN_PROGRESS,
    "cursando": EducationStatus.IN_PROGRESS,
    "completed": EducationStatus.COMPLETED,
    "concluído": EducationStatus.COMPLETED,
    "concluido": EducationStatus.COMPLETED,
    "concluída": EducationStatus.COMPLETED,
    "concluida": EducationStatus.COMPLETED,
    "interrupted": EducationStatus.INTERRUPTED,
    "interrompido": EducationStatus.INTERRUPTED,
    "interrompida": EducationStatus.INTERRUPTED,
}
_PROFICIENCY_MAP: dict[str, ProficiencyLevel] = {
    "basic": ProficiencyLevel.BASIC,
    "básico": ProficiencyLevel.BASIC,
    "basico": ProficiencyLevel.BASIC,
    "intermediate": ProficiencyLevel.INTERMEDIATE,
    "intermediário": ProficiencyLevel.INTERMEDIATE,
    "intermediario": ProficiencyLevel.INTERMEDIATE,
    "advanced": ProficiencyLevel.ADVANCED,
    "avançado": ProficiencyLevel.ADVANCED,
    "avancado": ProficiencyLevel.ADVANCED,
    "expert": ProficiencyLevel.EXPERT,
}
_LANGUAGE_MAP: dict[str, LanguageLevel] = {
    "basic": LanguageLevel.BASIC,
    "básico": LanguageLevel.BASIC,
    "basico": LanguageLevel.BASIC,
    "intermediate": LanguageLevel.INTERMEDIATE,
    "intermediário": LanguageLevel.INTERMEDIATE,
    "intermediario": LanguageLevel.INTERMEDIATE,
    "advanced": LanguageLevel.ADVANCED,
    "avançado": LanguageLevel.ADVANCED,
    "avancado": LanguageLevel.ADVANCED,
    "fluent": LanguageLevel.FLUENT,
    "fluente": LanguageLevel.FLUENT,
    "native": LanguageLevel.NATIVE,
    "nativo": LanguageLevel.NATIVE,
    "nativa": LanguageLevel.NATIVE,
}


def _convert_experience(
    item: ExtractedExperience,
    index: int,
    issues: list[CandidateImportIssue],
) -> ExperienceDraft:
    prefix = f"experiences[{index}]"
    return ExperienceDraft(
        company=_required_value(item.company, f"{prefix}.company", issues),
        role=_required_value(item.role, f"{prefix}.role", issues),
        start_date=_try_iso_date(item.start_date, f"{prefix}.start_date", issues)
        if item.start_date is not None
        else _required_value(None, f"{prefix}.start_date", issues),
        end_date=_try_iso_date(item.end_date, f"{prefix}.end_date", issues, allow_current=True),
        activities=tuple(field.value for field in item.activities),
        achievements=tuple(field.value for field in item.achievements),
    )


def _convert_education(
    item: ExtractedEducation,
    index: int,
    issues: list[CandidateImportIssue],
) -> EducationDraft:
    prefix = f"education[{index}]"
    status = _map_closed(
        item.status,
        f"{prefix}.status",
        issues,
        _EDUCATION_STATUS_MAP,
        CandidateImportIssueCode.UNSUPPORTED_EDUCATION_STATUS,
    )
    if item.status is None:
        _issue(issues, f"{prefix}.status", CandidateImportIssueCode.MISSING_REQUIRED_FIELD)
    return EducationDraft(
        institution=_required_value(item.institution, f"{prefix}.institution", issues),
        course=_required_value(item.course, f"{prefix}.course", issues),
        status=status,
        start_date=_try_iso_date(item.start_date, f"{prefix}.start_date", issues),
        end_date=_try_iso_date(item.end_date, f"{prefix}.end_date", issues),
    )


def _convert_named_item(
    item: ExtractedNamedItem,
    index: int,
    collection: str,
    issues: list[CandidateImportIssue],
) -> NamedItemDraft:
    level = _map_closed(
        item.level,
        f"{collection}[{index}].level",
        issues,
        _PROFICIENCY_MAP,
        CandidateImportIssueCode.UNSUPPORTED_PROFICIENCY_LEVEL,
    )
    return NamedItemDraft(name=item.name.value, level=level)


def _convert_language(
    item: ExtractedLanguage,
    index: int,
    issues: list[CandidateImportIssue],
) -> LanguageDraft:
    level = _map_closed(
        item.level,
        f"languages[{index}].level",
        issues,
        _LANGUAGE_MAP,
        CandidateImportIssueCode.UNSUPPORTED_LANGUAGE_LEVEL,
    )
    return LanguageDraft(name=item.name.value, level=level)


def _convert_certification(
    item: ExtractedCertification,
    index: int,
    issues: list[CandidateImportIssue],
) -> CertificationDraft:
    prefix = f"certifications[{index}]"
    return CertificationDraft(
        name=_required_value(item.name, f"{prefix}.name", issues),
        issuer=_required_value(item.issuer, f"{prefix}.issuer", issues),
        issue_date=_try_iso_date(item.issue_date, f"{prefix}.issue_date", issues),
        expiration_date=_try_iso_date(
            item.expiration_date, f"{prefix}.expiration_date", issues
        ),
        credential_id=_value(item.credential_id),
        credential_url=_value(item.credential_url),
    )


def _convert_project(
    item: ExtractedProject,
    index: int,
    issues: list[CandidateImportIssue],
) -> ProjectDraft:
    prefix = f"projects[{index}]"
    return ProjectDraft(
        name=_required_value(item.name, f"{prefix}.name", issues),
        description=_required_value(item.description, f"{prefix}.description", issues),
        start_date=_try_iso_date(item.start_date, f"{prefix}.start_date", issues),
        end_date=_try_iso_date(item.end_date, f"{prefix}.end_date", issues, allow_current=True),
        technologies=tuple(field.value for field in item.technologies),
        url=_value(item.url),
    )


class CandidateResumeDraftConverter:
    def convert(self, extraction: CandidateResumeExtraction) -> CandidateImportDraft:
        issues: list[CandidateImportIssue] = []
        personal_info = PersonalInfoDraft(
            full_name=_required_value(
                extraction.personal_info.full_name, "personal_info.full_name", issues
            ),
            city=_required_value(extraction.personal_info.city, "personal_info.city", issues),
            state=_required_value(extraction.personal_info.state, "personal_info.state", issues),
            country=_required_value(
                extraction.personal_info.country, "personal_info.country", issues
            ),
        )
        contact_info = ContactInfoDraft(
            email=_required_value(extraction.contact_info.email, "contact_info.email", issues),
            phone=_required_value(extraction.contact_info.phone, "contact_info.phone", issues),
        )
        professional_links = ProfessionalLinksDraft(
            linkedin=_value(extraction.professional_links.linkedin),
            github=_value(extraction.professional_links.github),
            portfolio=_value(extraction.professional_links.portfolio),
        )
        return CandidateImportDraft(
            personal_info=personal_info,
            contact_info=contact_info,
            professional_links=professional_links,
            experiences=tuple(
                _convert_experience(item, index, issues)
                for index, item in enumerate(extraction.experiences)
            ),
            education=tuple(
                _convert_education(item, index, issues)
                for index, item in enumerate(extraction.education)
            ),
            skills=tuple(
                _convert_named_item(item, index, "skills", issues)
                for index, item in enumerate(extraction.skills)
            ),
            technologies=tuple(
                _convert_named_item(item, index, "technologies", issues)
                for index, item in enumerate(extraction.technologies)
            ),
            tools=tuple(
                _convert_named_item(item, index, "tools", issues)
                for index, item in enumerate(extraction.tools)
            ),
            languages=tuple(
                _convert_language(item, index, issues)
                for index, item in enumerate(extraction.languages)
            ),
            certifications=tuple(
                _convert_certification(item, index, issues)
                for index, item in enumerate(extraction.certifications)
            ),
            projects=tuple(
                _convert_project(item, index, issues)
                for index, item in enumerate(extraction.projects)
            ),
            issues=tuple(issues),
        )
