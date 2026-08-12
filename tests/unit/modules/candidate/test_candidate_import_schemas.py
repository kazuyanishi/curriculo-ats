import pytest
from pydantic import ValidationError

from resume_ai.modules.candidate.application.import_schemas import (
    CandidateResumeExtraction,
    ExtractedEducation,
    ExtractedExperience,
    ExtractedLanguage,
    ExtractedNamedItem,
    ResumeFieldEvidence,
)


def test_evidence_accepts_raw_value_and_evidence() -> None:
    evidence = ResumeFieldEvidence(value="Python", evidence="Skills: Python")
    assert evidence.value == "Python"


@pytest.mark.parametrize("field", ["value", "evidence"])
def test_evidence_rejects_blank_fields(field: str) -> None:
    with pytest.raises(ValidationError):
        ResumeFieldEvidence(
            value="Python" if field == "evidence" else "",
            evidence="Skills: Python" if field == "value" else "",
        )


def test_evidence_forbids_extra_fields() -> None:
    with pytest.raises(ValidationError):
        ResumeFieldEvidence(value="Python", evidence="Python", extra="x")


def test_empty_extraction_is_valid() -> None:
    extraction = CandidateResumeExtraction()
    assert extraction.experiences == ()
    assert extraction.personal_info.full_name is None


def test_optional_personal_info_and_partial_experience_are_allowed() -> None:
    evidence = ResumeFieldEvidence(value="Backend Developer", evidence="Backend Developer")
    extraction = CandidateResumeExtraction(experiences=[ExtractedExperience(role=evidence)])
    assert extraction.experiences[0].company is None


def test_raw_dates_status_and_language_level_are_preserved() -> None:
    date = ResumeFieldEvidence(value="01/2024", evidence="01/2024")
    status = ResumeFieldEvidence(value="Em andamento", evidence="Em andamento")
    level = ResumeFieldEvidence(value="Fluente", evidence="Inglês Fluente")
    extraction = CandidateResumeExtraction(
        education=[ExtractedEducation(status=status, start_date=date)],
        languages=[
            ExtractedLanguage(
                name=ResumeFieldEvidence(value="Inglês", evidence="Inglês Fluente"),
                level=level,
            )
        ],
    )
    assert extraction.education[0].start_date.value == "01/2024"
    assert extraction.education[0].status.value == "Em andamento"
    assert extraction.languages[0].level.value == "Fluente"


def test_named_item_requires_name() -> None:
    with pytest.raises(ValidationError):
        ExtractedNamedItem()
