import json

from resume_ai.integrations.ai.client import StructuredAIClient
from resume_ai.modules.candidate.domain.entities import Candidate
from resume_ai.modules.matching.application.catalog import build_candidate_evidence_catalog
from resume_ai.modules.matching.domain.entities import MatchingResult, MatchStatus
from resume_ai.modules.optimization.application.exceptions import OptimizationTruthGateError
from resume_ai.modules.optimization.application.proposals import (
    CandidateOptimizationProposal,
    OptimizationStatementVerdict,
    ValidatedCandidateOptimizationProposal,
    ValidatedExperienceOptimization,
)
from resume_ai.modules.optimization.infrastructure.optimization_truth_gate_prompt import (
    OPTIMIZATION_TRUTH_GATE_SYSTEM_PROMPT,
)
from resume_ai.modules.optimization.infrastructure.optimization_truth_gate_schemas import (
    CandidateOptimizationVerificationAIResponse,
)


class AISemanticOptimizationTruthGate:
    def __init__(self, client: StructuredAIClient) -> None:
        self._client = client

    def validate(
        self,
        candidate: Candidate,
        matching: MatchingResult,
        proposal: CandidateOptimizationProposal,
    ) -> ValidatedCandidateOptimizationProposal:
        if not proposal.experiences:
            return ValidatedCandidateOptimizationProposal()

        catalog = {item.path: item.text for item in build_candidate_evidence_catalog(candidate)}
        payload, expected = self._payload(candidate, matching, proposal, catalog)
        if not expected:
            return self._validated(proposal, {})

        response = self._client.generate(
            system_prompt=OPTIMIZATION_TRUTH_GATE_SYSTEM_PROMPT,
            user_prompt=json.dumps(payload, ensure_ascii=False),
            response_model=CandidateOptimizationVerificationAIResponse,
        )
        verdicts = self._verdicts(expected, response)
        return self._validated(proposal, verdicts)

    @staticmethod
    def _payload(
        candidate: Candidate,
        matching: MatchingResult,
        proposal: CandidateOptimizationProposal,
        catalog: dict[str, str],
    ) -> tuple[dict[str, object], dict[int, tuple[int, ...]]]:
        experiences = []
        expected: dict[int, tuple[int, ...]] = {}
        for experience in proposal.experiences:
            index = experience.experience_index
            if not 0 <= index < len(candidate.experiences) or index in expected:
                raise OptimizationTruthGateError()
            statements = []
            for statement_index, statement in enumerate(experience.statements):
                prefix = f"experiences[{index}]."
                if any(
                    not path.startswith(prefix) or path not in catalog
                    for path in statement.source_paths
                ):
                    raise OptimizationTruthGateError()
                if any(
                    not 0 <= match_index < len(matching.matches)
                    or matching.matches[match_index].status is not MatchStatus.MATCHED
                    for match_index in statement.target_match_indexes
                ):
                    raise OptimizationTruthGateError()
                statements.append(
                    {
                        "statement_index": statement_index,
                        "proposed_text": statement.text,
                        "source_evidence": [
                            {"path": path, "text": catalog[path]} for path in statement.source_paths
                        ],
                    }
                )
            if statements:
                expected[index] = tuple(range(len(statements)))
                experiences.append({"experience_index": index, "statements": statements})
        return {"experiences": experiences}, expected

    @staticmethod
    def _verdicts(
        expected: dict[int, tuple[int, ...]],
        response: CandidateOptimizationVerificationAIResponse,
    ) -> dict[tuple[int, int], OptimizationStatementVerdict]:
        returned = [item.experience_index for item in response.experiences]
        if set(returned) != set(expected) or len(returned) != len(set(returned)):
            raise OptimizationTruthGateError()

        verdicts = {}
        for experience in response.experiences:
            returned_indexes = [item.statement_index for item in experience.statements]
            if set(returned_indexes) != set(expected[experience.experience_index]) or len(
                returned_indexes
            ) != len(set(returned_indexes)):
                raise OptimizationTruthGateError()
            for item in experience.statements:
                verdicts[(experience.experience_index, item.statement_index)] = item.verdict
        return verdicts

    @staticmethod
    def _validated(
        proposal: CandidateOptimizationProposal,
        verdicts: dict[tuple[int, int], OptimizationStatementVerdict],
    ) -> ValidatedCandidateOptimizationProposal:
        return ValidatedCandidateOptimizationProposal(
            tuple(
                ValidatedExperienceOptimization(
                    experience.experience_index,
                    tuple(
                        statement
                        for statement_index, statement in enumerate(experience.statements)
                        if verdicts.get((experience.experience_index, statement_index))
                        is OptimizationStatementVerdict.SUPPORTED
                    ),
                )
                for experience in proposal.experiences
            )
        )
