from typing import Protocol

from resume_ai.modules.candidate.domain.entities import Candidate
from resume_ai.modules.jobs.domain.entities import JobCriteria, JobCriterion
from resume_ai.modules.matching.domain.entities import CriterionMatch, MatchingResult


class CandidateJobMatcher(Protocol):
    def match(
        self,
        candidate: Candidate,
        criteria: JobCriteria,
    ) -> MatchingResult: ...


class CandidateCriterionMatcher(Protocol):
    def match(
        self,
        candidate: Candidate,
        criterion: JobCriterion,
    ) -> CriterionMatch: ...


class CandidateMatchingRefiner(Protocol):
    def refine(
        self,
        candidate: Candidate,
        result: MatchingResult,
    ) -> MatchingResult: ...
