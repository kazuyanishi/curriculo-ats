from dataclasses import dataclass

from resume_ai.modules.candidate.domain.entities import Candidate
from resume_ai.modules.jobs.application.services import ExtractJobCriteria
from resume_ai.modules.jobs.domain.entities import JobCriteria, JobPosting
from resume_ai.modules.matching.application.services import (
    AnalyzeMatchingGaps,
    MatchAndScoreCandidateToJob,
)
from resume_ai.modules.matching.domain.entities import (
    GapAnalysisResult,
    MatchingResult,
    MatchingScore,
)
from resume_ai.modules.optimization.domain.services import DeterministicCandidateOptimizer


class OptimizeCandidate:
    def __init__(self, optimizer: DeterministicCandidateOptimizer) -> None:
        self._optimizer = optimizer

    def execute(self, candidate: Candidate, result: MatchingResult) -> Candidate:
        return self._optimizer.optimize(candidate, result)


@dataclass(frozen=True, slots=True)
class CandidateAnalysisResult:
    criteria: JobCriteria
    matching: MatchingResult
    score: MatchingScore
    gaps: GapAnalysisResult
    optimized_candidate: Candidate


class AnalyzeCandidateForJob:
    def __init__(
        self,
        criteria_extractor: ExtractJobCriteria,
        matcher: MatchAndScoreCandidateToJob,
        gap_analyzer: AnalyzeMatchingGaps,
        optimizer: OptimizeCandidate,
    ) -> None:
        self._criteria_extractor = criteria_extractor
        self._matcher = matcher
        self._gap_analyzer = gap_analyzer
        self._optimizer = optimizer

    def execute(
        self,
        candidate: Candidate,
        job: JobPosting,
    ) -> CandidateAnalysisResult:
        criteria = self._criteria_extractor.execute(job)
        matching, score = self._matcher.execute(candidate, criteria)
        gaps = self._gap_analyzer.execute(matching)
        optimized_candidate = self._optimizer.execute(candidate, matching)
        return CandidateAnalysisResult(
            criteria=criteria,
            matching=matching,
            score=score,
            gaps=gaps,
            optimized_candidate=optimized_candidate,
        )
