from resume_ai.modules.candidate.domain.entities import Candidate
from resume_ai.modules.jobs.domain.entities import JobCriteria
from resume_ai.modules.matching.application.ports import (
    CandidateCriterionMatcher,
    CandidateJobMatcher,
    CandidateMatchingRefiner,
)
from resume_ai.modules.matching.domain.entities import MatchingResult


class DeterministicCandidateJobMatcher:
    def __init__(self, criterion_matcher: CandidateCriterionMatcher) -> None:
        self._criterion_matcher = criterion_matcher

    def match(
        self,
        candidate: Candidate,
        criteria: JobCriteria,
    ) -> MatchingResult:
        matches = tuple(
            self._criterion_matcher.match(candidate, criterion) for criterion in criteria.criteria
        )
        return MatchingResult(matches=matches)


class HybridCandidateJobMatcher:
    def __init__(
        self,
        deterministic_matcher: CandidateJobMatcher,
        semantic_refiner: CandidateMatchingRefiner,
    ) -> None:
        self._deterministic_matcher = deterministic_matcher
        self._semantic_refiner = semantic_refiner

    def match(self, candidate: Candidate, criteria: JobCriteria) -> MatchingResult:
        result = self._deterministic_matcher.match(candidate, criteria)
        if all(match.status.value == "matched" for match in result.matches):
            return result
        return self._semantic_refiner.refine(candidate, result)
