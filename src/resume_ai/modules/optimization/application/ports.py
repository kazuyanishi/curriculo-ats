from typing import Protocol

from resume_ai.modules.candidate.domain.entities import Candidate
from resume_ai.modules.matching.domain.entities import MatchingResult
from resume_ai.modules.optimization.application.planning import CandidateOptimizationPlan
from resume_ai.modules.optimization.application.proposals import CandidateOptimizationProposal


class CandidateExperienceOptimizer(Protocol):
    def optimize(
        self,
        candidate: Candidate,
        matching: MatchingResult,
        plan: CandidateOptimizationPlan,
    ) -> CandidateOptimizationProposal: ...
