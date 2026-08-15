class OptimizationProposalGroundingError(Exception):
    """Raised when an AI optimization proposal exceeds its grounded context."""


class OptimizationTruthGateError(Exception):
    """Raised when optimization statement verification violates its contract."""
