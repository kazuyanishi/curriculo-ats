import pytest

from resume_ai.modules.candidate.application.exceptions import ResumeCandidateGroundingError
from resume_ai.modules.candidate.application.grounding import CandidateResumeTruthGate
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


def field(value: str, evidence: str | None = None) -> ResumeFieldEvidence:
    return ResumeFieldEvidence(value=value, evidence=evidence or value)


def test_valid_facts_pass_and_empty_extraction_passes() -> None:
    gate = CandidateResumeTruthGate()
    extraction = CandidateResumeExtraction(
        personal_info=ExtractedPersonalInfo(full_name=field("Jane Doe")),
        technologies=[
            ExtractedNamedItem(name=field("Python")),
            ExtractedNamedItem(name=field("FastAPI")),
        ],
    )
    assert gate.validate("Jane Doe\nPython\nFastAPI", extraction) is None
    assert gate.validate("anything", CandidateResumeExtraction()) is None
    assert gate.validate("", CandidateResumeExtraction()) is None


def test_value_must_be_literal_inside_evidence() -> None:
    extraction = CandidateResumeExtraction(
        technologies=[ExtractedNamedItem(name=field("Kubernetes", "Skills: Python"))]
    )
    with pytest.raises(ResumeCandidateGroundingError):
        CandidateResumeTruthGate().validate("Skills: Python", extraction)


def test_evidence_must_be_literal_inside_resume() -> None:
    extraction = CandidateResumeExtraction(
        technologies=[ExtractedNamedItem(name=field("Kubernetes", "Skills: Kubernetes"))]
    )
    with pytest.raises(ResumeCandidateGroundingError):
        CandidateResumeTruthGate().validate("Skills: Python", extraction)


@pytest.mark.parametrize(
    ("resume_text", "value", "evidence"),
    [
        ("Python", "python", "Python"),
        ("Inglês", "Ingles", "Inglês"),
        ("Python   FastAPI", "FastAPI", "Python FastAPI"),
    ],
)
def test_grounding_is_case_accent_and_whitespace_sensitive(
    resume_text: str, value: str, evidence: str
) -> None:
    extraction = CandidateResumeExtraction(
        technologies=[ExtractedNamedItem(name=field(value, evidence))]
    )
    with pytest.raises(ResumeCandidateGroundingError):
        CandidateResumeTruthGate().validate(resume_text, extraction)


def test_empty_resume_with_fact_fails() -> None:
    extraction = CandidateResumeExtraction(technologies=[ExtractedNamedItem(name=field("Python"))])
    with pytest.raises(ResumeCandidateGroundingError):
        CandidateResumeTruthGate().validate("", extraction)


def test_entire_extraction_tree_and_nested_collections_are_validated() -> None:
    facts = [
        "Jane Doe",
        "Curitiba",
        "PR",
        "Brasil",
        "jane@example.com",
        "+55",
        "linkedin.com/jane",
        "github.com/jane",
        "portfolio.dev",
        "Example Systems",
        "Backend Developer",
        "2022",
        "Atual",
        "Developed APIs",
        "Reduced latency",
        "Computer Science",
        "University",
        "Em andamento",
        "01/2020",
        "12/2024",
        "Python",
        "Advanced",
        "Docker",
        "Git",
        "Inglês",
        "Fluente",
        "AWS Certification",
        "AWS",
        "2024",
        "2026",
        "CERT-1",
        "cert.example",
        "Resume App",
        "Built a resume app",
        "2023",
        "Atual",
        "FastAPI",
        "app.example",
    ]
    text = "\n".join(facts)
    extraction = CandidateResumeExtraction(
        personal_info=ExtractedPersonalInfo(
            full_name=field("Jane Doe"),
            city=field("Curitiba"),
            state=field("PR"),
            country=field("Brasil"),
        ),
        contact_info=ExtractedContactInfo(email=field("jane@example.com"), phone=field("+55")),
        professional_links=ExtractedProfessionalLinks(
            linkedin=field("linkedin.com/jane"),
            github=field("github.com/jane"),
            portfolio=field("portfolio.dev"),
        ),
        experiences=[
            ExtractedExperience(
                company=field("Example Systems"),
                role=field("Backend Developer"),
                start_date=field("2022"),
                end_date=field("Atual"),
                activities=[field("Developed APIs")],
                achievements=[field("Reduced latency")],
            )
        ],
        education=[
            ExtractedEducation(
                institution=field("University"),
                course=field("Computer Science"),
                status=field("Em andamento"),
                start_date=field("01/2020"),
                end_date=field("12/2024"),
            )
        ],
        skills=[ExtractedNamedItem(name=field("Python"), level=field("Advanced"))],
        technologies=[ExtractedNamedItem(name=field("Docker"))],
        tools=[ExtractedNamedItem(name=field("Git"))],
        languages=[ExtractedLanguage(name=field("Inglês"), level=field("Fluente"))],
        certifications=[
            ExtractedCertification(
                name=field("AWS Certification"),
                issuer=field("AWS"),
                issue_date=field("2024"),
                expiration_date=field("2026"),
                credential_id=field("CERT-1"),
                credential_url=field("cert.example"),
            )
        ],
        projects=[
            ExtractedProject(
                name=field("Resume App"),
                description=field("Built a resume app"),
                start_date=field("2023"),
                end_date=field("Atual"),
                technologies=[field("FastAPI")],
                url=field("app.example"),
            )
        ],
    )
    original = extraction
    assert CandidateResumeTruthGate().validate(text, extraction) is None
    assert extraction == original


def test_deep_invalid_fact_is_rejected() -> None:
    extraction = CandidateResumeExtraction(
        projects=[ExtractedProject(technologies=[field("Kubernetes")])]
    )
    with pytest.raises(ResumeCandidateGroundingError):
        CandidateResumeTruthGate().validate("Project\nPython", extraction)
