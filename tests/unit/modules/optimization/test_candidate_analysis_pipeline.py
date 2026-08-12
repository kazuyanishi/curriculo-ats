from typing import get_type_hints

import pytest

from resume_ai.bootstrap import build_analyze_candidate_for_job
from resume_ai.core.exceptions import DomainError
from resume_ai.integrations.ai.config import AIConfig
from resume_ai.modules.candidate.domain.entities import Candidate, ContactInfo, PersonalInfo
from resume_ai.modules.jobs.application.schemas import JobCriteriaInput
from resume_ai.modules.jobs.domain.entities import JobCriteria, JobPosting
from resume_ai.modules.matching.domain.entities import (
    GapAnalysisResult,
    MatchingResult,
    MatchingScore,
)
from resume_ai.modules.optimization.application.services import (
    AnalyzeCandidateForJob,
    CandidateAnalysisResult,
)


def _candidate() -> Candidate:
    return Candidate(
        personal_info=PersonalInfo("Jane Doe", "Curitiba", "PR", "Brazil"),
        contact_info=ContactInfo("jane@example.com", "+55"),
    )


class RecordingExtractor:
    def __init__(self, criteria: JobCriteria, events: list[str]) -> None:
        self.criteria = criteria
        self.events = events

    def execute(self, job: JobPosting) -> JobCriteria:
        self.events.append("extract")
        return self.criteria


class RecordingMatcher:
    def __init__(self, matching: MatchingResult, score: MatchingScore, events: list[str]) -> None:
        self.matching = matching
        self.score = score
        self.events = events
        self.received = None

    def execute(
        self,
        candidate: Candidate,
        criteria: JobCriteria,
    ) -> tuple[MatchingResult, MatchingScore]:
        self.events.append("match")
        self.received = (candidate, criteria)
        return self.matching, self.score


class RecordingGaps:
    def __init__(self, gaps: GapAnalysisResult, events: list[str]) -> None:
        self.gaps = gaps
        self.events = events
        self.received = None

    def execute(self, matching: MatchingResult) -> GapAnalysisResult:
        self.events.append("gaps")
        self.received = matching
        return self.gaps


class RecordingOptimizer:
    def __init__(self, optimized: Candidate, events: list[str]) -> None:
        self.optimized = optimized
        self.events = events
        self.received = None

    def execute(self, candidate: Candidate, matching: MatchingResult) -> Candidate:
        self.events.append("optimize")
        self.received = (candidate, matching)
        return self.optimized


def test_pipeline_orchestrates_in_order_and_preserves_identity() -> None:
    events: list[str] = []
    candidate = _candidate()
    job = JobPosting("Python is required.")
    criteria = JobCriteria()
    matching = MatchingResult()
    score = MatchingScore(None, None)
    gaps = GapAnalysisResult()
    optimized = _candidate()
    extractor = RecordingExtractor(criteria, events)
    matcher = RecordingMatcher(matching, score, events)
    gap_analyzer = RecordingGaps(gaps, events)
    optimizer = RecordingOptimizer(optimized, events)

    service = AnalyzeCandidateForJob(
        extractor,  # type: ignore[arg-type]
        matcher,  # type: ignore[arg-type]
        gap_analyzer,  # type: ignore[arg-type]
        optimizer,  # type: ignore[arg-type]
    )
    result = service.execute(candidate, job)

    assert events == ["extract", "match", "gaps", "optimize"]
    assert matcher.received == (candidate, criteria)
    assert gap_analyzer.received is matching
    assert optimizer.received == (candidate, matching)
    assert result.criteria is criteria
    assert result.matching is matching
    assert result.score is score
    assert result.gaps is gaps
    assert result.optimized_candidate is optimized


def test_pipeline_stops_after_extraction_failure() -> None:
    class FailingExtractor:
        def execute(self, job: JobPosting) -> JobCriteria:
            raise RuntimeError("extract failure")

    class FailingStage:
        def execute(self, *args: object) -> object:
            raise AssertionError("stage should not execute")

    with pytest.raises(RuntimeError, match="extract failure"):
        AnalyzeCandidateForJob(
            FailingExtractor(),  # type: ignore[arg-type]
            FailingStage(),  # type: ignore[arg-type]
            FailingStage(),  # type: ignore[arg-type]
            FailingStage(),  # type: ignore[arg-type]
        ).execute(_candidate(), JobPosting("description"))


def test_pipeline_stops_after_matching_failure() -> None:
    events: list[str] = []
    class FailingMatcher:
        def execute(
            self,
            candidate: Candidate,
            criteria: JobCriteria,
        ) -> tuple[MatchingResult, MatchingScore]:
            events.append("match")
            raise RuntimeError("match failure")

    class FailingLaterStage:
        def execute(self, *args: object) -> object:
            raise AssertionError("later stage should not execute")

    with pytest.raises(RuntimeError, match="match failure"):
        AnalyzeCandidateForJob(
            RecordingExtractor(JobCriteria(), events),
            FailingMatcher(),  # type: ignore[arg-type]
            FailingLaterStage(),  # type: ignore[arg-type]
            FailingLaterStage(),  # type: ignore[arg-type]
        ).execute(_candidate(), JobPosting("description"))


class FakeOpenAIClient:
    response: JobCriteriaInput | None = None

    def __init__(self, config: AIConfig) -> None:
        self.config = config

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[JobCriteriaInput],
    ) -> JobCriteriaInput:
        assert self.response is not None
        return self.response


def test_bootstrap_composes_real_pipeline_with_fake_ai(monkeypatch) -> None:
    FakeOpenAIClient.response = JobCriteriaInput(
        criteria=[
            {
                "category": "technology",
                "value": "Python",
                "evidence": "Python is required.",
                "importance": "required",
            }
        ]
    )
    monkeypatch.setattr("resume_ai.bootstrap.OpenAIStructuredAIClient", FakeOpenAIClient)

    result = build_analyze_candidate_for_job(AIConfig("key", "model")).execute(
        _candidate(), JobPosting("Python is required.")
    )

    assert result.criteria.criteria[0].value == "Python"
    assert result.matching.total == 1
    assert result.score.score == 0.0
    assert result.gaps.gaps[0].criterion.value == "Python"
    assert result.optimized_candidate is not None


def test_bootstrap_truth_gate_blocks_hallucinated_evidence(monkeypatch) -> None:
    FakeOpenAIClient.response = JobCriteriaInput(
        criteria=[
            {
                "category": "technology",
                "value": "Python",
                "evidence": "Invented evidence.",
                "importance": "required",
            }
        ]
    )
    monkeypatch.setattr("resume_ai.bootstrap.OpenAIStructuredAIClient", FakeOpenAIClient)

    with pytest.raises(DomainError):
        build_analyze_candidate_for_job(AIConfig("key", "model")).execute(
            _candidate(), JobPosting("Python is required.")
        )


def test_pipeline_type_hints() -> None:
    hints = get_type_hints(AnalyzeCandidateForJob.execute)
    assert hints["candidate"] is Candidate
    assert hints["job"] is JobPosting
    assert hints["return"] is CandidateAnalysisResult
    builder_hints = get_type_hints(build_analyze_candidate_for_job)
    assert builder_hints["config"] is AIConfig
    assert builder_hints["return"] is AnalyzeCandidateForJob
