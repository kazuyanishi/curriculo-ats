import logging

from resume_ai.modules.candidate.domain.entities import Candidate
from resume_ai.modules.jobs.domain.entities import JobCriteria
from resume_ai.modules.matching.application.exceptions import SemanticMatchingGroundingError
from resume_ai.modules.matching.application.ports import CandidateJobMatcher
from resume_ai.modules.matching.application.provenance import MatchingProvenanceGate
from resume_ai.modules.matching.domain.entities import (
    GapAnalysisResult,
    MatchingResult,
    MatchingScore,
)
from resume_ai.modules.matching.domain.services import (
    DeterministicGapAnalyzer,
    MatchingScoreCalculator,
)

logger = logging.getLogger(__name__)


class MatchCandidateToJob:
    def __init__(
        self,
        matcher: CandidateJobMatcher,
        provenance_gate: MatchingProvenanceGate | None = None,
        fallback_matcher: CandidateJobMatcher | None = None,
    ) -> None:
        self._matcher = matcher
        self._provenance_gate = provenance_gate
        self._fallback_matcher = fallback_matcher

    def execute(
        self,
        candidate: Candidate,
        criteria: JobCriteria,
    ) -> MatchingResult:
        try:
            result = self._matcher.match(candidate, criteria)
        except SemanticMatchingGroundingError:
            # Preserve the conservative deterministic result if the model emits
            # an invalid evidence path or incomplete decision set. The analysis
            # can still report gaps instead of failing the entire request.
            logger.warning(
                "Semantic matching output could not be grounded; using deterministic matches"
            )
            if self._fallback_matcher is None:
                raise
            result = self._fallback_matcher.match(candidate, criteria)
        if self._provenance_gate is not None:
            self._provenance_gate.validate(candidate, result)
        return result


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
