from resume_ai.bootstrap import build_grounded_optimize_candidate, build_optimize_candidate
from resume_ai.integrations.ai.config import AIConfig
from resume_ai.modules.candidate.domain.entities import Candidate
from resume_ai.modules.matching.domain.entities import MatchingResult
from resume_ai.modules.optimization.application.services import (
    DeterministicCandidateOptimizationProposalApplier,
    GroundedCandidateOptimizer,
    GroundedStandaloneCandidateOptimizer,
    OptimizeCandidate,
)
from resume_ai.modules.optimization.domain.services import DeterministicCandidateOptimizer
from resume_ai.modules.optimization.infrastructure.contextual_experience_optimizer import (
    AIContextualExperienceOptimizer,
)
from resume_ai.modules.optimization.infrastructure.semantic_optimization_truth_gate import (
    AISemanticOptimizationTruthGate,
)


def test_optimize_candidate_delegates_to_domain_optimizer() -> None:
    class RecordingOptimizer:
        def __init__(self) -> None:
            self.received = None
            self.output = object()

        def optimize(self, candidate: Candidate, result: MatchingResult) -> object:
            self.received = (candidate, result)
            return self.output

    optimizer = RecordingOptimizer()
    service = OptimizeCandidate(optimizer)  # type: ignore[arg-type]
    candidate = object()  # type: ignore[assignment]
    result = MatchingResult()

    assert service.execute(candidate, result) is optimizer.output  # type: ignore[arg-type]
    assert optimizer.received == (candidate, result)


def test_bootstrap_builds_functional_optimizer() -> None:
    service = build_optimize_candidate()

    assert isinstance(service, OptimizeCandidate)
    assert isinstance(service._optimizer, DeterministicCandidateOptimizer)


def test_bootstrap_builds_grounded_optimizer_without_calling_ai() -> None:
    service = build_grounded_optimize_candidate(AIConfig("key", "model"))

    assert isinstance(service, OptimizeCandidate)
    assert isinstance(service._optimizer, GroundedCandidateOptimizer)
    assert isinstance(
        service._optimizer._standalone_optimizer, GroundedStandaloneCandidateOptimizer
    )
    assert isinstance(service._optimizer._experience_optimizer, AIContextualExperienceOptimizer)
    assert isinstance(
        service._optimizer._experience_optimizer._truth_gate, AISemanticOptimizationTruthGate
    )
    assert isinstance(
        service._optimizer._proposal_applier, DeterministicCandidateOptimizationProposalApplier
    )
