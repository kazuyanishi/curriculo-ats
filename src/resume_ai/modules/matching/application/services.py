from resume_ai.modules.candidate.domain.entities import Candidate
from resume_ai.modules.jobs.domain.entities import JobCriteria
from resume_ai.modules.matching.application.ports import CandidateJobMatcher
from resume_ai.modules.matching.domain.entities import MatchingResult, MatchingScore
from resume_ai.modules.matching.domain.services import MatchingScoreCalculator


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
