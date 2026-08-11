from typing import get_type_hints

from resume_ai.modules.candidate.domain.entities import (
    Candidate,
    ContactInfo,
    PersonalInfo,
)
from resume_ai.modules.candidate.domain.repositories import CandidateRepository


class FakeCandidateRepository:
    def __init__(self, candidate: Candidate) -> None:
        self.candidate = candidate

    def get(self) -> Candidate:
        return self.candidate


def _get_candidate(repository: CandidateRepository) -> Candidate:
    return repository.get()


def _candidate() -> Candidate:
    return Candidate(
        personal_info=PersonalInfo(
            full_name="Jane Doe",
            city="Curitiba",
            state="PR",
            country="Brazil",
        ),
        contact_info=ContactInfo(
            email="jane@example.com",
            phone="+55 41 99999-0000",
        ),
    )


def test_candidate_repository_supports_structural_get_contract() -> None:
    candidate = _candidate()
    repository = FakeCandidateRepository(candidate)

    result = _get_candidate(repository)

    assert result is candidate


def test_candidate_repository_get_returns_candidate_type_hint() -> None:
    hints = get_type_hints(CandidateRepository.get)

    assert hints["return"] is Candidate
