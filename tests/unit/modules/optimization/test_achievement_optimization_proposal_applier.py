import pytest

from resume_ai.modules.candidate.domain.entities import (
    Achievement,
    Activity,
    Candidate,
    ContactInfo,
    Experience,
    PersonalInfo,
    Skill,
)
from resume_ai.modules.candidate.domain.value_objects import YearMonth
from resume_ai.modules.optimization.application.exceptions import OptimizationProposalGroundingError
from resume_ai.modules.optimization.application.proposals import (
    CandidateAchievementOptimizationProposal,
    ExperienceAchievementOptimizationProposal,
    OptimizedAchievementStatementProposal,
)
from resume_ai.modules.optimization.application.services import (
    DeterministicCandidateAchievementOptimizationProposalApplier,
)


def candidate() -> Candidate:
    return Candidate(
        PersonalInfo("Jane Doe", "Curitiba", "PR", "Brazil"),
        ContactInfo("jane@example.test", "+55"),
        experiences=(
            Experience(
                "Example",
                "Analyst",
                YearMonth("2020-01"),
                activities=(Activity("Activity"),),
                achievements=(
                    Achievement("A"),
                    Achievement("X"),
                    Achievement("B"),
                    Achievement("Y"),
                ),
            ),
        ),
        skills=(Skill("Python"),),
    )


def proposal(
    text: str = "A optimized", indexes: tuple[int, ...] = (0,)
) -> CandidateAchievementOptimizationProposal:
    return CandidateAchievementOptimizationProposal(
        (
            ExperienceAchievementOptimizationProposal(
                0,
                (
                    OptimizedAchievementStatementProposal(
                        text,
                        tuple(
                            f"experiences[0].achievements[{index}].description" for index in indexes
                        ),
                        (0,),
                    ),
                ),
            ),
        )
    )


def apply(source: Candidate, value: CandidateAchievementOptimizationProposal) -> Candidate:
    return DeterministicCandidateAchievementOptimizationProposalApplier().apply(source, value)


def test_empty_proposal_preserves_candidate_identity() -> None:
    source = candidate()
    assert apply(source, CandidateAchievementOptimizationProposal()) is source


def test_replacement_is_non_destructive_and_preserves_activities_and_sections() -> None:
    source = candidate()
    result = apply(source, proposal("B optimized", (2,)))

    assert tuple(item.description for item in result.experiences[0].achievements) == (
        "A",
        "X",
        "B optimized",
        "Y",
    )
    assert result.experiences[0].activities is source.experiences[0].activities
    assert result.experiences[0].company == source.experiences[0].company
    assert result.experiences[0].role == source.experiences[0].role
    assert result.skills is source.skills
    assert source == candidate()


def test_combined_achievements_use_the_smallest_original_index() -> None:
    result = apply(candidate(), proposal("AB", (0, 2)))
    assert tuple(item.description for item in result.experiences[0].achievements) == (
        "AB",
        "X",
        "Y",
    )


def test_proposal_order_does_not_reorder_independent_achievements() -> None:
    source = candidate()
    result = apply(
        source,
        CandidateAchievementOptimizationProposal(
            (
                ExperienceAchievementOptimizationProposal(
                    0,
                    (
                        OptimizedAchievementStatementProposal(
                            "B2", ("experiences[0].achievements[2].description",), (0,)
                        ),
                        OptimizedAchievementStatementProposal(
                            "A0", ("experiences[0].achievements[0].description",), (0,)
                        ),
                    ),
                ),
            )
        ),
    )
    assert tuple(item.description for item in result.experiences[0].achievements) == (
        "A0",
        "X",
        "B2",
        "Y",
    )


@pytest.mark.parametrize(
    "path",
    [
        "experiences[0].activities[0].description",
        "experiences[0].role",
        "experiences[0].company",
        "experiences[1].achievements[0].description",
        "experiences[0].achievements[99].description",
        "skills[0].name",
    ],
)
def test_non_achievement_or_invalid_paths_fail_closed(path: str) -> None:
    source = candidate()
    invalid = CandidateAchievementOptimizationProposal(
        (
            ExperienceAchievementOptimizationProposal(
                0, (OptimizedAchievementStatementProposal("Invalid", (path,), (0,)),)
            ),
        )
    )
    with pytest.raises(OptimizationProposalGroundingError):
        apply(source, invalid)
    assert source == candidate()


def test_overlapping_sources_fail_closed() -> None:
    source = candidate()
    invalid = CandidateAchievementOptimizationProposal(
        (
            ExperienceAchievementOptimizationProposal(
                0,
                (
                    OptimizedAchievementStatementProposal(
                        "First", ("experiences[0].achievements[0].description",), (0,)
                    ),
                    OptimizedAchievementStatementProposal(
                        "Overlap",
                        (
                            "experiences[0].achievements[0].description",
                            "experiences[0].achievements[1].description",
                        ),
                        (0,),
                    ),
                ),
            ),
        )
    )
    with pytest.raises(OptimizationProposalGroundingError):
        apply(source, invalid)
