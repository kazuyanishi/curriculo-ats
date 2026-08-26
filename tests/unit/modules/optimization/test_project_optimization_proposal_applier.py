import pytest

from resume_ai.modules.candidate.domain.entities import (
    Candidate,
    ContactInfo,
    PersonalInfo,
    Project,
)
from resume_ai.modules.candidate.domain.value_objects import YearMonth
from resume_ai.modules.optimization.application.exceptions import OptimizationProposalGroundingError
from resume_ai.modules.optimization.application.proposals import (
    CandidateProjectOptimizationProposal,
    OptimizedProjectDescriptionProposal,
    ProjectOptimizationProposal,
)
from resume_ai.modules.optimization.application.services import (
    DeterministicCandidateProjectOptimizationProposalApplier,
)


def candidate() -> Candidate:
    return Candidate(
        PersonalInfo("Jane", "Curitiba", "PR", "Brazil"),
        ContactInfo("jane@example.test", "+55"),
        projects=(
            Project(
                "A",
                "Description A",
                YearMonth("2020-01"),
                technologies=("Python",),
            ),
            Project("B", "Description B"),
        ),
    )


def test_project_applier_replaces_only_authorized_description_and_preserves_integrity() -> None:
    source = candidate()
    proposal = CandidateProjectOptimizationProposal(
        (
            ProjectOptimizationProposal(
                0,
                OptimizedProjectDescriptionProposal(
                    "Improved A", ("projects[0].description",), (0,)
                ),
            ),
        )
    )
    result = DeterministicCandidateProjectOptimizationProposalApplier().apply(source, proposal)
    assert result.projects[0].description == "Improved A"
    assert result.projects[0].name == source.projects[0].name
    assert result.projects[0].start_date is source.projects[0].start_date
    assert result.projects[0].technologies is source.projects[0].technologies
    assert result.projects[1] is source.projects[1]
    assert source == candidate()


@pytest.mark.parametrize(
    "path",
    [
        "projects[0].name",
        "projects[1].description",
        "experiences[0].activities[0].description",
    ],
)
def test_project_applier_rejects_wrong_source_path(path: str) -> None:
    proposal = CandidateProjectOptimizationProposal(
        (
            ProjectOptimizationProposal(
                0,
                OptimizedProjectDescriptionProposal("Invalid", (path,), (0,)),
            ),
        )
    )
    with pytest.raises(OptimizationProposalGroundingError):
        DeterministicCandidateProjectOptimizationProposalApplier().apply(candidate(), proposal)
