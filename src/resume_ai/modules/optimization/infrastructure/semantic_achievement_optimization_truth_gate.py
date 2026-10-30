import json

from resume_ai.integrations.ai.client import StructuredAIClient
from resume_ai.modules.candidate.domain.entities import Candidate
from resume_ai.modules.matching.application.catalog import build_candidate_evidence_catalog
from resume_ai.modules.optimization.application.exceptions import OptimizationProposalGroundingError
from resume_ai.modules.optimization.application.proposals import (
    CandidateAchievementOptimizationProposal,
    OptimizedAchievementStatementProposal,
)
from resume_ai.modules.optimization.infrastructure import (
    achievement_optimization_truth_gate_prompt,
    achievement_optimization_truth_gate_schemas,
)


class AISemanticAchievementOptimizationTruthGate:
    def __init__(self, client: StructuredAIClient) -> None:
        self._client = client

    def validate(
        self,
        candidate: Candidate,
        proposal: CandidateAchievementOptimizationProposal,
    ) -> None:
        if not proposal.experiences:
            return
        catalog = {item.path: item.text for item in build_candidate_evidence_catalog(candidate)}
        for experience in proposal.experiences:
            if not 0 <= experience.experience_index < len(candidate.experiences):
                raise OptimizationProposalGroundingError()
            for statement in experience.statements:
                response = self._client.generate(
                    system_prompt=(
                        achievement_optimization_truth_gate_prompt.ACHIEVEMENT_OPTIMIZATION_TRUTH_GATE_SYSTEM_PROMPT
                    ),
                    user_prompt=json.dumps(
                        self._payload(experience.experience_index, statement, catalog),
                        ensure_ascii=False,
                    ),
                    response_model=(
                        achievement_optimization_truth_gate_schemas.AchievementOptimizationStatementTruthDecision
                    ),
                )
                if not response.fully_supported:
                    raise OptimizationProposalGroundingError()

    @staticmethod
    def _payload(
        experience_index: int,
        statement: OptimizedAchievementStatementProposal,
        catalog: dict[str, str],
    ) -> dict[str, object]:
        prefix = f"experiences[{experience_index}].achievements["
        if any(
            not path.startswith(prefix) or path not in catalog for path in statement.source_paths
        ):
            raise OptimizationProposalGroundingError()
        return {
            "proposed_text": statement.text,
            "source_evidence": [
                {"path": path, "text": catalog[path]} for path in statement.source_paths
            ],
        }
