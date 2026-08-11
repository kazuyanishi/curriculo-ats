from resume_ai.modules.candidate.domain.entities import Candidate
from resume_ai.modules.jobs.domain.entities import JobCriteria
from resume_ai.modules.matching.application.ports import CandidateJobMatcher
from resume_ai.modules.matching.domain.entities import MatchingResult


class MatchCandidateToJob:
    def __init__(self, matcher: CandidateJobMatcher) -> None:
        self._matcher = matcher

    def execute(
        self,
        candidate: Candidate,
        criteria: JobCriteria,
    ) -> MatchingResult:
        return self._matcher.match(candidate, criteria)
