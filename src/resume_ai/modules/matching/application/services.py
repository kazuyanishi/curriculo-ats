from resume_ai.modules.candidate.domain.entities import Candidate
from resume_ai.modules.jobs.domain.entities import JobCriteria
from resume_ai.modules.matching.application.ports import CandidateJobMatcher
from resume_ai.modules.matching.domain.entities import (
    GapAnalysisResult,
    MatchingResult,
    MatchingScore,
)
from resume_ai.modules.matching.domain.services import (
    DeterministicGapAnalyzer,
    MatchingScoreCalculator,
)


class MatchCandidateToJob:
    def __init__(self, matcher: CandidateJobMatcher) -> None:
        self._matcher = matcher

    def execute(
        self,
        candidate: Candidate,
        criteria: JobCriteria,
    ) -> MatchingResult:
        return self._matcher.match(candidate, criteria)


class CalculateMatchingScore:
    def __init__(self, calculator: MatchingScoreCalculator) -> None:
        self._calculator = calculator

    def execute(self, result: MatchingResult) -> MatchingScore:
        return self._calculator.calculate(result)


class AnalyzeMatchingGaps:
    def __init__(self, analyzer: DeterministicGapAnalyzer) -> None:
        self._analyzer = analyzer

    def execute(self, result: MatchingResult) -> GapAnalysisResult:
        return self._analyzer.analyze(result)


class MatchAndScoreCandidateToJob:
    def __init__(
        self,
        matcher: MatchCandidateToJob,
        score_calculator: CalculateMatchingScore,
    ) -> None:
        self._matcher = matcher
        self._score_calculator = score_calculator

    def execute(
        self,
        candidate: Candidate,
        criteria: JobCriteria,
    ) -> tuple[MatchingResult, MatchingScore]:
        matching_result = self._matcher.execute(candidate, criteria)
        matching_score = self._score_calculator.execute(matching_result)
        return matching_result, matching_score
