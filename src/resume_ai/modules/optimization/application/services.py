import re
from dataclasses import dataclass, replace

from resume_ai.modules.candidate.domain.entities import Achievement, Activity, Candidate
from resume_ai.modules.jobs.application.services import ExtractJobCriteria
from resume_ai.modules.jobs.domain.entities import JobCriteria, JobPosting
from resume_ai.modules.matching.application.catalog import build_candidate_evidence_catalog
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
from resume_ai.modules.optimization.application.planning import (
    BuildCandidateOptimizationPlan,
    CandidateOptimizationPlan,
)
from resume_ai.modules.optimization.application.ports import (
    CandidateAchievementOptimizationProposalApplier,
    CandidateAchievementOptimizer,
    CandidateExperienceOptimizer,
    CandidateOptimizationProposalApplier,
    CandidateOptimizer,
    CandidateProjectOptimizationProposalApplier,
    CandidateProjectOptimizer,
    CandidateStandaloneOptimizer,
)
from resume_ai.modules.optimization.application.proposals import (
    CandidateAchievementOptimizationProposal,
    CandidateOptimizationProposal,
    CandidateProjectOptimizationProposal,
    OptimizedAchievementStatementProposal,
    OptimizedExperienceStatementProposal,
)

_ACTIVITY_PATH = re.compile(r"^experiences\[(\d+)]\.activities\[(\d+)]\.description$")
_ACHIEVEMENT_PATH = re.compile(r"^experiences\[(\d+)]\.achievements\[(\d+)]\.description$")
_PROJECT_PATH = re.compile(r"^projects\[(\d+)]\.description$")
_STANDALONE_PATH = re.compile(
    r"^(skills|technologies|tools|languages|certifications)\[(\d+)]\.[^.]+$"
)


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


