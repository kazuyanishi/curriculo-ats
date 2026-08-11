from resume_ai.modules.candidate.domain.entities import Candidate
from resume_ai.modules.candidate.domain.repositories import CandidateRepository


class LoadCandidate:
    def __init__(self, repository: CandidateRepository) -> None:
        self._repository = repository

    def execute(self) -> Candidate:
        return self._repository.get()
