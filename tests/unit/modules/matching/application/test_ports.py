import inspect
from typing import get_type_hints

from resume_ai.modules.candidate.domain.entities import Candidate, ContactInfo, PersonalInfo
from resume_ai.modules.jobs.domain.entities import JobCriteria
from resume_ai.modules.matching.application.ports import CandidateJobMatcher
from resume_ai.modules.matching.domain.entities import MatchingResult


class FakeCandidateJobMatcher:
    def __init__(self, result: MatchingResult) -> None:
        self.result = result
        self.received_candidate: Candidate | None = None
        self.received_criteria: JobCriteria | None = None

    def match(
        self,
        candidate: Candidate,
        criteria: JobCriteria,
    ) -> MatchingResult:
        self.received_candidate = candidate
        self.received_criteria = criteria
        return self.result


def _candidate() -> Candidate:
    return Candidate(
        personal_info=PersonalInfo(
            full_name="Jane Doe",
            city="Curitiba",
            state="PR",
            country="Brazil",
        ),
        contact_info=ContactInfo(email="jane@example.com", phone="+55 41 99999-0000"),
    )


def _match(
    matcher: CandidateJobMatcher,
    candidate: Candidate,
    criteria: JobCriteria,
) -> MatchingResult:
    return matcher.match(candidate, criteria)


def test_candidate_job_matcher_contract_type_hints() -> None:
    hints = get_type_hints(CandidateJobMatcher.match)
    parameters = inspect.signature(CandidateJobMatcher.match).parameters

    assert hints["candidate"] is Candidate
    assert hints["criteria"] is JobCriteria
    assert hints["return"] is MatchingResult
    assert parameters["self"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert parameters["candidate"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert parameters["criteria"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD


def test_structural_implementation_returns_the_same_result() -> None:
    expected_result = MatchingResult()
    matcher = FakeCandidateJobMatcher(expected_result)

    result = _match(matcher, _candidate(), JobCriteria())

    assert result is expected_result


def test_structural_implementation_receives_original_domain_objects() -> None:
    candidate = _candidate()
    criteria = JobCriteria()
    matcher = FakeCandidateJobMatcher(MatchingResult())

    _match(matcher, candidate, criteria)

    assert matcher.received_candidate is candidate
    assert matcher.received_criteria is criteria
