import json
from types import SimpleNamespace

import pytest

from resume_ai.modules.candidate.domain.entities import (
    Achievement,
    Candidate,
    ContactInfo,
    Experience,
    PersonalInfo,
)
from resume_ai.modules.candidate.domain.value_objects import YearMonth
from resume_ai.modules.optimization.application.exceptions import OptimizationProposalGroundingError
from resume_ai.modules.optimization.application.proposals import (
    CandidateAchievementOptimizationProposal,
    ExperienceAchievementOptimizationProposal,
    OptimizedAchievementStatementProposal,
)
from resume_ai.modules.optimization.infrastructure import (
    semantic_achievement_optimization_truth_gate,
)

A = "experiences[0].achievements[0].description"


def candidate() -> Candidate:
    return Candidate(
        PersonalInfo("Jane Doe", "Curitiba", "PR", "Brazil"),
        ContactInfo("jane@example.test", "+55"),
        experiences=(
            Experience(
                "Example",
                "Analyst",
                YearMonth("2020-01"),
                achievements=(Achievement("Redução de 40% no tempo de atendimento."),),
            ),
        ),
    )


class FakeClient:
    def __init__(self, supported: bool) -> None:
        self.supported = supported
        self.calls: list[str] = []

    def generate(self, *, system_prompt, user_prompt, response_model):
        self.calls.append(user_prompt)
        return SimpleNamespace(fully_supported=self.supported)


def proposal(text: str, path: str = A) -> CandidateAchievementOptimizationProposal:
    return CandidateAchievementOptimizationProposal(
        (
            ExperienceAchievementOptimizationProposal(
                0, (OptimizedAchievementStatementProposal(text, (path,), (0,)),)
            ),
        )
    )


def test_truth_gate_accepts_faithful_paraphrase_and_uses_only_source_achievement() -> None:
    fake = FakeClient(True)
    semantic_achievement_optimization_truth_gate.AISemanticAchievementOptimizationTruthGate(
        fake
    ).validate(candidate(), proposal("Reduziu em 40% o tempo de atendimento."))

    assert json.loads(fake.calls[0]) == {
        "proposed_text": "Reduziu em 40% o tempo de atendimento.",
        "source_evidence": [{"path": A, "text": "Redução de 40% no tempo de atendimento."}],
    }


@pytest.mark.parametrize(
    "text",
    [
        "Redução de 40% no tempo de atendimento.",
        "Redução de 40% usando Python.",
        "Aumentou a satisfação de clientes em 50%.",
    ],
)
def test_truth_gate_rejects_invented_facts_when_ai_reports_unsupported(text: str) -> None:
    with pytest.raises(OptimizationProposalGroundingError):
        semantic_achievement_optimization_truth_gate.AISemanticAchievementOptimizationTruthGate(
            FakeClient(False)
        ).validate(candidate(), proposal(text))


def test_invalid_non_achievement_source_fails_before_ai() -> None:
    fake = FakeClient(True)
    with pytest.raises(OptimizationProposalGroundingError):
        semantic_achievement_optimization_truth_gate.AISemanticAchievementOptimizationTruthGate(
            fake
        ).validate(candidate(), proposal("x", "experiences[0].activities[0].description"))
    assert fake.calls == []
