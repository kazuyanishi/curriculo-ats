import json
from types import SimpleNamespace

import pytest

from resume_ai.modules.candidate.domain.entities import (
    Candidate,
    ContactInfo,
    PersonalInfo,
    Project,
)
from resume_ai.modules.optimization.application.exceptions import (
    OptimizationProposalGroundingError,
)
from resume_ai.modules.optimization.application.proposals import (
    CandidateProjectOptimizationProposal,
    OptimizedProjectDescriptionProposal,
    ProjectOptimizationProposal,
)
from resume_ai.modules.optimization.infrastructure import (
    semantic_project_optimization_truth_gate,
)

PROJECT_DESCRIPTION = "projects[0].description"


def candidate() -> Candidate:
    return Candidate(
        PersonalInfo("Jane Doe", "Curitiba", "PR", "Brazil"),
        ContactInfo("jane@example.test", "+55"),
        projects=(Project("Resume AI", "Developed a Python application."),),
    )


class FakeClient:
    def __init__(self, supported: bool) -> None:
        self.supported = supported
        self.calls: list[str] = []

    def generate(self, *, system_prompt, user_prompt, response_model):
        self.calls.append(user_prompt)
        return SimpleNamespace(fully_supported=self.supported)


def proposal(text: str, path: str = PROJECT_DESCRIPTION) -> CandidateProjectOptimizationProposal:
    return CandidateProjectOptimizationProposal(
        (
            ProjectOptimizationProposal(
                0,
                OptimizedProjectDescriptionProposal(text, (path,), (0,)),
            ),
        )
    )


def test_truth_gate_accepts_supported_project_description_with_isolated_source() -> None:
    fake = FakeClient(True)

    semantic_project_optimization_truth_gate.AISemanticProjectOptimizationTruthGate(fake).validate(
        candidate(), proposal("Python application developed.")
    )

    assert json.loads(fake.calls[0]) == {
        "proposed_text": "Python application developed.",
        "source_evidence": [
            {"path": PROJECT_DESCRIPTION, "text": "Developed a Python application."}
        ],
    }
    assert "Resume AI" not in fake.calls[0]


@pytest.mark.parametrize(
    "text",
    [
        "Developed a Python application with FastAPI.",
        "Increased customer revenue by 50%.",
    ],
)
def test_truth_gate_rejects_unsupported_project_facts(text: str) -> None:
    with pytest.raises(OptimizationProposalGroundingError):
        semantic_project_optimization_truth_gate.AISemanticProjectOptimizationTruthGate(
            FakeClient(False)
        ).validate(candidate(), proposal(text))


@pytest.mark.parametrize(
    "path",
    ["projects[0].name", "projects[1].description", "experiences[0].activities[0].description"],
)
def test_truth_gate_rejects_cross_or_non_description_sources_before_ai(path: str) -> None:
    fake = FakeClient(True)

    with pytest.raises(OptimizationProposalGroundingError):
        semantic_project_optimization_truth_gate.AISemanticProjectOptimizationTruthGate(
            fake
        ).validate(candidate(), proposal("Project description.", path))

    assert fake.calls == []
