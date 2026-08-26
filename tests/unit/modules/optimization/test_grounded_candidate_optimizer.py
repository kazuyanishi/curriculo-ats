from dataclasses import dataclass

import pytest

from resume_ai.modules.candidate.domain.entities import (
    Achievement,
    Activity,
    Candidate,
    ContactInfo,
    Experience,
    PersonalInfo,
    Skill,
    Technology,
)
from resume_ai.modules.candidate.domain.value_objects import YearMonth
from resume_ai.modules.jobs.domain.entities import CriterionCategory, JobCriterion
from resume_ai.modules.matching.application.provenance import MatchingProvenanceGate
from resume_ai.modules.matching.domain.entities import CriterionMatch, MatchingResult, MatchStatus
from resume_ai.modules.optimization.application.planning import (
    BuildCandidateOptimizationPlan,
    CandidateOptimizationPlan,
)
from resume_ai.modules.optimization.application.proposals import (
    CandidateAchievementOptimizationProposal,
    CandidateOptimizationProposal,
)
from resume_ai.modules.optimization.application.services import (
    DeterministicCandidateOptimizationProposalApplier,
    GroundedCandidateOptimizer,
    GroundedStandaloneCandidateOptimizer,
)
from resume_ai.modules.optimization.infrastructure.contextual_experience_optimizer import (
    AIContextualExperienceOptimizer,
)
from resume_ai.modules.optimization.infrastructure.contextual_experience_schemas import (
    CandidateOptimizationAIResponse,
)
from resume_ai.modules.optimization.infrastructure.optimization_truth_gate_schemas import (
    OptimizationStatementTruthDecision,
)
from resume_ai.modules.optimization.infrastructure.semantic_optimization_truth_gate import (
    AISemanticOptimizationTruthGate,
)

ACTIVITY_PATH = "experiences[0].activities[0].description"
SKILL_PATH = "skills[1].name"


def candidate() -> Candidate:
    return Candidate(
        PersonalInfo("Jane Doe", "Curitiba", "PR", "Brazil"),
        ContactInfo("jane@example.test", "+55 41 99999-0000"),
        experiences=(
            Experience(
                "Example",
                "Support Analyst",
                YearMonth("2020-01"),
                activities=(Activity("Atendimento e acompanhamento de chamados."),),
            ),
        ),
        skills=(Skill("Python"), Skill("Communication")),
        technologies=(Technology("Docker"), Technology("PostgreSQL")),
    )


def matching(*matches: CriterionMatch) -> MatchingResult:
    return MatchingResult(matches)


def criterion(category: CriterionCategory, value: str) -> JobCriterion:
    return JobCriterion(category, value, f"{value} is required.")


class RecordingPlanner:
    def __init__(self, plan: CandidateOptimizationPlan, events: list[str]) -> None:
        self.plan = plan
        self.events = events
        self.received = None

    def execute(self, candidate: Candidate, matching: MatchingResult) -> CandidateOptimizationPlan:
        self.events.append("planner")
        self.received = (candidate, matching)
        return self.plan


class RecordingExperienceOptimizer:
    def __init__(self, proposal: CandidateOptimizationProposal, events: list[str]) -> None:
        self.proposal = proposal
        self.events = events
        self.received = None

    def optimize(self, candidate, matching, plan) -> CandidateOptimizationProposal:
        self.events.append("experience_optimizer")
        self.received = (candidate, matching, plan)
        return self.proposal


class RecordingApplier:
    def __init__(self, output: Candidate, events: list[str]) -> None:
        self.output = output
        self.events = events
        self.received = None

    def apply(self, candidate, proposal) -> Candidate:
        self.events.append("applier")
        self.received = (candidate, proposal)
        return self.output


class EmptyAchievementOptimizer:
    def optimize(self, candidate, matching, plan) -> CandidateAchievementOptimizationProposal:
        return CandidateAchievementOptimizationProposal()


class IdentityAchievementApplier:
    def apply(self, candidate, proposal) -> Candidate:
        return candidate


class RecordingStandaloneOptimizer:
    def __init__(self, output: Candidate, events: list[str]) -> None:
        self.output = output
        self.events = events
        self.received = None

    def optimize(self, candidate, plan) -> Candidate:
        self.events.append("standalone")
        self.received = (candidate, plan)
        return self.output


