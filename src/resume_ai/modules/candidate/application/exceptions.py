class ResumeTextExtractionError(Exception):
    """Raised when resume text cannot be extracted."""


class ResumeCandidateGroundingError(Exception):
    """Raised when extracted resume facts are not grounded in source text."""
