from typing import get_type_hints

import pytest

from resume_ai.modules.candidate.domain.entities import (
    Candidate,
    ContactInfo,
    PersonalInfo,
)
from resume_ai.modules.jobs.domain.entities import (
    CriterionCategory,
    CriterionImportance,
    JobCriteria,
    JobCriterion,
)
from resume_ai.modules.matching.application.services import (
    CalculateMatchingScore,
    MatchAndScoreCandidateToJob,
    MatchCandidateToJob,
)
from resume_ai.modules.matching.domain.entities import MatchingResult, MatchingScore


def _candidate() -> Candidate:
    return Candidate(
        personal_info=PersonalInfo("Jane Doe", "Curitiba", "PR", "Brazil"),
        contact_info=ContactInfo("jane@example.com", "+55"),
    )


def _criteria() -> JobCriteria:
    return JobCriteria(
        criteria=(
            JobCriterion(
                category=CriterionCategory.TECHNOLOGY,
                value="Python",
                evidence="Python is required.",
                importance=CriterionImportance.REQUIRED,
            ),
        )
    )


class FakeMatcher:
    def __init__(self, result: MatchingResult) -> None:
        self.result = result
        self.calls = 0
        self.received_candidate: Candidate | None = None
        self.received_criteria: JobCriteria | None = None
        self.events: list[str] = []

    def execute(self, candidate: Candidate, criteria: JobCriteria) -> MatchingResult:
        self.calls += 1
        self.received_candidate = candidate
        self.received_criteria = criteria
        self.events.append("matching")
        return self.result


class FakeScoreCalculator:
    def __init__(self, score: MatchingScore) -> None:
        self.score = score
        self.calls = 0
        self.received_result: MatchingResult | None = None
        self.events: list[str] = []

    def execute(self, result: MatchingResult) -> MatchingScore:
        self.calls += 1
        self.received_result = result
        self.events.append("score")
        return self.score


class FailingMatcher:
    def execute(self, candidate: Candidate, criteria: JobCriteria) -> MatchingResult:
        raise RuntimeError("matching failure")


class FailingScoreCalculator:
    def execute(self, result: MatchingResult) -> MatchingScore:
        raise RuntimeError("score failure")


def test_pipeline_delegates_inputs_and_preserves_result_identities() -> None:
    candidate = _candidate()
    criteria = _criteria()
    matching_result = MatchingResult()
    matching_score = MatchingScore(score=None, coverage=None)
    matcher = FakeMatcher(matching_result)
    score_calculator = FakeScoreCalculator(matching_score)

    result = MatchAndScoreCandidateToJob(  # type: ignore[arg-type]
        matcher, score_calculator  # type: ignore[arg-type]
    ).execute(candidate, criteria)

    assert matcher.calls == 1
    assert matcher.received_candidate is candidate
    assert matcher.received_criteria is criteria
    assert score_calculator.calls == 1
    assert score_calculator.received_result is matching_result
    assert result[0] is matching_result
    assert result[1] is matching_score


def test_pipeline_executes_matching_before_score() -> None:
    matcher = FakeMatcher(MatchingResult())
    score_calculator = FakeScoreCalculator(MatchingScore(score=None, coverage=None))
    matcher.events = score_calculator.events = []

    MatchAndScoreCandidateToJob(  # type: ignore[arg-type]
        matcher, score_calculator  # type: ignore[arg-type]
    ).execute(_candidate(), _criteria())

    assert matcher.events == ["matching", "score"]


def test_matching_error_prevents_score_and_propagates() -> None:
    score_calculator = FakeScoreCalculator(MatchingScore(score=None, coverage=None))

    with pytest.raises(RuntimeError, match="matching failure"):
        MatchAndScoreCandidateToJob(  # type: ignore[arg-type]
            FailingMatcher(), score_calculator  # type: ignore[arg-type]
        ).execute(_candidate(), _criteria())

    assert score_calculator.calls == 0


def test_score_error_propagates() -> None:
    with pytest.raises(RuntimeError, match="score failure"):
        MatchAndScoreCandidateToJob(  # type: ignore[arg-type]
            FakeMatcher(MatchingResult()), FailingScoreCalculator()  # type: ignore[arg-type]
        ).execute(_candidate(), _criteria())


def test_pipeline_type_hints() -> None:
    constructor_hints = get_type_hints(MatchAndScoreCandidateToJob.__init__)
    execute_hints = get_type_hints(MatchAndScoreCandidateToJob.execute)

    assert constructor_hints["matcher"] is MatchCandidateToJob
    assert constructor_hints["score_calculator"] is CalculateMatchingScore
    assert execute_hints["candidate"] is Candidate
    assert execute_hints["criteria"] is JobCriteria
    assert execute_hints["return"] == tuple[MatchingResult, MatchingScore]
