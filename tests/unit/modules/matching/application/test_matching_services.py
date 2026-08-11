import inspect
from typing import get_type_hints

import pytest

from resume_ai.modules.candidate.domain.entities import Candidate, ContactInfo, PersonalInfo
from resume_ai.modules.jobs.domain.entities import JobCriteria
from resume_ai.modules.matching.application.ports import CandidateJobMatcher
from resume_ai.modules.matching.application.services import MatchCandidateToJob
from resume_ai.modules.matching.domain.entities import MatchingResult


class FakeCandidateJobMatcher:
    def __init__(self, result: MatchingResult) -> None:
        self.result = result
        self.calls = 0
        self.received_candidates: list[Candidate] = []
        self.received_criteria: list[JobCriteria] = []

    def match(
        self,
        candidate: Candidate,
        criteria: JobCriteria,
    ) -> MatchingResult:
        self.calls += 1
        self.received_candidates.append(candidate)
        self.received_criteria.append(criteria)
        return self.result


class FailingCandidateJobMatcher:
    def match(
        self,
        candidate: Candidate,
        criteria: JobCriteria,
    ) -> MatchingResult:
        raise RuntimeError("matching failure")


def _candidate(name: str) -> Candidate:
    return Candidate(
        personal_info=PersonalInfo(
            full_name=name,
            city="Curitiba",
            state="PR",
            country="Brazil",
        ),
        contact_info=ContactInfo(email="candidate@example.com", phone="+55"),
    )


def test_service_delegates_and_preserves_result_identity() -> None:
    expected_result = MatchingResult()
    matcher = FakeCandidateJobMatcher(expected_result)
    service = MatchCandidateToJob(matcher)

    result = service.execute(_candidate("Jane Doe"), JobCriteria())

    assert result is expected_result
    assert matcher.calls == 1


def test_service_passes_the_original_arguments() -> None:
    candidate = _candidate("Jane Doe")
    criteria = JobCriteria()
    matcher = FakeCandidateJobMatcher(MatchingResult())

    MatchCandidateToJob(matcher).execute(candidate, criteria)

    assert matcher.received_candidates == [candidate]
    assert matcher.received_criteria == [criteria]
    assert matcher.received_candidates[0] is candidate
    assert matcher.received_criteria[0] is criteria


def test_service_delegates_each_execution_once_in_order() -> None:
    candidate_a = _candidate("Jane Doe")
    criteria_a = JobCriteria()
    candidate_b = _candidate("John Doe")
    criteria_b = JobCriteria()
    matcher = FakeCandidateJobMatcher(MatchingResult())
    service = MatchCandidateToJob(matcher)

    service.execute(candidate_a, criteria_a)
    service.execute(candidate_b, criteria_b)

    assert matcher.calls == 2
    assert matcher.received_candidates == [candidate_a, candidate_b]
    assert matcher.received_criteria == [criteria_a, criteria_b]


def test_service_propagates_matcher_errors() -> None:
    with pytest.raises(RuntimeError, match="matching failure"):
        MatchCandidateToJob(FailingCandidateJobMatcher()).execute(
            _candidate("Jane Doe"), JobCriteria()
        )


def test_service_type_hints() -> None:
    init_hints = get_type_hints(MatchCandidateToJob.__init__)
    execute_hints = get_type_hints(MatchCandidateToJob.execute)
    parameters = inspect.signature(MatchCandidateToJob.execute).parameters

    assert init_hints["matcher"] is CandidateJobMatcher
    assert init_hints["return"] is type(None)
    assert execute_hints["candidate"] is Candidate
    assert execute_hints["criteria"] is JobCriteria
    assert execute_hints["return"] is MatchingResult
    assert all(
        parameters[name].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
        for name in ("self", "candidate", "criteria")
    )
