from resume_ai.modules.candidate.application.exceptions import ResumeCandidateGroundingError
from resume_ai.modules.candidate.application.import_schemas import (
    CandidateResumeExtraction,
    ExtractedCertification,
    ExtractedContactInfo,
    ExtractedEducation,
    ExtractedExperience,
    ExtractedLanguage,
    ExtractedNamedItem,
    ExtractedPersonalInfo,
    ExtractedProfessionalLinks,
    ExtractedProject,
    ResumeFieldEvidence,
)


class CandidateResumeTruthGate:
    def validate(self, resume_text: str, extraction: CandidateResumeExtraction) -> None:
        self._validate_personal_info(resume_text, extraction.personal_info)
        self._validate_contact_info(resume_text, extraction.contact_info)
        self._validate_links(resume_text, extraction.professional_links)
        for experience in extraction.experiences:
            self._validate_experience(resume_text, experience)
        for education in extraction.education:
            self._validate_education(resume_text, education)
        for item in extraction.skills + extraction.technologies + extraction.tools:
            self._validate_named_item(resume_text, item)
        for language in extraction.languages:
            self._validate_language(resume_text, language)
        for certification in extraction.certifications:
            self._validate_certification(resume_text, certification)
        for project in extraction.projects:
            self._validate_project(resume_text, project)

    @staticmethod
    def _validate_field(resume_text: str, field: ResumeFieldEvidence) -> None:
        if field.value not in field.evidence or field.evidence not in resume_text:
            raise ResumeCandidateGroundingError(
                "Candidate resume extraction is not grounded in source text"
            )

    @classmethod
    def _validate_optional(cls, resume_text: str, field: ResumeFieldEvidence | None) -> None:
        if field is not None:
            cls._validate_field(resume_text, field)

    @classmethod
    def _validate_personal_info(cls, text: str, info: ExtractedPersonalInfo) -> None:
        for field in (info.full_name, info.city, info.state, info.country):
            cls._validate_optional(text, field)

    @classmethod
    def _validate_contact_info(cls, text: str, info: ExtractedContactInfo) -> None:
        for field in (info.email, info.phone):
            cls._validate_optional(text, field)

    @classmethod
    def _validate_links(cls, text: str, links: ExtractedProfessionalLinks) -> None:
        for field in (links.linkedin, links.github, links.portfolio):
            cls._validate_optional(text, field)

    @classmethod
    def _validate_experience(cls, text: str, experience: ExtractedExperience) -> None:
        for field in (
            experience.company,
            experience.role,
            experience.start_date,
            experience.end_date,
        ):
            cls._validate_optional(text, field)
        for field in experience.activities + experience.achievements:
            cls._validate_field(text, field)

    @classmethod
    def _validate_education(cls, text: str, education: ExtractedEducation) -> None:
        for field in (
            education.institution,
            education.course,
            education.status,
            education.start_date,
            education.end_date,
        ):
            cls._validate_optional(text, field)

    @classmethod
    def _validate_named_item(cls, text: str, item: ExtractedNamedItem) -> None:
        cls._validate_field(text, item.name)
        cls._validate_optional(text, item.level)

    @classmethod
    def _validate_language(cls, text: str, language: ExtractedLanguage) -> None:
        cls._validate_field(text, language.name)
        cls._validate_optional(text, language.level)

    @classmethod
    def _validate_certification(cls, text: str, certification: ExtractedCertification) -> None:
        for field in (
            certification.name,
            certification.issuer,
            certification.issue_date,
            certification.expiration_date,
            certification.credential_id,
            certification.credential_url,
        ):
            cls._validate_optional(text, field)

    @classmethod
    def _validate_project(cls, text: str, project: ExtractedProject) -> None:
        for field in (
            project.name,
            project.description,
            project.start_date,
            project.end_date,
            project.url,
        ):
            cls._validate_optional(text, field)
        for technology in project.technologies:
            cls._validate_field(text, technology)
