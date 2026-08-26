import json
import re

from resume_ai.integrations.ai.client import StructuredAIClient
from resume_ai.modules.candidate.domain.entities import Candidate
from resume_ai.modules.matching.application.catalog import build_candidate_evidence_catalog
from resume_ai.modules.matching.application.provenance import MatchingProvenanceGate
from resume_ai.modules.matching.domain.entities import MatchingResult, MatchStatus
from resume_ai.modules.optimization.application.exceptions import OptimizationProposalGroundingError
from resume_ai.modules.optimization.application.planning import (
    CandidateOptimizationPlan,
    ProjectOptimizationContext,
)
from resume_ai.modules.optimization.application.ports import CandidateProjectOptimizationTruthGate
from resume_ai.modules.optimization.application.proposals import (
    CandidateProjectOptimizationProposal,
    OptimizedProjectDescriptionProposal,
    ProjectOptimizationProposal,
)
from resume_ai.modules.optimization.infrastructure.contextual_project_prompt import (
    CONTEXTUAL_PROJECT_OPTIMIZATION_SYSTEM_PROMPT,
)
from resume_ai.modules.optimization.infrastructure.contextual_project_schemas import (
    CandidateProjectOptimizationAIResponse,
)

_PROJECT_PATH = re.compile(r"^projects\[(\d+)]\.description$")


class AIContextualProjectOptimizer:
    def __init__(
        self, client: StructuredAIClient, truth_gate: CandidateProjectOptimizationTruthGate
    ) -> None:
        self._client = client
        self._truth_gate = truth_gate

    def optimize(
        self, candidate: Candidate, matching: MatchingResult, plan: CandidateOptimizationPlan
    ) -> CandidateProjectOptimizationProposal:
        if not plan.project_contexts:
            proposal = CandidateProjectOptimizationProposal()
            self._truth_gate.validate(candidate, proposal)
            return proposal
        MatchingProvenanceGate().validate(candidate, matching)
        catalog = {item.path: item.text for item in build_candidate_evidence_catalog(candidate)}
        response = self._client.generate(
            system_prompt=CONTEXTUAL_PROJECT_OPTIMIZATION_SYSTEM_PROMPT,
            user_prompt=json.dumps(self._payload(matching, plan, catalog), ensure_ascii=False),
            response_model=CandidateProjectOptimizationAIResponse,
        )
        proposal = self._proposal(plan, matching, response)
        self._truth_gate.validate(candidate, proposal)
        return proposal

    @staticmethod
    def _payload(
        matching: MatchingResult, plan: CandidateOptimizationPlan, catalog: dict[str, str]
    ) -> dict[str, object]:
        contexts = []
        for context in plan.project_contexts:
            if any(
                (item := _PROJECT_PATH.fullmatch(path)) is None
                or int(item.group(1)) != context.project_index
                for path in context.evidence_paths
            ):
                raise OptimizationProposalGroundingError()
            criteria = []
            for index in context.match_indexes:
                if (
                    not 0 <= index < len(matching.matches)
                    or matching.matches[index].status is not MatchStatus.MATCHED
                ):
                    raise OptimizationProposalGroundingError()
                match = matching.matches[index]
                criterion = match.criterion
                criteria.append(
                    {
                        "match_index": index,
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
                    "project_index": context.project_index,
                    "criteria": criteria,
                    "candidate_evidence": evidence,
                }
            )
        return {"project_contexts": contexts}

    @staticmethod
    def _proposal(
        plan: CandidateOptimizationPlan,
        matching: MatchingResult,
        response: CandidateProjectOptimizationAIResponse,
    ) -> CandidateProjectOptimizationProposal:
        expected = [context.project_index for context in plan.project_contexts]
        returned = [item.project_index for item in response.projects]
        if set(expected) != set(returned) or len(returned) != len(set(returned)):
            raise OptimizationProposalGroundingError()
        by_index = {item.project_index: item for item in response.projects}
        proposals = []
        for context in plan.project_contexts:
            description = by_index[context.project_index].description
            if description is None:
                proposals.append(ProjectOptimizationProposal(context.project_index))
                continue
            if not set(description.source_paths).issubset(context.evidence_paths):
                raise OptimizationProposalGroundingError()
            if not set(description.target_match_indexes).issubset(context.match_indexes):
                raise OptimizationProposalGroundingError()
            AIContextualProjectOptimizer._validate_binding(
                matching, context, description.source_paths, description.target_match_indexes
            )
            proposals.append(
                ProjectOptimizationProposal(
                    context.project_index,
                    OptimizedProjectDescriptionProposal(
                        description.text, description.source_paths, description.target_match_indexes
                    ),
                )
            )
        return CandidateProjectOptimizationProposal(tuple(proposals))

    @staticmethod
    def _validate_binding(
        matching: MatchingResult,
        context: ProjectOptimizationContext,
        sources: tuple[str, ...],
        targets: tuple[int, ...],
    ) -> None:
        target_paths: set[str] = set()
        for index in targets:
            if not 0 <= index < len(matching.matches) or index not in context.match_indexes:
                raise OptimizationProposalGroundingError()
            match = matching.matches[index]
            if match.status is not MatchStatus.MATCHED or not match.candidate_evidence_paths:
                raise OptimizationProposalGroundingError()
            paths = set(match.candidate_evidence_paths)
            if not set(sources).intersection(paths):
                raise OptimizationProposalGroundingError()
            target_paths.update(paths)
        if not set(sources).issubset(target_paths):
            raise OptimizationProposalGroundingError()
