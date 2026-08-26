import json
import re

from resume_ai.integrations.ai.client import StructuredAIClient
from resume_ai.modules.candidate.domain.entities import Candidate
from resume_ai.modules.matching.application.catalog import build_candidate_evidence_catalog
from resume_ai.modules.matching.application.provenance import MatchingProvenanceGate
from resume_ai.modules.matching.domain.entities import MatchingResult, MatchStatus
from resume_ai.modules.optimization.application.exceptions import OptimizationProposalGroundingError
from resume_ai.modules.optimization.application.planning import (
    AchievementOptimizationContext,
    CandidateOptimizationPlan,
)
from resume_ai.modules.optimization.application.ports import (
    CandidateAchievementOptimizationTruthGate,
)
from resume_ai.modules.optimization.application.proposals import (
    CandidateAchievementOptimizationProposal,
    ExperienceAchievementOptimizationProposal,
    OptimizedAchievementStatementProposal,
)
from resume_ai.modules.optimization.infrastructure.contextual_achievement_prompt import (
    CONTEXTUAL_ACHIEVEMENT_OPTIMIZATION_SYSTEM_PROMPT,
)
from resume_ai.modules.optimization.infrastructure.contextual_achievement_schemas import (
    CandidateAchievementOptimizationAIResponse,
)

_ACHIEVEMENT_PATH = re.compile(r"^experiences\[(\d+)]\.achievements\[(\d+)]\.description$")


class AIContextualAchievementOptimizer:
    def __init__(
        self,
        client: StructuredAIClient,
        truth_gate: CandidateAchievementOptimizationTruthGate,
    ) -> None:
        self._client = client
        self._truth_gate = truth_gate

    def optimize(
        self,
        candidate: Candidate,
        matching: MatchingResult,
        plan: CandidateOptimizationPlan,
    ) -> CandidateAchievementOptimizationProposal:
        if not plan.achievement_contexts:
            proposal = CandidateAchievementOptimizationProposal()
            self._truth_gate.validate(candidate, proposal)
            return proposal

        MatchingProvenanceGate().validate(candidate, matching)
        catalog = {item.path: item.text for item in build_candidate_evidence_catalog(candidate)}
        response = self._client.generate(
            system_prompt=CONTEXTUAL_ACHIEVEMENT_OPTIMIZATION_SYSTEM_PROMPT,
            user_prompt=json.dumps(self._payload(matching, plan, catalog), ensure_ascii=False),
            response_model=CandidateAchievementOptimizationAIResponse,
        )
        proposal = self._proposal(plan, matching, response)
        self._truth_gate.validate(candidate, proposal)
        return proposal

    @staticmethod
    def _payload(
        matching: MatchingResult, plan: CandidateOptimizationPlan, catalog: dict[str, str]
    ) -> dict[str, object]:
        contexts = []
        for context in plan.achievement_contexts:
            if any(
                (match := _ACHIEVEMENT_PATH.fullmatch(path)) is None
                or int(match.group(1)) != context.experience_index
                for path in context.evidence_paths
            ):
                raise OptimizationProposalGroundingError()
            criteria = []
            for match_index in context.match_indexes:
                if not 0 <= match_index < len(matching.matches):
                    raise OptimizationProposalGroundingError()
                match = matching.matches[match_index]
                if match.status is not MatchStatus.MATCHED:
                    raise OptimizationProposalGroundingError()
                criterion = match.criterion
                criteria.append(
                    {
                        "match_index": match_index,
                        "category": criterion.category.value,
                        "value": criterion.value,
                        "evidence": criterion.evidence,
                        "importance": criterion.importance.value,
                        "candidate_evidence_paths": list(match.candidate_evidence_paths),
                    }
                )
            try:
                evidence = [
                    {"path": path, "text": catalog[path]} for path in context.evidence_paths
                ]
            except KeyError as error:
                raise OptimizationProposalGroundingError() from error
            contexts.append(
                {
                    "experience_index": context.experience_index,
                    "criteria": criteria,
                    "candidate_evidence": evidence,
                }
            )
        return {"achievement_contexts": contexts}

    @staticmethod
    def _proposal(
        plan: CandidateOptimizationPlan,
        matching: MatchingResult,
        response: CandidateAchievementOptimizationAIResponse,
    ) -> CandidateAchievementOptimizationProposal:
        expected = [context.experience_index for context in plan.achievement_contexts]
        returned = [item.experience_index for item in response.experiences]
        if set(returned) != set(expected) or len(returned) != len(set(returned)):
            raise OptimizationProposalGroundingError()
        by_index = {item.experience_index: item for item in response.experiences}
        proposals = []
        for context in plan.achievement_contexts:
            statements = []
            for statement in by_index[context.experience_index].statements:
                if not set(statement.source_paths).issubset(context.evidence_paths):
                    raise OptimizationProposalGroundingError()
                if not set(statement.target_match_indexes).issubset(context.match_indexes):
                    raise OptimizationProposalGroundingError()
                AIContextualAchievementOptimizer._validate_source_target_binding(
                    matching, context, statement.source_paths, statement.target_match_indexes
                )
                statements.append(
                    OptimizedAchievementStatementProposal(
                        statement.text, statement.source_paths, statement.target_match_indexes
                    )
                )
            proposals.append(
                ExperienceAchievementOptimizationProposal(
                    context.experience_index, tuple(statements)
                )
            )
        return CandidateAchievementOptimizationProposal(tuple(proposals))

    @staticmethod
    def _validate_source_target_binding(
        matching: MatchingResult,
        context: AchievementOptimizationContext,
        source_paths: tuple[str, ...],
        target_match_indexes: tuple[int, ...],
    ) -> None:
        target_paths: set[str] = set()
        for target_match_index in target_match_indexes:
            if not 0 <= target_match_index < len(matching.matches):
                raise OptimizationProposalGroundingError()
            if target_match_index not in context.match_indexes:
                raise OptimizationProposalGroundingError()
            match = matching.matches[target_match_index]
            if match.status is not MatchStatus.MATCHED or not match.candidate_evidence_paths:
                raise OptimizationProposalGroundingError()
            paths = set(match.candidate_evidence_paths)
            if not set(source_paths).intersection(paths):
                raise OptimizationProposalGroundingError()
            target_paths.update(paths)
        if not set(source_paths).issubset(target_paths):
            raise OptimizationProposalGroundingError()