def test_orchestrator_runs_in_order_with_original_inputs() -> None:
    events: list[str] = []
    source = candidate()
    result = candidate()
    applied = candidate()
    matching_result = MatchingResult()
    plan = CandidateOptimizationPlan()
    proposal = CandidateOptimizationProposal()
    planner = RecordingPlanner(plan, events)
    experience_optimizer = RecordingExperienceOptimizer(proposal, events)
    applier = RecordingApplier(applied, events)
    standalone = RecordingStandaloneOptimizer(result, events)

    output = GroundedCandidateOptimizer(
        planner,  # type: ignore[arg-type]
        experience_optimizer,  # type: ignore[arg-type]
        EmptyAchievementOptimizer(),  # type: ignore[arg-type]
        applier,  # type: ignore[arg-type]
        IdentityAchievementApplier(),  # type: ignore[arg-type]
        standalone,  # type: ignore[arg-type]
    ).optimize(source, matching_result)

    assert events == ["planner", "experience_optimizer", "applier", "standalone"]
    assert planner.received == (source, matching_result)
    assert experience_optimizer.received == (source, matching_result, plan)
    assert applier.received == (source, proposal)
    assert standalone.received == (applied, plan)
    assert output is result


@pytest.mark.parametrize(
    "failing_stage", ["planner", "experience_optimizer", "applier", "standalone"]
)
def test_orchestrator_is_fail_closed(failing_stage: str) -> None:
    events: list[str] = []
    source = candidate()

    class FailingPlanner:
        def execute(self, candidate, matching):
            events.append("planner")
            if failing_stage == "planner":
                raise RuntimeError("planner failure")
            return CandidateOptimizationPlan()

    class FailingExperienceOptimizer:
        def optimize(self, candidate, matching, plan):
            events.append("experience_optimizer")
            if failing_stage == "experience_optimizer":
                raise RuntimeError("experience optimizer failure")
            return CandidateOptimizationProposal()

    class FailingApplier:
        def apply(self, candidate, proposal):
            events.append("applier")
            if failing_stage == "applier":
                raise RuntimeError("applier failure")
            return candidate

    class FailingStandaloneOptimizer:
        def optimize(self, candidate, plan):
            events.append("standalone")
            if failing_stage == "standalone":
                raise RuntimeError("standalone optimizer failure")
            raise AssertionError("standalone optimizer should not execute")

    with pytest.raises(RuntimeError):
        GroundedCandidateOptimizer(
            FailingPlanner(),  # type: ignore[arg-type]
            FailingExperienceOptimizer(),  # type: ignore[arg-type]
            EmptyAchievementOptimizer(),  # type: ignore[arg-type]
            FailingApplier(),  # type: ignore[arg-type]
            IdentityAchievementApplier(),  # type: ignore[arg-type]
            FailingStandaloneOptimizer(),  # type: ignore[arg-type]
        ).optimize(source, MatchingResult())

    assert (
        events
        == {
            "planner": ["planner"],
            "experience_optimizer": ["planner", "experience_optimizer"],
            "applier": ["planner", "experience_optimizer", "applier"],
            "standalone": ["planner", "experience_optimizer", "applier", "standalone"],
        }[failing_stage]
    )
    assert source == candidate()


@dataclass
class FakeStructuredAIClient:
    calls: list[type]
    source_path: str = ACTIVITY_PATH
    optimized_text: str = "Atendimento e acompanhamento de chamados técnicos."

    def generate(self, *, system_prompt, user_prompt, response_model):
        self.calls.append(response_model)
        if response_model is CandidateOptimizationAIResponse:
            return CandidateOptimizationAIResponse.model_validate(
                {
                    "experiences": [
                        {
                            "experience_index": 0,
                            "statements": [
                                {
                                    "text": self.optimized_text,
                                    "source_paths": [self.source_path],
                                    "target_match_indexes": [0],
                                }
                            ],
                        }
                    ]
                }
            )
        assert response_model is OptimizationStatementTruthDecision
        return OptimizationStatementTruthDecision(fully_supported=True)


def real_grounded_optimizer(client: FakeStructuredAIClient) -> GroundedCandidateOptimizer:
    return GroundedCandidateOptimizer(
        BuildCandidateOptimizationPlan(MatchingProvenanceGate()),
        AIContextualExperienceOptimizer(client, AISemanticOptimizationTruthGate(client)),
        EmptyAchievementOptimizer(),
        DeterministicCandidateOptimizationProposalApplier(),
        IdentityAchievementApplier(),
        GroundedStandaloneCandidateOptimizer(),
    )


