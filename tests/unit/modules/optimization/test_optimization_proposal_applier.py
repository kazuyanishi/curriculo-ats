import inspect

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
    ProfessionalLinks,
    Project,
    Skill,
    Technology,
    Tool,
)
from resume_ai.modules.candidate.domain.value_objects import YearMonth
from resume_ai.modules.optimization.application.exceptions import OptimizationProposalGroundingError
from resume_ai.modules.optimization.application.ports import CandidateOptimizationProposalApplier
from resume_ai.modules.optimization.application.proposals import (
    CandidateOptimizationProposal,
    ExperienceOptimizationProposal,
    OptimizedExperienceStatementProposal,
)
from resume_ai.modules.optimization.application.services import (
    DeterministicCandidateOptimizationProposalApplier,
)


def candidate() -> Candidate:
    return Candidate(
        personal_info=PersonalInfo("Jane Doe", "Curitiba", "PR", "Brazil"),
        contact_info=ContactInfo("jane@example.test", "+55 41 99999-0000"),
        professional_links=ProfessionalLinks(github="https://github.com/jane"),
        experiences=(
            Experience(
                "Example Zero",
                "Support Analyst",
                YearMonth("2020-01"),
                YearMonth("2024-01"),
                activities=(Activity("Atendimento de chamados."), Activity("Organização no Jira.")),
                achievements=(Achievement("Melhoria de processo."),),
            ),
            Experience(
                "Example One",
                "Developer",
                YearMonth("2021-01"),
                activities=(Activity("Desenvolvimento Python."),),
            ),
            Experience(
                "Example Two",
                "Analyst",
                YearMonth("2022-01"),
                activities=(Activity("Análise de dados."),),
            ),
        ),
        education=(Education("Example University", "Computer Science", EducationStatus.COMPLETED),),
        skills=(Skill("Communication"),),
        technologies=(Technology("Python"),),
        tools=(Tool("Jira"),),
        languages=(Language("English", LanguageLevel.FLUENT),),
        certifications=(Certification("Certification", "Issuer"),),
        projects=(Project("Project", "Description"),),
    )


def statement(text: str) -> OptimizedExperienceStatementProposal:
    return OptimizedExperienceStatementProposal(
        text,
        ("experiences[0].activities[0].description",),
        (0,),
    )


def proposal(*items: ExperienceOptimizationProposal) -> CandidateOptimizationProposal:
    return CandidateOptimizationProposal(items)


def apply(source: Candidate, input_proposal: CandidateOptimizationProposal) -> Candidate:
    return DeterministicCandidateOptimizationProposalApplier().apply(source, input_proposal)


def test_empty_proposal_returns_the_original_candidate() -> None:
    source = candidate()

    assert apply(source, CandidateOptimizationProposal()) is source


def test_experience_with_empty_statements_preserves_its_activities() -> None:
    source = candidate()
    input_proposal = proposal(ExperienceOptimizationProposal(0))

    result = apply(source, input_proposal)

    assert result is source
    assert result.experiences[0].activities is source.experiences[0].activities


def test_applies_one_experience_by_replacing_only_activities() -> None:
    source = candidate()
    input_proposal = proposal(ExperienceOptimizationProposal(0, (statement("Chamados via Jira."),)))

    result = apply(source, input_proposal)

    optimized = result.experiences[0]
    original = source.experiences[0]
    assert result is not source
    assert optimized.activities == (Activity("Chamados via Jira."),)
    assert optimized.company == original.company
    assert optimized.role == original.role
    assert optimized.start_date is original.start_date
    assert optimized.end_date is original.end_date
    assert optimized.achievements is original.achievements


def test_preserves_statement_order_and_duplicates() -> None:
    source = candidate()
    first = statement("Primeiro.")
    second = statement("Segundo.")
    duplicate = statement("Primeiro.")

    result = apply(source, proposal(ExperienceOptimizationProposal(0, (first, second, duplicate))))

    assert tuple(item.description for item in result.experiences[0].activities) == (
        "Primeiro.",
        "Segundo.",
        "Primeiro.",
    )


def test_multiple_experiences_apply_at_indexes_without_reordering_candidate() -> None:
    source = candidate()
    input_proposal = proposal(
        ExperienceOptimizationProposal(2, (statement("Experiência dois."),)),
        ExperienceOptimizationProposal(0, (statement("Experiência zero."),)),
    )

    result = apply(source, input_proposal)

    assert [item.company for item in result.experiences] == [
        "Example Zero",
        "Example One",
        "Example Two",
    ]
    assert result.experiences[0].activities == (Activity("Experiência zero."),)
    assert result.experiences[2].activities == (Activity("Experiência dois."),)
    assert result.experiences[1] is source.experiences[1]


def test_unmentioned_experiences_and_other_candidate_sections_are_shared() -> None:
    source = candidate()

    result = apply(source, proposal(ExperienceOptimizationProposal(1, (statement("Novo texto."),))))

    assert result.experiences[0] is source.experiences[0]
    assert result.experiences[2] is source.experiences[2]
    assert result.personal_info is source.personal_info
    assert result.contact_info is source.contact_info
    assert result.professional_links is source.professional_links
    assert result.education is source.education
    assert result.skills is source.skills
    assert result.technologies is source.technologies
    assert result.tools is source.tools
    assert result.languages is source.languages
    assert result.certifications is source.certifications
    assert result.projects is source.projects


@pytest.mark.parametrize(
    "input_proposal",
    [
        proposal(ExperienceOptimizationProposal(3, (statement("Invalid."),))),
        proposal(
            ExperienceOptimizationProposal(0, (statement("First."),)),
            ExperienceOptimizationProposal(0, (statement("Second."),)),
        ),
    ],
)
def test_invalid_or_duplicate_experience_indexes_fail_closed(input_proposal) -> None:
    source = candidate()

    with pytest.raises(OptimizationProposalGroundingError):
        apply(source, input_proposal)

    assert source == candidate()


def test_candidate_and_proposal_are_immutable() -> None:
    source = candidate()
    input_proposal = proposal(ExperienceOptimizationProposal(0, (statement("Novo texto."),)))

    result = apply(source, input_proposal)

    assert source == candidate()
    assert input_proposal == proposal(
        ExperienceOptimizationProposal(0, (statement("Novo texto."),))
    )
    assert result.experiences[0].activities != source.experiences[0].activities


def test_applier_contract_has_no_ai_job_or_matching_dependency() -> None:
    parameters = inspect.signature(CandidateOptimizationProposalApplier.apply).parameters
    assert list(parameters) == ["self", "candidate", "proposal"]
    assert not inspect.signature(DeterministicCandidateOptimizationProposalApplier).parameters
