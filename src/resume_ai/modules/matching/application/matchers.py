from resume_ai.modules.candidate.domain.entities import Candidate
from resume_ai.modules.jobs.domain.entities import JobCriteria
from resume_ai.modules.matching.application.ports import CandidateCriterionMatcher
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
            self._criterion_matcher.match(candidate, criterion)
            for criterion in criteria.criteria
        )
        return MatchingResult(matches=matches)
