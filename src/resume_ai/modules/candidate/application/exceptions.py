from enum import StrEnum


class ResumeTextExtractionError(Exception):
    """Raised when resume text cannot be extracted."""


class GroundingReason(StrEnum):
    VALUE_NOT_IN_EVIDENCE = "value_not_in_evidence"
    EVIDENCE_NOT_IN_RESUME_TEXT = "evidence_not_in_resume_text"


class ResumeCandidateGroundingError(Exception):
    """Raised when extracted resume facts are not grounded in source text."""

    def __init__(
        self,
        path: str,
        reason: GroundingReason,
        whitespace_normalized_match: bool | None = None,
    ) -> None:
        self.path = path
        self.reason = reason
        self.whitespace_normalized_match = whitespace_normalized_match
        super().__init__("Candidate resume extraction is not grounded in source text")
