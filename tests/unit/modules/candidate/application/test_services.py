from typing import get_type_hints

import pytest

from resume_ai.modules.candidate.application.services import LoadCandidate
from resume_ai.modules.candidate.domain.entities import Candidate, ContactInfo, PersonalInfo
from resume_ai.modules.candidate.domain.repositories import CandidateRepository


class FakeCandidateRepository:
    def __init__(self, candidate: Candidate) -> None:
        self.candidate = candidate
        self.get_calls = 0

    def get(self) -> Candidate:
        self.get_calls += 1
        return self.candidate


class FailingCandidateRepository:
    def get(self) -> Candidate:
        raise RuntimeError("repository failure")


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


def test_load_candidate_returns_repository_candidate() -> None:
    candidate = _candidate()
    repository = FakeCandidateRepository(candidate)

    result = LoadCandidate(repository).execute()

    assert result is candidate
    assert repository.get_calls == 1


def test_load_candidate_delegates_on_every_execution() -> None:
    repository = FakeCandidateRepository(_candidate())
    service = LoadCandidate(repository)

    service.execute()
    service.execute()

    assert repository.get_calls == 2


def test_load_candidate_propagates_repository_exception() -> None:
    service = LoadCandidate(FailingCandidateRepository())

    with pytest.raises(RuntimeError, match="repository failure"):
        service.execute()


def test_load_candidate_constructor_uses_repository_protocol() -> None:
    hints = get_type_hints(LoadCandidate.__init__)

    assert hints["repository"] is CandidateRepository


def test_load_candidate_execute_returns_candidate_type() -> None:
    hints = get_type_hints(LoadCandidate.execute)

    assert hints["return"] is Candidate
