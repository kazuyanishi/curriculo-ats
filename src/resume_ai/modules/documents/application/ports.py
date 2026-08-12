from typing import Protocol

from resume_ai.modules.candidate.domain.entities import Candidate


class CandidateDocumentRenderer(Protocol):
    def render(self, candidate: Candidate) -> bytes:
        ...
