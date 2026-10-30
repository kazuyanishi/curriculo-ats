import json
import re

from resume_ai.integrations.ai.client import StructuredAIClient
from resume_ai.modules.candidate.domain.entities import Candidate
from resume_ai.modules.matching.application.catalog import build_candidate_evidence_catalog
from resume_ai.modules.optimization.application.exceptions import OptimizationProposalGroundingError
from resume_ai.modules.optimization.application.proposals import (
    CandidateProjectOptimizationProposal,
)
from resume_ai.modules.optimization.infrastructure.project_optimization_truth_gate_prompt import (
    PROJECT_OPTIMIZATION_TRUTH_GATE_SYSTEM_PROMPT,
)
from resume_ai.modules.optimization.infrastructure.project_optimization_truth_gate_schemas import (
    ProjectOptimizationTruthDecision,
)

_PROJECT_PATH = re.compile(r"^projects\[(\d+)]\.description$")


class AISemanticProjectOptimizationTruthGate:
    def __init__(self, client: StructuredAIClient) -> None:
        self._client = client

    def validate(
        self, candidate: Candidate, proposal: CandidateProjectOptimizationProposal
    ) -> None:
        catalog = {item.path: item.text for item in build_candidate_evidence_catalog(candidate)}
        for project in proposal.projects:
            if not 0 <= project.project_index < len(candidate.projects):
                raise OptimizationProposalGroundingError()
            if project.description is None:
                continue
            paths = project.description.source_paths
            if any(
                (match := _PROJECT_PATH.fullmatch(path)) is None
                or int(match.group(1)) != project.project_index
                or path not in catalog
                for path in paths
            ):
                raise OptimizationProposalGroundingError()
            response = self._client.generate(
                system_prompt=PROJECT_OPTIMIZATION_TRUTH_GATE_SYSTEM_PROMPT,
                user_prompt=json.dumps(
                    {
                        "proposed_text": project.description.text,
                        "source_evidence": [
                            {"path": path, "text": catalog[path]} for path in paths
                        ],
                    },
                    ensure_ascii=False,
                ),
                response_model=ProjectOptimizationTruthDecision,
            )
            if not response.fully_supported:
                raise OptimizationProposalGroundingError()
