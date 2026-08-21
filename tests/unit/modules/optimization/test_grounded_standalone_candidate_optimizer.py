import pytest

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
    ProficiencyLevel,
    Project,
    Skill,
    Technology,
    Tool,
)
from resume_ai.modules.candidate.domain.value_objects import YearMonth
from resume_ai.modules.optimization.application.exceptions import OptimizationProposalGroundingError
from resume_ai.modules.optimization.application.planning import (
    CandidateOptimizationPlan,
    StandaloneOptimizationContext,
)
from resume_ai.modules.optimization.application.services import GroundedStandaloneCandidateOptimizer


def candidate() -> Candidate:
    return Candidate(
        PersonalInfo("Jane Doe", "Curitiba", "PR", "Brazil"),
        ContactInfo("jane@example.test", "+55 41 99999-0000"),
        experiences=(
            Experience(
                "Example",
                "Support Analyst",
                YearMonth("2020-01"),
                activities=(Activity("Atendimento a usuários."),),
                achievements=(Achievement("Redução de tempo de atendimento."),),
            ),
        ),
        education=(Education("Example University", "Computer Science", EducationStatus.COMPLETED),),
        skills=(
            Skill("Leadership"),
            Skill("Python", ProficiencyLevel.ADVANCED),
            Skill("Communication", ProficiencyLevel.INTERMEDIATE),
            Skill("Troubleshooting"),
        ),
        technologies=(Technology("Docker"), Technology("PostgreSQL", ProficiencyLevel.ADVANCED)),
        tools=(Tool("Git"), Tool("Jira")),
        languages=(Language("English"), Language("Portuguese", LanguageLevel.NATIVE)),
        certifications=(
            Certification("Azure Fundamentals", "Microsoft"),
            Certification("AWS Cloud Practitioner", "Amazon"),
        ),
        projects=(Project("Resume AI", "Aplicação para análise de currículos."),),
    )


def plan(*paths: str) -> CandidateOptimizationPlan:
    return CandidateOptimizationPlan(
        standalone_contexts=(StandaloneOptimizationContext(0, paths),) if paths else ()
    )


def test_empty_plan_returns_original_candidate() -> None:
    source = candidate()

    assert (
        GroundedStandaloneCandidateOptimizer().optimize(source, CandidateOptimizationPlan())
        is source
    )


@pytest.mark.parametrize(
    ("path", "collection", "expected_first"),
    [
        ("skills[2].name", "skills", "Communication"),
        ("skills[2].level", "skills", "Communication"),
        ("tools[1].name", "tools", "Jira"),
        ("languages[1].level", "languages", "Portuguese"),
        ("certifications[1].issuer", "certifications", "AWS Cloud Practitioner"),
    ],
)
def test_supported_provenance_path_prioritizes_its_collection(
    path: str,
    collection: str,
    expected_first: str,
) -> None:
    result = GroundedStandaloneCandidateOptimizer().optimize(candidate(), plan(path))

    assert getattr(result, collection)[0].name == expected_first


def test_semantic_alias_prioritizes_technology_from_provenance_without_renaming() -> None:
    source = candidate()

    result = GroundedStandaloneCandidateOptimizer().optimize(source, plan("technologies[1].name"))

    assert tuple(item.name for item in result.technologies) == ("PostgreSQL", "Docker")
    assert result.technologies[0] is source.technologies[1]


def test_stable_prioritization_deduplicates_paths_and_preserves_source_order() -> None:
    source = candidate()
    input_plan = CandidateOptimizationPlan(
        standalone_contexts=(
            StandaloneOptimizationContext(0, ("skills[3].name", "skills[1].name")),
            StandaloneOptimizationContext(1, ("skills[1].level",)),
        )
    )

    result = GroundedStandaloneCandidateOptimizer().optimize(source, input_plan)

    assert tuple(item.name for item in result.skills) == (
        "Python",
        "Troubleshooting",
        "Leadership",
        "Communication",
    )
    assert result.skills[0] is source.skills[1]
    assert result.skills[1] is source.skills[3]


def test_valid_unsupported_paths_leave_candidate_unchanged() -> None:
    source = candidate()

    result = GroundedStandaloneCandidateOptimizer().optimize(
        source,
        plan(
            "education[0].course",
            "projects[0].description",
            "experiences[0].role",
            "experiences[0].achievements[0].description",
            "personal_info.city",
        ),
    )

    assert result is source


def test_mixed_context_prioritizes_supported_path_and_preserves_other_sections() -> None:
    source = candidate()

    result = GroundedStandaloneCandidateOptimizer().optimize(
        source,
        plan("technologies[1].name", "projects[0].description"),
    )

    assert result.technologies[0] is source.technologies[1]
    assert result.personal_info is source.personal_info
    assert result.contact_info is source.contact_info
    assert result.experiences is source.experiences
    assert result.education is source.education
    assert result.projects is source.projects
    assert result.experiences is source.experiences
    assert result.skills is source.skills
    assert result.tools is source.tools
    assert result.languages is source.languages
    assert result.certifications is source.certifications


@pytest.mark.parametrize("path", ["technologies[999].name", "skills[999].level"])
def test_nonexistent_provenance_path_fails_closed(path: str) -> None:
    source = candidate()

    with pytest.raises(OptimizationProposalGroundingError):
        GroundedStandaloneCandidateOptimizer().optimize(source, plan(path))

    assert source == candidate()
