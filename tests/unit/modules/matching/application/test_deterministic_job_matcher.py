import inspect
from typing import get_type_hints

import pytest

from resume_ai.core.exceptions import DomainError
from resume_ai.modules.candidate.domain.entities import Candidate, ContactInfo, PersonalInfo
from resume_ai.modules.jobs.domain.entities import (
    CriterionCategory,
    CriterionImportance,
    JobCriteria,
    JobCriterion,
)
from resume_ai.modules.matching.application.matchers import (
    DeterministicCandidateJobMatcher,
)
from resume_ai.modules.matching.application.ports import (
    CandidateCriterionMatcher,
    CandidateJobMatcher,
)
from resume_ai.modules.matching.domain.entities import (
    CriterionMatch,
    MatchingResult,
    MatchStatus,
)


class FakeCandidateCriterionMatcher:
    def __init__(self, results: tuple[CriterionMatch, ...]) -> None:
        self.results = results
        self.calls = 0
        self.received_candidates: list[Candidate] = []
        self.received_criteria: list[JobCriterion] = []

    def match(
        self,
        candidate: Candidate,
        criterion: JobCriterion,
    ) -> CriterionMatch:
        self.received_candidates.append(candidate)
        self.received_criteria.append(criterion)
        result = self.results[self.calls]
        self.calls += 1
        return result


class FailingCandidateCriterionMatcher:
    def __init__(self, fail_at: int) -> None:
        self.fail_at = fail_at
        self.calls = 0

    def match(
        self,
        candidate: Candidate,
        criterion: JobCriterion,
    ) -> CriterionMatch:
        self.calls += 1
        if self.calls == self.fail_at:
            raise DomainError("unsupported criterion")
        return CriterionMatch(criterion=criterion, status=MatchStatus.MATCHED)


def _candidate() -> Candidate:
    return Candidate(
        personal_info=PersonalInfo(
            full_name="Jane Doe",
            city="Curitiba",
            state="PR",
            country="Brazil",
        ),
        contact_info=ContactInfo(email="jane@example.com", phone="+55"),
    )


def _criterion(value: str) -> JobCriterion:
    return JobCriterion(
        category=CriterionCategory.TECHNOLOGY,
        value=value,
        evidence=f"{value} is required.",
        importance=CriterionImportance.REQUIRED,
    )


def _match_job(
    matcher: CandidateJobMatcher,
    candidate: Candidate,
    criteria: JobCriteria,
) -> MatchingResult:
    return matcher.match(candidate, criteria)


def test_matcher_is_structurally_compatible_and_preserves_order_and_identity() -> None:
    criteria_items = tuple(
        _criterion(value) for value in ("Python", "FastAPI", "Docker", "English")
    )
    criteria = JobCriteria(criteria=criteria_items)
    individual_results = tuple(
        CriterionMatch(
            criterion=criterion,
            status=MatchStatus.NOT_MATCHED if criterion.value == "Docker" else MatchStatus.MATCHED,
        )
        for criterion in criteria_items
    )
    candidate = _candidate()
    individual_matcher = FakeCandidateCriterionMatcher(individual_results)

    result = _match_job(
        DeterministicCandidateJobMatcher(individual_matcher),
        candidate,
        criteria,
    )

    assert result.total == 4
    assert result.matched_count == 3
    assert result.not_matched_count == 1
    assert result.matches == individual_results
    assert all(
        actual is expected
        for actual, expected in zip(result.matches, individual_results, strict=True)
    )
    assert individual_matcher.calls == 4
    assert individual_matcher.received_criteria == list(criteria_items)
    assert all(
        received is expected
        for received, expected in zip(
            individual_matcher.received_criteria, criteria_items, strict=True
        )
    )
    assert all(received is candidate for received in individual_matcher.received_candidates)


def test_empty_criteria_produces_empty_result_without_delegation() -> None:
    individual_matcher = FakeCandidateCriterionMatcher(())

    result = DeterministicCandidateJobMatcher(individual_matcher).match(
        _candidate(), JobCriteria()
    )

    assert result == MatchingResult()
    assert result.matches == ()
    assert individual_matcher.calls == 0


def test_matcher_propagates_error_and_stops_immediately() -> None:
    criteria_items = tuple(_criterion(value) for value in ("Python", "Education", "Docker"))
    individual_matcher = FailingCandidateCriterionMatcher(fail_at=2)

    with pytest.raises(DomainError, match="unsupported criterion"):
        DeterministicCandidateJobMatcher(individual_matcher).match(
            _candidate(), JobCriteria(criteria=criteria_items)
        )

    assert individual_matcher.calls == 2


def test_matcher_constructor_type_hints() -> None:
    hints = get_type_hints(DeterministicCandidateJobMatcher.__init__)

    assert hints["criterion_matcher"] is CandidateCriterionMatcher
    assert hints["return"] is type(None)


def test_matcher_method_type_hints() -> None:
    hints = get_type_hints(DeterministicCandidateJobMatcher.match)
    parameters = inspect.signature(DeterministicCandidateJobMatcher.match).parameters

    assert hints["candidate"] is Candidate
    assert hints["criteria"] is JobCriteria
    assert hints["return"] is MatchingResult
    assert parameters["candidate"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert parameters["criteria"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
