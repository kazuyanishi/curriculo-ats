from resume_ai.bootstrap import build_optimize_candidate
from resume_ai.modules.candidate.domain.entities import Candidate
from resume_ai.modules.matching.domain.entities import MatchingResult
from resume_ai.modules.optimization.application.services import OptimizeCandidate
from resume_ai.modules.optimization.domain.services import DeterministicCandidateOptimizer


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
