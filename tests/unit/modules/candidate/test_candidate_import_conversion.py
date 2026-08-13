from copy import deepcopy

import pytest

from resume_ai.modules.candidate.application.import_conversion import (
    CandidateResumeDraftConverter,
)
from resume_ai.modules.candidate.application.import_draft import CandidateImportIssueCode
from resume_ai.modules.candidate.application.import_schemas import (
    CandidateResumeExtraction,
    ExtractedCertification,
    ExtractedEducation,
    ExtractedExperience,
    ExtractedLanguage,
    ExtractedNamedItem,
    ExtractedPersonalInfo,
    ExtractedProject,
    ResumeFieldEvidence,
)
from resume_ai.modules.candidate.domain.entities import (
    EducationStatus,
    LanguageLevel,
    ProficiencyLevel,
)


def evidence(value: str) -> ResumeFieldEvidence:
    return ResumeFieldEvidence(value=value, evidence=value)


def issue_codes(draft) -> list[CandidateImportIssueCode]:
    return [issue.code for issue in draft.issues]


def test_empty_extraction_preserves_none_and_reports_required_fields() -> None:
    draft = CandidateResumeDraftConverter().convert(CandidateResumeExtraction())

    assert draft.personal_info.full_name is None
    assert draft.contact_info.email is None
    assert [issue.path for issue in draft.issues] == [
        "personal_info.full_name",
        "personal_info.city",
        "personal_info.state",
        "personal_info.country",
        "contact_info.email",
        "contact_info.phone",
    ]
    assert all(
        issue.code == CandidateImportIssueCode.MISSING_REQUIRED_FIELD
        for issue in draft.issues
    )


def test_simple_values_are_literal_values_not_evidence() -> None:
    extraction = CandidateResumeExtraction(
        personal_info=ExtractedPersonalInfo(
            full_name=evidence("Jane Doe"),
            city=evidence("Curitiba"),
            state=evidence("PR"),
            country=evidence("Brasil"),
        ),
        contact_info={"email": evidence("not-an-email"), "phone": evidence("+55")},
        professional_links={"github": evidence("github.com/jane")},
    )

    draft = CandidateResumeDraftConverter().convert(extraction)

    assert draft.personal_info.full_name == "Jane Doe"
    assert draft.contact_info.email == "not-an-email"
    assert draft.professional_links.github == "github.com/jane"
    assert draft.issues == ()


def test_partial_experiences_are_preserved_with_missing_issues() -> None:
    extraction = CandidateResumeExtraction(
        experiences=(ExtractedExperience(role=evidence("Backend Developer")),)
    )

    draft = CandidateResumeDraftConverter().convert(extraction)

    assert len(draft.experiences) == 1
    assert draft.experiences[0].role == "Backend Developer"
    assert [issue.path for issue in draft.issues] == [
        "personal_info.full_name",
        "personal_info.city",
        "personal_info.state",
        "personal_info.country",
        "contact_info.email",
        "contact_info.phone",
        "experiences[0].company",
        "experiences[0].start_date",
    ]


@pytest.mark.parametrize("value", ["2024-01-31", "2024-01", "01/2024"])
def test_valid_iso_date_is_preserved(value: str) -> None:
    extraction = CandidateResumeExtraction(
        experiences=(ExtractedExperience(start_date=evidence(value)),)
    )

    draft = CandidateResumeDraftConverter().convert(extraction)

    assert draft.experiences[0].start_date == "2024-01"
    assert not any(issue.path == "experiences[0].start_date" for issue in draft.issues)


@pytest.mark.parametrize("value", ["13/2024", "2024-13", "2024-02-31"])
def test_invalid_month_dates_report_unsupported_format(value: str) -> None:
    extraction = CandidateResumeExtraction(
        experiences=(ExtractedExperience(start_date=evidence(value)),)
    )

    draft = CandidateResumeDraftConverter().convert(extraction)

    assert draft.experiences[0].start_date is None
    issue = next(issue for issue in draft.issues if issue.path == "experiences[0].start_date")
    assert issue.code == CandidateImportIssueCode.UNSUPPORTED_DATE_FORMAT
    assert issue.raw_value == value


@pytest.mark.parametrize(
    "value",
    [
        "2024-02-31",
        "20240131",
        "2021-W01-1",
        "2024/01/31",
        "01/31/2024",
        "31/01/2024",
        "2024",
        "2024-1-31",
        "2024-01-1",
    ],
)
def test_unsupported_dates_are_not_inferred(value: str) -> None:
    extraction = CandidateResumeExtraction(
        experiences=(ExtractedExperience(start_date=evidence(value)),)
    )

    draft = CandidateResumeDraftConverter().convert(extraction)

    assert draft.experiences[0].start_date is None
    issue = next(issue for issue in draft.issues if issue.path == "experiences[0].start_date")
    assert issue.code == CandidateImportIssueCode.UNSUPPORTED_DATE_FORMAT
    assert issue.raw_value == value


