from typing import Protocol

from resume_ai.modules.candidate.domain.entities import Candidate


class CandidateRepository(Protocol):
    """Repository contract for retrieving the candidate aggregate."""

    def get(self) -> Candidate:
        ...
