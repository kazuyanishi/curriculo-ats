from resume_ai.modules.candidate.application.exceptions import (
    GroundingReason,
    ResumeCandidateGroundingError,
)
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
        for index, experience in enumerate(extraction.experiences):
            self._validate_experience(resume_text, experience, f"experiences[{index}]")
        for index, education in enumerate(extraction.education):
            self._validate_education(resume_text, education, f"education[{index}]")
        for collection_name, items in (
            ("skills", extraction.skills),
            ("technologies", extraction.technologies),
            ("tools", extraction.tools),
        ):
            for index, item in enumerate(items):
                self._validate_named_item(resume_text, item, f"{collection_name}[{index}]")
        for index, language in enumerate(extraction.languages):
            self._validate_language(resume_text, language, f"languages[{index}]")
        for index, certification in enumerate(extraction.certifications):
            self._validate_certification(resume_text, certification, f"certifications[{index}]")
        for index, project in enumerate(extraction.projects):
            self._validate_project(resume_text, project, f"projects[{index}]")

    @staticmethod
    def _validate_field(resume_text: str, field: ResumeFieldEvidence, path: str) -> None:
        if field.value not in field.evidence:
            raise ResumeCandidateGroundingError(path, GroundingReason.VALUE_NOT_IN_EVIDENCE)
        if field.evidence not in resume_text:
            normalized_evidence = " ".join(field.evidence.split())
            normalized_resume_text = " ".join(resume_text.split())
            raise ResumeCandidateGroundingError(
                path,
                GroundingReason.EVIDENCE_NOT_IN_RESUME_TEXT,
                normalized_evidence in normalized_resume_text,
            )

    @classmethod
    def _validate_optional(
        cls, resume_text: str, field: ResumeFieldEvidence | None, path: str
    ) -> None:
        if field is not None:
            cls._validate_field(resume_text, field, path)

    @classmethod
    def _validate_personal_info(cls, text: str, info: ExtractedPersonalInfo) -> None:
        for name, field in (
            ("full_name", info.full_name),
            ("city", info.city),
            ("state", info.state),
            ("country", info.country),
        ):
            cls._validate_optional(text, field, f"personal_info.{name}")

    @classmethod
    def _validate_contact_info(cls, text: str, info: ExtractedContactInfo) -> None:
        for name, field in (("email", info.email), ("phone", info.phone)):
            cls._validate_optional(text, field, f"contact_info.{name}")

    @classmethod
    def _validate_links(cls, text: str, links: ExtractedProfessionalLinks) -> None:
        for name, field in (
            ("linkedin", links.linkedin),
            ("github", links.github),
            ("portfolio", links.portfolio),
        ):
            cls._validate_optional(text, field, f"professional_links.{name}")

    @classmethod
    def _validate_experience(cls, text: str, experience: ExtractedExperience, path: str) -> None:
        for name, field in (
            ("company", experience.company),
            ("role", experience.role),
            ("start_date", experience.start_date),
            ("end_date", experience.end_date),
        ):
            cls._validate_optional(text, field, f"{path}.{name}")
        for name, fields in (
            ("activities", experience.activities),
            ("achievements", experience.achievements),
        ):
            for index, field in enumerate(fields):
                cls._validate_field(text, field, f"{path}.{name}[{index}]")

    @classmethod
    def _validate_education(cls, text: str, education: ExtractedEducation, path: str) -> None:
        for name, field in (
            ("institution", education.institution),
            ("course", education.course),
            ("status", education.status),
            ("start_date", education.start_date),
            ("end_date", education.end_date),
        ):
            cls._validate_optional(text, field, f"{path}.{name}")

    @classmethod
    def _validate_named_item(cls, text: str, item: ExtractedNamedItem, path: str) -> None:
        cls._validate_field(text, item.name, f"{path}.name")
        cls._validate_optional(text, item.level, f"{path}.level")

    @classmethod
    def _validate_language(cls, text: str, language: ExtractedLanguage, path: str) -> None:
        cls._validate_field(text, language.name, f"{path}.name")
        cls._validate_optional(text, language.level, f"{path}.level")

    @classmethod
    def _validate_certification(
        cls, text: str, certification: ExtractedCertification, path: str
    ) -> None:
        for name, field in (
            ("name", certification.name),
            ("issuer", certification.issuer),
            ("issue_date", certification.issue_date),
            ("expiration_date", certification.expiration_date),
            ("credential_id", certification.credential_id),
            ("credential_url", certification.credential_url),
        ):
            cls._validate_optional(text, field, f"{path}.{name}")

    @classmethod
    def _validate_project(cls, text: str, project: ExtractedProject, path: str) -> None:
        for name, field in (
            ("name", project.name),
            ("description", project.description),
            ("start_date", project.start_date),
            ("end_date", project.end_date),
            ("url", project.url),
        ):
            cls._validate_optional(text, field, f"{path}.{name}")
        for index, technology in enumerate(project.technologies):
            cls._validate_field(text, technology, f"{path}.technologies[{index}]")