def test_valid_leap_day_is_preserved() -> None:
    extraction = CandidateResumeExtraction(
        experiences=(ExtractedExperience(start_date=evidence("2000-02-29")),)
    )

    draft = CandidateResumeDraftConverter().convert(extraction)

    assert draft.experiences[0].start_date == "2000-02"
    assert not any(issue.path == "experiences[0].start_date" for issue in draft.issues)


def test_certification_dates_keep_full_day_precision() -> None:
    extraction = CandidateResumeExtraction(
        certifications=(
            ExtractedCertification(
                name=evidence("Certification"),
                issuer=evidence("Institute"),
                issue_date=evidence("2025-03-17"),
            ),
        )
    )

    draft = CandidateResumeDraftConverter().convert(extraction)

    assert draft.certifications[0].issue_date == "2025-03-17"


@pytest.mark.parametrize("value", ["Atual", "ATUAL", "Present", "present", "Current"])
def test_current_markers_are_supported_only_for_experience_end_date(value: str) -> None:
    extraction = CandidateResumeExtraction(
        experiences=(
            ExtractedExperience(end_date=evidence(value)),
            ExtractedExperience(start_date=evidence(value)),
        )
    )

    draft = CandidateResumeDraftConverter().convert(extraction)

    assert draft.experiences[0].end_date is None
    assert not any(issue.path == "experiences[0].end_date" for issue in draft.issues)
    assert draft.experiences[1].start_date is None
    assert any(issue.path == "experiences[1].start_date" for issue in draft.issues)


def test_closed_education_status_map_and_unknown_status() -> None:
    extraction = CandidateResumeExtraction(
        education=(
            ExtractedEducation(status=evidence("Em andamento")),
            ExtractedEducation(status=evidence("Concluida")),
            ExtractedEducation(status=evidence("Trancado")),
        )
    )

    draft = CandidateResumeDraftConverter().convert(extraction)

    assert draft.education[0].status is EducationStatus.IN_PROGRESS
    assert draft.education[1].status is EducationStatus.COMPLETED
    assert draft.education[2].status is None
    issue = next(issue for issue in draft.issues if issue.path == "education[2].status")
    assert issue.code == CandidateImportIssueCode.UNSUPPORTED_EDUCATION_STATUS
    assert issue.raw_value == "Trancado"


def test_closed_proficiency_and_language_maps() -> None:
    extraction = CandidateResumeExtraction(
        skills=(
            ExtractedNamedItem(name=evidence("Python"), level=evidence("Avançado")),
            ExtractedNamedItem(name=evidence("SQL"), level=evidence("Senior")),
        ),
        languages=(
            ExtractedLanguage(name=evidence("Português"), level=evidence("Nativo")),
            ExtractedLanguage(name=evidence("English"), level=evidence("Conversacional")),
        ),
    )

    draft = CandidateResumeDraftConverter().convert(extraction)

    assert draft.skills[0].level is ProficiencyLevel.ADVANCED
    assert draft.skills[1].level is None
    assert draft.languages[0].level is LanguageLevel.NATIVE
    assert draft.languages[1].level is None
    assert issue_codes(draft).count(CandidateImportIssueCode.UNSUPPORTED_PROFICIENCY_LEVEL) == 1
    assert issue_codes(draft).count(CandidateImportIssueCode.UNSUPPORTED_LANGUAGE_LEVEL) == 1


def test_partial_collections_and_nested_values_are_preserved() -> None:
    extraction = CandidateResumeExtraction(
        experiences=(
            ExtractedExperience(
                activities=(evidence("Build APIs"),),
                achievements=(evidence("Reduced latency"),),
            ),
        ),
        certifications=(ExtractedCertification(name=evidence("AWS")),),
        projects=(
            ExtractedProject(
                description=evidence("A real project"),
                technologies=(evidence("Python"), evidence("FastAPI")),
            ),
        ),
    )

    draft = CandidateResumeDraftConverter().convert(extraction)

    assert draft.experiences[0].activities == ("Build APIs",)
    assert draft.experiences[0].achievements == ("Reduced latency",)
    assert draft.certifications[0].name == "AWS"
    assert draft.projects[0].description == "A real project"
    assert draft.projects[0].technologies == ("Python", "FastAPI")
    assert "certifications[0].issuer" in [issue.path for issue in draft.issues]
    assert "projects[0].name" in [issue.path for issue in draft.issues]


def test_conversion_does_not_mutate_extraction() -> None:
    extraction = CandidateResumeExtraction(
        personal_info=ExtractedPersonalInfo(full_name=evidence("Jane Doe")),
        experiences=(ExtractedExperience(start_date=evidence("01/2024")),),
    )
    before = deepcopy(extraction)

    CandidateResumeDraftConverter().convert(extraction)

    assert extraction == before
