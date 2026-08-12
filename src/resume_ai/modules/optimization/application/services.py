from resume_ai.modules.candidate.domain.entities import Candidate
from resume_ai.modules.matching.domain.entities import MatchingResult
from resume_ai.modules.optimization.domain.services import DeterministicCandidateOptimizer


class OptimizeCandidate:
    def __init__(self, optimizer: DeterministicCandidateOptimizer) -> None:
        self._optimizer = optimizer

    def execute(self, candidate: Candidate, result: MatchingResult) -> Candidate:
        return self._optimizer.optimize(candidate, result)
