import json

from resume_ai.integrations.ai.client import StructuredAIClient
from resume_ai.modules.candidate.domain.entities import Candidate
from resume_ai.modules.matching.application.catalog import build_candidate_evidence_catalog
from resume_ai.modules.matching.application.provenance import MatchingProvenanceGate
from resume_ai.modules.matching.domain.entities import MatchingResult, MatchStatus
from resume_ai.modules.optimization.application.exceptions import OptimizationProposalGroundingError
from resume_ai.modules.optimization.application.planning import CandidateOptimizationPlan
from resume_ai.modules.optimization.application.proposals import (
    CandidateOptimizationProposal,
    ExperienceOptimizationProposal,
    OptimizedExperienceStatementProposal,
)
from resume_ai.modules.optimization.infrastructure.contextual_experience_prompt import (
    CONTEXTUAL_EXPERIENCE_OPTIMIZATION_SYSTEM_PROMPT,
)
from resume_ai.modules.optimization.infrastructure.contextual_experience_schemas import (
    CandidateOptimizationAIResponse,
)


class AIContextualExperienceOptimizer:
    def __init__(self, client: StructuredAIClient) -> None:
        self._client = client

    def optimize(
        self,
        candidate: Candidate,
        matching: MatchingResult,
        plan: CandidateOptimizationPlan,
    ) -> CandidateOptimizationProposal:
        if not plan.experience_contexts:
            return CandidateOptimizationProposal()

        MatchingProvenanceGate().validate(candidate, matching)
        catalog = {item.path: item.text for item in build_candidate_evidence_catalog(candidate)}
        payload = self._payload(matching, plan, catalog)
        response = self._client.generate(
            system_prompt=CONTEXTUAL_EXPERIENCE_OPTIMIZATION_SYSTEM_PROMPT,
            user_prompt=json.dumps(payload, ensure_ascii=False),
            response_model=CandidateOptimizationAIResponse,
        )
        return self._proposal(plan, response)

    @staticmethod
    def _payload(
        matching: MatchingResult,
        plan: CandidateOptimizationPlan,
        catalog: dict[str, str],
    ) -> dict[str, object]:
        contexts = []
        for context in plan.experience_contexts:
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
        return {"experience_contexts": contexts}

    @staticmethod
    def _proposal(
        plan: CandidateOptimizationPlan,
        response: CandidateOptimizationAIResponse,
    ) -> CandidateOptimizationProposal:
        expected = [context.experience_index for context in plan.experience_contexts]
        returned = [item.experience_index for item in response.experiences]
        if set(returned) != set(expected) or len(returned) != len(set(returned)):
            raise OptimizationProposalGroundingError()
        by_index = {item.experience_index: item for item in response.experiences}
        proposals = []
        for context in plan.experience_contexts:
            statements = []
            for statement in by_index[context.experience_index].statements:
                if not set(statement.source_paths).issubset(context.evidence_paths):
                    raise OptimizationProposalGroundingError()
                if not set(statement.target_match_indexes).issubset(context.match_indexes):
                    raise OptimizationProposalGroundingError()
                statements.append(
                    OptimizedExperienceStatementProposal(
                        text=statement.text,
                        source_paths=statement.source_paths,
                        target_match_indexes=statement.target_match_indexes,
                    )
                )
            proposals.append(
                ExperienceOptimizationProposal(context.experience_index, tuple(statements))
            )
        return CandidateOptimizationProposal(tuple(proposals))
