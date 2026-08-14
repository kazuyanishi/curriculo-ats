import pytest

from resume_ai.modules.candidate.application.exceptions import (
    GroundingReason,
    ResumeCandidateGroundingError,
)
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


def test_entire_extraction_tree_and_nested_collections_are_validated() -> None:
    facts = [
        "Jane Doe",
        "Curitiba",
        "PR",
        "Brazil",
        "jane@example.com",
        "+55",
        "linkedin.com/jane",
        "github.com/jane",
        "portfolio.dev",
        "Example Systems",
        "Backend Developer",
        "2022",
        "Current",
        "Developed APIs",
        "Reduced latency",
        "Computer Science",
        "University",
        "In progress",
        "01/2020",
        "12/2024",
        "Python",
        "Advanced",
        "Docker",
        "Git",
        "English",
        "Fluent",
        "AWS Certification",
        "AWS",
        "2024",
        "2026",
        "CERT-1",
        "cert.example",
        "Resume App",
        "Built a resume app",
        "2023",
        "FastAPI",
        "app.example",
    ]
    extraction = CandidateResumeExtraction(
        personal_info=ExtractedPersonalInfo(
            full_name=field("Jane Doe"),
            city=field("Curitiba"),
            state=field("PR"),
            country=field("Brazil"),
        ),
        contact_info=ExtractedContactInfo(email=field("jane@example.com"), phone=field("+55")),
        professional_links=ExtractedProfessionalLinks(
            linkedin=field("linkedin.com/jane"),
            github=field("github.com/jane"),
            portfolio=field("portfolio.dev"),
        ),
        experiences=(
            ExtractedExperience(
                company=field("Example Systems"),
                role=field("Backend Developer"),
                start_date=field("2022"),
                end_date=field("Current"),
                activities=(field("Developed APIs"),),
                achievements=(field("Reduced latency"),),
            ),
        ),
        education=(
            ExtractedEducation(
                institution=field("University"),
                course=field("Computer Science"),
                status=field("In progress"),
                start_date=field("01/2020"),
                end_date=field("12/2024"),
            ),
        ),
        skills=(ExtractedNamedItem(name=field("Python"), level=field("Advanced")),),
        technologies=(ExtractedNamedItem(name=field("Docker")),),
        tools=(ExtractedNamedItem(name=field("Git")),),
        languages=(ExtractedLanguage(name=field("English"), level=field("Fluent")),),
        certifications=(
            ExtractedCertification(
                name=field("AWS Certification"),
                issuer=field("AWS"),
                issue_date=field("2024"),
                expiration_date=field("2026"),
                credential_id=field("CERT-1"),
                credential_url=field("cert.example"),
            ),
        ),
        projects=(
            ExtractedProject(
                name=field("Resume App"),
                description=field("Built a resume app"),
                start_date=field("2023"),
                technologies=(field("FastAPI"),),
                url=field("app.example"),
            ),
        ),
    )

    assert CandidateResumeTruthGate().validate("\n".join(facts), extraction) is None


def test_value_must_be_literal_inside_evidence() -> None:
    extraction = CandidateResumeExtraction(
        technologies=[ExtractedNamedItem(name=field("Kubernetes", "Skills: Python"))]
    )
    with pytest.raises(ResumeCandidateGroundingError) as raised:
        CandidateResumeTruthGate().validate("Skills: Python", extraction)

    assert raised.value.path == "technologies[0].name"
    assert raised.value.reason is GroundingReason.VALUE_NOT_IN_EVIDENCE
    assert raised.value.whitespace_normalized_match is None
    assert "Kubernetes" not in str(raised.value)


def test_project_description_must_be_literal_inside_evidence() -> None:
    extraction = CandidateResumeExtraction(
        projects=(
            ExtractedProject(
                description=field(
                    "Desenvolvimento de um sistema ERP completo.",
                    "Desenvolvimento e evolução de sistema ERP próprio.",
                )
            ),
        )
    )

    with pytest.raises(ResumeCandidateGroundingError) as raised:
        CandidateResumeTruthGate().validate(
            "Desenvolvimento e evolução de sistema ERP próprio.", extraction
        )

    assert raised.value.path == "projects[0].description"
    assert raised.value.reason is GroundingReason.VALUE_NOT_IN_EVIDENCE


def test_literal_project_description_passes_grounding() -> None:
    description = "Desenvolvimento e evolução de sistema ERP próprio."
    extraction = CandidateResumeExtraction(
        projects=(ExtractedProject(description=field(description)),)
    )

    assert (
        CandidateResumeTruthGate().validate(f"PROJETO: Sistema ERP\n{description}", extraction)
        is None
    )


def test_literal_evidence_is_accepted() -> None:
    extraction = CandidateResumeExtraction(technologies=[ExtractedNamedItem(name=field("Python"))])
    assert CandidateResumeTruthGate().validate("Python FastAPI", extraction) is None


