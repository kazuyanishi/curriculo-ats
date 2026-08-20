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
                activities=(Activity("A"), Activity("X"), Activity("B"), Activity("Y")),
                achievements=(Achievement("Achievement"),),
            ),
            Experience(
                "Example One",
                "Developer",
                YearMonth("2021-01"),
                activities=(Activity("Other"),),
            ),
        ),
        education=(Education("University", "Computer Science", EducationStatus.COMPLETED),),
        skills=(Skill("Communication"),),
        technologies=(Technology("Python"),),
        tools=(Tool("Jira"),),
        languages=(Language("English", LanguageLevel.FLUENT),),
        certifications=(Certification("Certification", "Issuer"),),
        projects=(Project("Project", "Description"),),
    )


def statement(
    text: str,
    indexes: tuple[int, ...] = (0,),
    experience_index: int = 0,
) -> OptimizedExperienceStatementProposal:
    return OptimizedExperienceStatementProposal(
        text,
        tuple(
            f"experiences[{experience_index}].activities[{index}].description" for index in indexes
        ),
        (0,),
    )


def apply(source: Candidate, proposal: CandidateOptimizationProposal) -> Candidate:
    return DeterministicCandidateOptimizationProposalApplier().apply(source, proposal)


def test_empty_proposal_and_empty_statements_preserve_original_candidate() -> None:
    source = candidate()

    assert apply(source, CandidateOptimizationProposal()) is source
    assert (
        apply(source, CandidateOptimizationProposal((ExperienceOptimizationProposal(0),))) is source
    )


def test_replaces_only_the_referenced_activity() -> None:
    source = candidate()
    proposal = CandidateOptimizationProposal(
        (ExperienceOptimizationProposal(0, (statement("BX", (2,)),)),)
    )

    result = apply(source, proposal)

    assert tuple(item.description for item in result.experiences[0].activities) == (
        "A",
        "X",
        "BX",
        "Y",
    )
    assert result.experiences[0].achievements is source.experiences[0].achievements


def test_combined_activities_are_inserted_at_the_smallest_original_index() -> None:
    source = candidate()
    proposal = CandidateOptimizationProposal(
        (ExperienceOptimizationProposal(0, (statement("AB", (0, 2)),)),)
    )

    result = apply(source, proposal)

    assert tuple(item.description for item in result.experiences[0].activities) == ("AB", "X", "Y")


def test_proposal_order_does_not_reorder_independent_activities() -> None:
    source = candidate()
    proposal = CandidateOptimizationProposal(
        (ExperienceOptimizationProposal(0, (statement("B2", (2,)), statement("A0", (0,)))),)
    )

    result = apply(source, proposal)

    assert tuple(item.description for item in result.experiences[0].activities) == (
        "A0",
        "X",
        "B2",
        "Y",
    )


def test_omitted_activities_and_unmentioned_experiences_are_shared() -> None:
    source = candidate()
    proposal = CandidateOptimizationProposal(
        (ExperienceOptimizationProposal(0, (statement("A0"),)),)
    )

    result = apply(source, proposal)

    assert tuple(item.description for item in result.experiences[0].activities) == (
        "A0",
        "X",
        "B",
        "Y",
    )
    assert result.experiences[1] is source.experiences[1]
    assert result.education is source.education
    assert result.skills is source.skills
    assert result.technologies is source.technologies
    assert result.tools is source.tools
    assert result.languages is source.languages
    assert result.certifications is source.certifications
    assert result.projects is source.projects


def test_multiple_experiences_apply_without_reordering_candidate() -> None:
    source = candidate()
    proposal = CandidateOptimizationProposal(
        (
            ExperienceOptimizationProposal(1, (statement("Other optimized", (0,), 1),)),
            ExperienceOptimizationProposal(0, (statement("A optimized", (0,)),)),
        )
    )

    result = apply(source, proposal)

    assert [experience.company for experience in result.experiences] == [
        "Example Zero",
        "Example One",
    ]
    assert result.experiences[0].activities[0] == Activity("A optimized")
    assert result.experiences[1].activities == (Activity("Other optimized"),)


def test_overlapping_sources_fail_before_candidate_is_built() -> None:
    source = candidate()
    proposal = CandidateOptimizationProposal(
        (
            ExperienceOptimizationProposal(
                0, (statement("First", (0,)), statement("Overlap", (0, 1)))
            ),
        )
    )

    with pytest.raises(OptimizationProposalGroundingError):
        apply(source, proposal)

    assert source == candidate()


@pytest.mark.parametrize(
    "path",
    [
        "experiences[0].role",
        "experiences[0].company",
        "experiences[0].achievements[0].description",
        "experiences[0].start_date",
        "skills[0].name",
        "experiences[1].activities[0].description",
        "experiences[0].activities[99].description",
    ],
)
def test_non_activity_or_invalid_source_path_fails_closed(path: str) -> None:
    source = candidate()
    proposal = CandidateOptimizationProposal(
        (
            ExperienceOptimizationProposal(
                0,
                (OptimizedExperienceStatementProposal("Invalid", (path,), (0,)),),
            ),
        )
    )

    with pytest.raises(OptimizationProposalGroundingError):
        apply(source, proposal)


def test_duplicate_experience_indexes_and_inputs_remain_immutable() -> None:
    source = candidate()
    proposal = CandidateOptimizationProposal(
        (
            ExperienceOptimizationProposal(0, (statement("First"),)),
            ExperienceOptimizationProposal(0, (statement("Second", (1,)),)),
        )
    )

    with pytest.raises(OptimizationProposalGroundingError):
        apply(source, proposal)

    assert source == candidate()
    assert proposal.experiences[0].statements[0].text == "First"


def test_applier_contract_has_no_ai_job_or_matching_dependency() -> None:
    parameters = inspect.signature(CandidateOptimizationProposalApplier.apply).parameters
    assert list(parameters) == ["self", "candidate", "proposal"]
    assert not inspect.signature(DeterministicCandidateOptimizationProposalApplier).parameters
