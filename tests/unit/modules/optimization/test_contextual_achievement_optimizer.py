import json

import pytest

from resume_ai.modules.candidate.domain.entities import (
    Achievement,
    Activity,
    Candidate,
    ContactInfo,
    Experience,
    PersonalInfo,
)
from resume_ai.modules.candidate.domain.value_objects import YearMonth
from resume_ai.modules.jobs.domain.entities import CriterionCategory, JobCriterion
from resume_ai.modules.matching.domain.entities import CriterionMatch, MatchingResult, MatchStatus
from resume_ai.modules.optimization.application.exceptions import OptimizationProposalGroundingError
from resume_ai.modules.optimization.application.planning import (
    AchievementOptimizationContext,
    CandidateOptimizationPlan,
)
from resume_ai.modules.optimization.application.proposals import (
    CandidateAchievementOptimizationProposal,
    ExperienceAchievementOptimizationProposal,
    OptimizedAchievementStatementProposal,
)
from resume_ai.modules.optimization.infrastructure.contextual_achievement_optimizer import (
    AIContextualAchievementOptimizer,
)
from resume_ai.modules.optimization.infrastructure.contextual_achievement_schemas import (
    CandidateAchievementOptimizationAIResponse,
)

A = "experiences[0].achievements[0].description"
B = "experiences[0].achievements[1].description"
ACTIVITY = "experiences[0].activities[0].description"


def candidate() -> Candidate:
    return Candidate(
        PersonalInfo("Jane Doe", "Curitiba", "PR", "Brazil"),
        ContactInfo("jane@example.test", "+55"),
        experiences=(
            Experience(
                "Example",
                "Support Analyst",
                YearMonth("2020-01"),
                activities=(Activity("Atendimento de chamados."),),
                achievements=(
                    Achievement("Redução de 40% no tempo de atendimento."),
                    Achievement("Padronização de documentação técnica."),
                ),
            ),
        ),
    )


def matching(*paths: tuple[str, ...]) -> MatchingResult:
    return MatchingResult(
        tuple(
            CriterionMatch(
                JobCriterion(CriterionCategory.OTHER, f"criterion-{index}", f"evidence-{index}"),
                MatchStatus.MATCHED,
                evidence_paths,
            )
            for index, evidence_paths in enumerate(paths)
        )
    )


class FakeClient:
    def __init__(self, response: CandidateAchievementOptimizationAIResponse) -> None:
        self.response = response
        self.calls: list[tuple[str, str, type]] = []

    def generate(self, *, system_prompt, user_prompt, response_model):
        self.calls.append((system_prompt, user_prompt, response_model))
        return self.response


class RecordingTruthGate:
    def __init__(self) -> None:
        self.calls = []

    def validate(self, candidate, proposal) -> None:
        self.calls.append((candidate, proposal))


def response(items: list[dict[str, object]]) -> CandidateAchievementOptimizationAIResponse:
    return CandidateAchievementOptimizationAIResponse.model_validate({"experiences": items})


def test_optimizer_uses_only_authorized_achievement_context_payload() -> None:
    plan = CandidateOptimizationPlan(
        achievement_contexts=(AchievementOptimizationContext(0, (1,), (B,)),)
    )
    fake = FakeClient(response([{"experience_index": 0, "statements": []}]))

    result = AIContextualAchievementOptimizer(fake, RecordingTruthGate()).optimize(
        candidate(), matching((A,), (B,)), plan
    )

    assert result == CandidateAchievementOptimizationProposal(
        (ExperienceAchievementOptimizationProposal(0),)
    )
    payload = json.loads(fake.calls[0][1])
    assert payload == {
        "achievement_contexts": [
            {
                "experience_index": 0,
                "criteria": [
                    {
                        "match_index": 1,
                        "category": "other",
                        "value": "criterion-1",
                        "evidence": "evidence-1",
                        "importance": "unspecified",
                        "candidate_evidence_paths": [B],
                    }
                ],
                "candidate_evidence": [
                    {"path": B, "text": candidate().experiences[0].achievements[1].description}
                ],
            }
        ]
    }
    encoded = fake.calls[0][1]
    for excluded in ("Jane Doe", "jane@example.test", "Atendimento de chamados.", "40%"):
        assert excluded not in encoded


def test_zero_context_uses_no_ai_call_and_validates_empty_proposal() -> None:
    fake = FakeClient(response([]))
    truth_gate = RecordingTruthGate()

    result = AIContextualAchievementOptimizer(fake, truth_gate).optimize(
        candidate(), MatchingResult(), CandidateOptimizationPlan()
    )

    assert result == CandidateAchievementOptimizationProposal()
    assert fake.calls == []
    assert truth_gate.calls[0][1] is result


@pytest.mark.parametrize(
    "items",
    [
        [{"experience_index": 0, "statements": []}, {"experience_index": 0, "statements": []}],
        [],
        [
            {
                "experience_index": 0,
                "statements": [
                    {"text": "x", "source_paths": [ACTIVITY], "target_match_indexes": [0]}
                ],
            }
        ],
        [
            {
                "experience_index": 0,
                "statements": [{"text": "x", "source_paths": [A], "target_match_indexes": [1]}],
            }
        ],
    ],
)
def test_invalid_context_or_source_target_binding_fails_closed(
    items: list[dict[str, object]],
) -> None:
    plan = CandidateOptimizationPlan(
        achievement_contexts=(AchievementOptimizationContext(0, (0,), (A,)),)
    )
    with pytest.raises(OptimizationProposalGroundingError):
        AIContextualAchievementOptimizer(
            FakeClient(response(items)), RecordingTruthGate()
        ).optimize(candidate(), matching((A,), (B,)), plan)


def test_valid_multi_target_preserves_source_target_identity() -> None:
    plan = CandidateOptimizationPlan(
        achievement_contexts=(AchievementOptimizationContext(0, (0, 1), (A,)),)
    )
    fake = FakeClient(
        response(
            [
                {
                    "experience_index": 0,
                    "statements": [
                        {
                            "text": "Reduziu em 40% o tempo de atendimento.",
                            "source_paths": [A],
                            "target_match_indexes": [0, 1],
                        }
                    ],
                }
            ]
        )
    )

    proposal = AIContextualAchievementOptimizer(fake, RecordingTruthGate()).optimize(
        candidate(), matching((A,), (A,)), plan
    )

    assert proposal.experiences[0].statements == (
        OptimizedAchievementStatementProposal(
            "Reduziu em 40% o tempo de atendimento.", (A,), (0, 1)
        ),
    )