@pytest.mark.parametrize(
    ("resume_text", "evidence"),
    [
        ("Python  FastAPI", "Python FastAPI"),
        ("Python\nFastAPI", "Python FastAPI"),
        ("Python\tFastAPI", "Python FastAPI"),
        ("Python \n\t FastAPI", "Python FastAPI"),
        (
            "Elaboração  de manuais\n e documentação técnica",
            "Elaboração de manuais e documentação técnica",
        ),
    ],
)
def test_whitespace_equivalent_evidence_is_accepted(resume_text: str, evidence: str) -> None:
    extraction = CandidateResumeExtraction(
        technologies=[ExtractedNamedItem(name=field("Python", evidence))]
        if evidence.startswith("Python")
        else CandidateResumeExtraction().technologies
    )
    if not evidence.startswith("Python"):
        extraction = CandidateResumeExtraction(
            experiences=(ExtractedExperience(activities=(field(evidence),)),)
        )

    assert CandidateResumeTruthGate().validate(resume_text, extraction) is None


@pytest.mark.parametrize(
    ("resume_text", "value", "evidence"),
    [
        ("Python", "python", "Python"),
        ("Inglês", "Ingles", "Inglês"),
        ("Python, FastAPI", "Python FastAPI", "Python FastAPI"),
        ("Elaboração de manuais", "Elaboração de documentação", "Elaboração de documentação"),
        ("Python FastAPI", "Python Django FastAPI", "Python Django FastAPI"),
    ],
)
def test_grounding_remains_strict_beyond_whitespace(
    resume_text: str, value: str, evidence: str
) -> None:
    extraction = CandidateResumeExtraction(
        technologies=[ExtractedNamedItem(name=field(value, evidence))]
    )
    with pytest.raises(ResumeCandidateGroundingError) as raised:
        CandidateResumeTruthGate().validate(resume_text, extraction)

    assert raised.value.reason in {
        GroundingReason.VALUE_NOT_IN_EVIDENCE,
        GroundingReason.EVIDENCE_NOT_IN_RESUME_TEXT,
    }


def test_evidence_failure_reports_non_whitespace_difference() -> None:
    extraction = CandidateResumeExtraction(
        experiences=(ExtractedExperience(activities=(field("Elaboração de documentação"),)),)
    )
    with pytest.raises(ResumeCandidateGroundingError) as raised:
        CandidateResumeTruthGate().validate("Elaboração de manuais", extraction)

    assert raised.value.path == "experiences[0].activities[0]"
    assert raised.value.reason is GroundingReason.EVIDENCE_NOT_IN_RESUME_TEXT
    assert raised.value.whitespace_normalized_match is False


def test_deep_invalid_fact_is_rejected() -> None:
    extraction = CandidateResumeExtraction(
        projects=[ExtractedProject(technologies=[field("Kubernetes")])]
    )
    with pytest.raises(ResumeCandidateGroundingError):
        CandidateResumeTruthGate().validate("Project\nPython", extraction)


@pytest.mark.parametrize(
    ("extraction", "resume_text", "expected_path"),
    [
        (
            CandidateResumeExtraction(
                personal_info=ExtractedPersonalInfo(full_name=field("Ghost"))
            ),
            "Jane Doe",
            "personal_info.full_name",
        ),
        (
            CandidateResumeExtraction(education=(ExtractedEducation(status=field("Completed")),)),
            "Computer Science",
            "education[0].status",
        ),
        (
            CandidateResumeExtraction(
                languages=(
                    ExtractedLanguage(name=field("Portuguese")),
                    ExtractedLanguage(name=field("English"), level=field("Fluent")),
                )
            ),
            "Portuguese\nEnglish",
            "languages[1].level",
        ),
        (
            CandidateResumeExtraction(
                projects=(
                    ExtractedProject(name=field("Project One")),
                    ExtractedProject(name=field("Project Two"), technologies=(field("Hidden"),)),
                )
            ),
            "Project One\nProject Two",
            "projects[1].technologies[0]",
        ),
        (
            CandidateResumeExtraction(
                experiences=(
                    ExtractedExperience(role=field("Backend Developer")),
                    ExtractedExperience(
                        role=field("Frontend Developer"),
                        activities=(field("Hidden activity"),),
                    ),
                )
            ),
            "Backend Developer\nFrontend Developer",
            "experiences[1].activities[0]",
        ),
    ],
)
def test_grounding_error_reports_nested_field_path(
    extraction: CandidateResumeExtraction, resume_text: str, expected_path: str
) -> None:
    with pytest.raises(ResumeCandidateGroundingError) as raised:
        CandidateResumeTruthGate().validate(resume_text, extraction)

    assert raised.value.path == expected_path
    assert raised.value.reason is GroundingReason.EVIDENCE_NOT_IN_RESUME_TEXT