def test_real_components_apply_grounded_experience_and_preserve_standalone_behavior() -> None:
    source = candidate()
    matching_result = matching(
        CriterionMatch(
            criterion(CriterionCategory.EXPERIENCE, "Support"),
            MatchStatus.MATCHED,
            (ACTIVITY_PATH,),
        ),
        CriterionMatch(
            criterion(CriterionCategory.SKILL, "Communication"), MatchStatus.MATCHED, (SKILL_PATH,)
        ),
    )
    fake = FakeStructuredAIClient([])

    result = real_grounded_optimizer(fake).optimize(source, matching_result)

    assert result.experiences[0].activities == (
        Activity("Atendimento e acompanhamento de chamados técnicos."),
    )
    assert tuple(item.name for item in result.skills) == ("Communication", "Python")
    assert fake.calls == [CandidateOptimizationAIResponse, OptimizationStatementTruthDecision]


def test_standalone_only_matching_skips_experience_ai_and_keeps_legacy_prioritization() -> None:
    source = candidate()
    matching_result = matching(
        CriterionMatch(
            criterion(CriterionCategory.SKILL, "Communication"), MatchStatus.MATCHED, (SKILL_PATH,)
        ),
    )
    fake = FakeStructuredAIClient([])

    result = real_grounded_optimizer(fake).optimize(source, matching_result)

    assert result.experiences is source.experiences
    assert tuple(item.name for item in result.skills) == ("Communication", "Python")
    assert fake.calls == []


def test_real_pipeline_prioritizes_semantic_technology_match_by_provenance() -> None:
    source = candidate()
    fake = FakeStructuredAIClient([])

    result = real_grounded_optimizer(fake).optimize(
        source,
        matching(
            CriterionMatch(
                criterion(CriterionCategory.EXPERIENCE, "Support"),
                MatchStatus.MATCHED,
                (ACTIVITY_PATH,),
            ),
            CriterionMatch(
                criterion(CriterionCategory.OTHER, "Postgres"),
                MatchStatus.MATCHED,
                ("technologies[1].name",),
            ),
        ),
    )

    assert tuple(item.name for item in result.technologies) == ("PostgreSQL", "Docker")
    assert result.technologies[0] is source.technologies[1]
    assert fake.calls == [CandidateOptimizationAIResponse, OptimizationStatementTruthDecision]


def test_real_pipeline_does_not_prioritize_skill_from_criterion_text_alone() -> None:
    source = candidate()
    fake = FakeStructuredAIClient([])

    result = real_grounded_optimizer(fake).optimize(
        source,
        matching(
            CriterionMatch(
                criterion(CriterionCategory.SKILL, "Python"),
                MatchStatus.MATCHED,
                (ACTIVITY_PATH,),
            ),
        ),
    )

    assert result.skills is source.skills
    assert fake.calls == [CandidateOptimizationAIResponse, OptimizationStatementTruthDecision]


def test_no_matches_skips_experience_ai_without_inventing_text() -> None:
    source = candidate()
    fake = FakeStructuredAIClient([])

    result = real_grounded_optimizer(fake).optimize(source, MatchingResult())

    assert result == source
    assert fake.calls == []


def test_unmatched_experience_activities_survive_the_real_grounded_pipeline() -> None:
    source = Candidate(
        PersonalInfo("Jane Doe", "Curitiba", "PR", "Brazil"),
        ContactInfo("jane@example.test", "+55 41 99999-0000"),
        experiences=(
            Experience(
                "Example",
                "Support Analyst",
                YearMonth("2020-01"),
                activities=(
                    Activity("Atendimento a usuários."),
                    Activity("Organização de chamados no Jira."),
                    Activity("Documentação de procedimentos."),
                ),
            ),
        ),
    )
    path = "experiences[0].activities[1].description"
    matching_result = matching(
        CriterionMatch(
            criterion(CriterionCategory.EXPERIENCE, "Jira"), MatchStatus.MATCHED, (path,)
        )
    )
    fake = FakeStructuredAIClient(
        [],
        source_path=path,
        optimized_text="Organização e acompanhamento de chamados utilizando Jira.",
    )

    result = real_grounded_optimizer(fake).optimize(source, matching_result)

    assert tuple(item.description for item in result.experiences[0].activities) == (
        "Atendimento a usuários.",
        "Organização e acompanhamento de chamados utilizando Jira.",
        "Documentação de procedimentos.",
    )


def test_achievement_only_match_stays_standalone_without_experience_ai() -> None:
    source = Candidate(
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
    )
    path = "experiences[0].achievements[0].description"
    fake = FakeStructuredAIClient([])

    result = real_grounded_optimizer(fake).optimize(
        source,
        matching(
            CriterionMatch(
                criterion(CriterionCategory.OTHER, "Speed"), MatchStatus.MATCHED, (path,)
            )
        ),
    )

    assert result.experiences is source.experiences
    assert fake.calls == []
