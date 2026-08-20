import re
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
from resume_ai.modules.optimization.application.planning import BuildCandidateOptimizationPlan
from resume_ai.modules.optimization.application.ports import (
    CandidateExperienceOptimizer,
    CandidateOptimizationProposalApplier,
    CandidateOptimizer,
)
from resume_ai.modules.optimization.application.proposals import (
    CandidateOptimizationProposal,
    OptimizedExperienceStatementProposal,
)
from resume_ai.modules.optimization.domain.services import DeterministicCandidateOptimizer

_ACTIVITY_PATH = re.compile(r"^experiences\[(\d+)]\.activities\[(\d+)]\.description$")


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
                activities=self._apply_activities(
                    experience.activities, by_experience_index[index]
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
    ) -> dict[int, tuple[tuple[int, frozenset[int], OptimizedExperienceStatementProposal], ...]]:
        by_experience_index: dict[
            int, tuple[tuple[int, frozenset[int], OptimizedExperienceStatementProposal], ...]
        ] = {}
        seen_indexes: set[int] = set()
        for experience_proposal in proposal.experiences:
            index = experience_proposal.experience_index
            if not 0 <= index < len(candidate.experiences) or index in seen_indexes:
                raise OptimizationProposalGroundingError()
            seen_indexes.add(index)
            if experience_proposal.statements:
                consumed: set[int] = set()
                replacements = []
                for statement in experience_proposal.statements:
                    activity_indexes = (
                        DeterministicCandidateOptimizationProposalApplier._activity_indexes(
                            candidate, index, statement
                        )
                    )
                    if consumed.intersection(activity_indexes):
                        raise OptimizationProposalGroundingError()
                    consumed.update(activity_indexes)
                    replacements.append((min(activity_indexes), activity_indexes, statement))
                by_experience_index[index] = tuple(replacements)
        return by_experience_index

    @staticmethod
    def _activity_indexes(
        candidate: Candidate,
        experience_index: int,
        statement: OptimizedExperienceStatementProposal,
    ) -> frozenset[int]:
        indexes = set()
        for path in statement.source_paths:
            match = _ACTIVITY_PATH.fullmatch(path)
            if match is None or int(match.group(1)) != experience_index:
                raise OptimizationProposalGroundingError()
            activity_index = int(match.group(2))
            if not 0 <= activity_index < len(candidate.experiences[experience_index].activities):
                raise OptimizationProposalGroundingError()
            indexes.add(activity_index)
        return frozenset(indexes)

    @staticmethod
    def _apply_activities(
        activities: tuple[Activity, ...],
        replacements: tuple[tuple[int, frozenset[int], OptimizedExperienceStatementProposal], ...],
    ) -> tuple[Activity, ...]:
        statements_by_first_index = {index: statement for index, _, statement in replacements}
        consumed_indexes = {
            activity_index
            for _, activity_indexes, _ in replacements
            for activity_index in activity_indexes
        }
        return tuple(
            Activity(statements_by_first_index[index].text)
            if index in statements_by_first_index
            else activity
            for index, activity in enumerate(activities)
            if index not in consumed_indexes or index in statements_by_first_index
        )


class GroundedCandidateOptimizer:
    def __init__(
        self,
        planner: BuildCandidateOptimizationPlan,
        experience_optimizer: CandidateExperienceOptimizer,
        proposal_applier: CandidateOptimizationProposalApplier,
        deterministic_optimizer: DeterministicCandidateOptimizer,
    ) -> None:
        self._planner = planner
        self._experience_optimizer = experience_optimizer
        self._proposal_applier = proposal_applier
        self._deterministic_optimizer = deterministic_optimizer

    def optimize(self, candidate: Candidate, matching: MatchingResult) -> Candidate:
        plan = self._planner.execute(candidate, matching)
        proposal = self._experience_optimizer.optimize(candidate, matching, plan)
        experience_optimized_candidate = self._proposal_applier.apply(candidate, proposal)
        return self._deterministic_optimizer.optimize(experience_optimized_candidate, matching)


class OptimizeCandidate:
    def __init__(self, optimizer: CandidateOptimizer) -> None:
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
