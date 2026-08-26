import pytest

from resume_ai.modules.candidate.domain.entities import Candidate, ContactInfo, PersonalInfo
from resume_ai.modules.matching.domain.entities import MatchingResult
from resume_ai.modules.optimization.application.planning import CandidateOptimizationPlan
from resume_ai.modules.optimization.application.proposals import (
    CandidateAchievementOptimizationProposal,
    CandidateOptimizationProposal,
)
from resume_ai.modules.optimization.application.services import GroundedCandidateOptimizer


def candidate() -> Candidate:
    return Candidate(
        PersonalInfo("Jane Doe", "Curitiba", "PR", "Brazil"),
        ContactInfo("jane@example.test", "+55"),
    )


def test_pipeline_orders_stages_and_gives_both_ai_optimizers_the_original_candidate() -> None:
    events: list[str] = []
    source = candidate()
    after_activities = candidate()
    after_achievements = candidate()
    final = candidate()
    plan = CandidateOptimizationPlan()

    class Planner:
        def execute(self, received_candidate, matching):
            events.append("planner")
            assert received_candidate is source
            return plan

    class ActivityOptimizer:
        def optimize(self, received_candidate, matching, received_plan):
            events.append("activity_optimizer")
            assert received_candidate is source
            assert received_plan is plan
            return CandidateOptimizationProposal()

    class AchievementOptimizer:
        def optimize(self, received_candidate, matching, received_plan):
            events.append("achievement_optimizer")
            assert received_candidate is source
            assert received_plan is plan
            return CandidateAchievementOptimizationProposal()

    class ActivityApplier:
        def apply(self, received_candidate, proposal):
            events.append("activity_applier")
            assert received_candidate is source
            return after_activities

    class AchievementApplier:
        def apply(self, received_candidate, proposal):
            events.append("achievement_applier")
            assert received_candidate is after_activities
            return after_achievements

    class StandaloneOptimizer:
        def optimize(self, received_candidate, received_plan):
            events.append("standalone_optimizer")
            assert received_candidate is after_achievements
            assert received_plan is plan
            return final

    result = GroundedCandidateOptimizer(
        Planner(),  # type: ignore[arg-type]
        ActivityOptimizer(),  # type: ignore[arg-type]
        AchievementOptimizer(),  # type: ignore[arg-type]
        ActivityApplier(),  # type: ignore[arg-type]
        AchievementApplier(),  # type: ignore[arg-type]
        StandaloneOptimizer(),  # type: ignore[arg-type]
    ).optimize(source, MatchingResult())

    assert result is final
    assert events == [
        "planner",
        "activity_optimizer",
        "achievement_optimizer",
        "activity_applier",
        "achievement_applier",
        "standalone_optimizer",
    ]


@pytest.mark.parametrize("failure", ["achievement_optimizer", "achievement_applier"])
def test_pipeline_stops_before_later_stage_when_achievement_stage_fails(failure: str) -> None:
    events: list[str] = []

    class Planner:
        def execute(self, candidate, matching):
            events.append("planner")
            return CandidateOptimizationPlan()

    class ActivityOptimizer:
        def optimize(self, candidate, matching, plan):
            events.append("activity_optimizer")
            return CandidateOptimizationProposal()

    class AchievementOptimizer:
        def optimize(self, candidate, matching, plan):
            events.append("achievement_optimizer")
            if failure == "achievement_optimizer":
                raise RuntimeError("failure")
            return CandidateAchievementOptimizationProposal()

    class ActivityApplier:
        def apply(self, candidate, proposal):
            events.append("activity_applier")
            return candidate

    class AchievementApplier:
        def apply(self, candidate, proposal):
            events.append("achievement_applier")
            if failure == "achievement_applier":
                raise RuntimeError("failure")
            return candidate

    class StandaloneOptimizer:
        def optimize(self, candidate, plan):
            events.append("standalone_optimizer")
            return candidate

    with pytest.raises(RuntimeError, match="failure"):
        GroundedCandidateOptimizer(
            Planner(),  # type: ignore[arg-type]
            ActivityOptimizer(),  # type: ignore[arg-type]
            AchievementOptimizer(),  # type: ignore[arg-type]
            ActivityApplier(),  # type: ignore[arg-type]
            AchievementApplier(),  # type: ignore[arg-type]
            StandaloneOptimizer(),  # type: ignore[arg-type]
        ).optimize(candidate(), MatchingResult())

    assert (
        events
        == {
            "achievement_optimizer": ["planner", "activity_optimizer", "achievement_optimizer"],
            "achievement_applier": [
                "planner",
                "activity_optimizer",
                "achievement_optimizer",
                "activity_applier",
                "achievement_applier",
            ],
        }[failure]
    )