class DeterministicCandidateAchievementOptimizationProposalApplier:
    def apply(
        self,
        candidate: Candidate,
        proposal: CandidateAchievementOptimizationProposal,
    ) -> Candidate:
        by_experience_index = self._by_experience_index(candidate, proposal)
        if not by_experience_index:
            return candidate

        experiences = tuple(
            replace(
                experience,
                achievements=self._apply_achievements(
                    experience.achievements, by_experience_index[index]
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
        proposal: CandidateAchievementOptimizationProposal,
    ) -> dict[int, tuple[tuple[int, frozenset[int], OptimizedAchievementStatementProposal], ...]]:
        by_experience_index = {}
        seen_indexes: set[int] = set()
        get_achievement_indexes = (
            DeterministicCandidateAchievementOptimizationProposalApplier._achievement_indexes
        )
        for experience_proposal in proposal.experiences:
            index = experience_proposal.experience_index
            if not 0 <= index < len(candidate.experiences) or index in seen_indexes:
                raise OptimizationProposalGroundingError()
            seen_indexes.add(index)
            if experience_proposal.statements:
                consumed: set[int] = set()
                replacements = []
                for statement in experience_proposal.statements:
                    achievement_indexes = get_achievement_indexes(candidate, index, statement)
                    if consumed.intersection(achievement_indexes):
                        raise OptimizationProposalGroundingError()
                    consumed.update(achievement_indexes)
                    replacements.append((min(achievement_indexes), achievement_indexes, statement))
                by_experience_index[index] = tuple(replacements)
        return by_experience_index

    @staticmethod
    def _achievement_indexes(
        candidate: Candidate,
        experience_index: int,
        statement: OptimizedAchievementStatementProposal,
    ) -> frozenset[int]:
        indexes = set()
        for path in statement.source_paths:
            match = _ACHIEVEMENT_PATH.fullmatch(path)
            if match is None or int(match.group(1)) != experience_index:
                raise OptimizationProposalGroundingError()
            achievement_index = int(match.group(2))
            if (
                not 0
                <= achievement_index
                < len(candidate.experiences[experience_index].achievements)
            ):
                raise OptimizationProposalGroundingError()
            indexes.add(achievement_index)
        return frozenset(indexes)

    @staticmethod
    def _apply_achievements(
        achievements: tuple[Achievement, ...],
        replacements: tuple[tuple[int, frozenset[int], OptimizedAchievementStatementProposal], ...],
    ) -> tuple[Achievement, ...]:
        statements_by_first_index = {index: statement for index, _, statement in replacements}
        consumed_indexes = {
            achievement_index
            for _, achievement_indexes, _ in replacements
            for achievement_index in achievement_indexes
        }
        return tuple(
            Achievement(statements_by_first_index[index].text)
            if index in statements_by_first_index
            else achievement
            for index, achievement in enumerate(achievements)
            if index not in consumed_indexes or index in statements_by_first_index
        )


class DeterministicCandidateProjectOptimizationProposalApplier:
    def apply(
        self, candidate: Candidate, proposal: CandidateProjectOptimizationProposal
    ) -> Candidate:
        replacements: dict[int, str] = {}
        for project_proposal in proposal.projects:
            index = project_proposal.project_index
            if not 0 <= index < len(candidate.projects) or index in replacements:
                raise OptimizationProposalGroundingError()
            if project_proposal.description is None:
                continue
            for path in project_proposal.description.source_paths:
                match = _PROJECT_PATH.fullmatch(path)
                if match is None or int(match.group(1)) != index:
                    raise OptimizationProposalGroundingError()
            replacements[index] = project_proposal.description.text
        if not replacements:
            return candidate
        projects = tuple(
            replace(project, description=replacements[index]) if index in replacements else project
            for index, project in enumerate(candidate.projects)
        )
        return replace(candidate, projects=projects)


class GroundedStandaloneCandidateOptimizer:
    def optimize(self, candidate: Candidate, plan: CandidateOptimizationPlan) -> Candidate:
        catalog_paths = {item.path for item in build_candidate_evidence_catalog(candidate)}
        indexes_by_collection = {
            collection: set()
            for collection in ("skills", "technologies", "tools", "languages", "certifications")
        }
        for context in plan.standalone_contexts:
            for path in context.evidence_paths:
                if path not in catalog_paths:
                    raise OptimizationProposalGroundingError()
                match = _STANDALONE_PATH.fullmatch(path)
                if match is not None:
                    indexes_by_collection[match.group(1)].add(int(match.group(2)))

        reordered = {}
        for collection, indexes in indexes_by_collection.items():
            items = getattr(candidate, collection)
            prioritized = self._prioritize(items, indexes)
            if prioritized is not items:
                reordered[collection] = prioritized
        return replace(candidate, **reordered) if reordered else candidate

    @staticmethod
    def _prioritize(items: tuple[object, ...], indexes: set[int]) -> tuple[object, ...]:
        ordered_indexes = [
            *[index for index in range(len(items)) if index in indexes],
            *[index for index in range(len(items)) if index not in indexes],
        ]
        if ordered_indexes == list(range(len(items))):
            return items
        return tuple(items[index] for index in ordered_indexes)


class GroundedCandidateOptimizer:
    def __init__(
        self,
        planner: BuildCandidateOptimizationPlan,
        experience_optimizer: CandidateExperienceOptimizer,
        achievement_optimizer: CandidateAchievementOptimizer,
        proposal_applier: CandidateOptimizationProposalApplier,
        achievement_proposal_applier: CandidateAchievementOptimizationProposalApplier,
        standalone_optimizer: CandidateStandaloneOptimizer,
        project_optimizer: CandidateProjectOptimizer,
        project_proposal_applier: CandidateProjectOptimizationProposalApplier,
    ) -> None:
        self._planner = planner
        self._experience_optimizer = experience_optimizer
        self._achievement_optimizer = achievement_optimizer
        self._project_optimizer = project_optimizer
        self._proposal_applier = proposal_applier
        self._achievement_proposal_applier = achievement_proposal_applier
        self._project_proposal_applier = project_proposal_applier
        self._standalone_optimizer = standalone_optimizer

    def optimize(self, candidate: Candidate, matching: MatchingResult) -> Candidate:
        plan = self._planner.execute(candidate, matching)
        activity_proposal = self._experience_optimizer.optimize(candidate, matching, plan)
        achievement_proposal = self._achievement_optimizer.optimize(candidate, matching, plan)
        project_proposal = self._project_optimizer.optimize(candidate, matching, plan)
        after_activities = self._proposal_applier.apply(candidate, activity_proposal)
        after_achievements = self._achievement_proposal_applier.apply(
            after_activities, achievement_proposal
        )
        after_projects = self._project_proposal_applier.apply(after_achievements, project_proposal)
        return self._standalone_optimizer.optimize(after_projects, plan)


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
