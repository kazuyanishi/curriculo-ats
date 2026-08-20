from dataclasses import dataclass, replace

from resume_ai.modules.candidate.domain.entities import Activity, Candidate
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
from resume_ai.modules.optimization.application.exceptions import OptimizationProposalGroundingError
from resume_ai.modules.optimization.application.proposals import (
    CandidateOptimizationProposal,
    OptimizedExperienceStatementProposal,
)
from resume_ai.modules.optimization.domain.services import DeterministicCandidateOptimizer


class DeterministicCandidateOptimizationProposalApplier:
    def apply(
        self,
        candidate: Candidate,
        proposal: CandidateOptimizationProposal,
    ) -> Candidate:
        by_experience_index = self._by_experience_index(candidate, proposal)
        if not by_experience_index:
            return candidate

        experiences = tuple(
            replace(
                experience,
                activities=tuple(
                    Activity(statement.text) for statement in by_experience_index[index]
                ),
            )
            if index in by_experience_index
            else experience
            for index, experience in enumerate(candidate.experiences)
        )
        return replace(candidate, experiences=experiences)

    @staticmethod
    def _by_experience_index(
        candidate: Candidate,
        proposal: CandidateOptimizationProposal,
    ) -> dict[int, tuple[OptimizedExperienceStatementProposal, ...]]:
        by_experience_index: dict[int, tuple[OptimizedExperienceStatementProposal, ...]] = {}
        seen_indexes: set[int] = set()
        for experience_proposal in proposal.experiences:
            index = experience_proposal.experience_index
            if not 0 <= index < len(candidate.experiences) or index in seen_indexes:
                raise OptimizationProposalGroundingError()
            seen_indexes.add(index)
            if experience_proposal.statements:
                by_experience_index[index] = experience_proposal.statements
        return by_experience_index


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
