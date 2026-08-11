from dataclasses import FrozenInstanceError

import pytest

from resume_ai.core.exceptions import DomainError
from resume_ai.modules.jobs.domain.entities import (
    CriterionCategory,
    CriterionImportance,
    JobCriterion,
)
from resume_ai.modules.matching.domain.entities import (
    CriterionMatch,
    MatchingResult,
    MatchStatus,
)


def _criterion(value: str = "Python") -> JobCriterion:
    return JobCriterion(
        category=CriterionCategory.TECHNOLOGY,
        value=value,
        evidence=f"{value} is required.",
        importance=CriterionImportance.REQUIRED,
    )


def test_match_status_has_only_the_supported_values() -> None:
    assert [status.value for status in MatchStatus] == ["matched", "not_matched"]


@pytest.mark.parametrize("status", MatchStatus)
def test_criterion_match_accepts_a_job_criterion_and_status(status: MatchStatus) -> None:
    result = CriterionMatch(_criterion(), status)

    assert result.criterion.value == "Python"
    assert result.status is status


def test_criterion_match_is_frozen_and_slotted() -> None:
    result = CriterionMatch(_criterion(), MatchStatus.MATCHED)

    with pytest.raises(FrozenInstanceError):
        result.status = MatchStatus.NOT_MATCHED
    assert not hasattr(result, "__dict__")


@pytest.mark.parametrize("criterion", [None, "Python"])
def test_criterion_match_rejects_invalid_criterion(criterion: object) -> None:
    with pytest.raises(DomainError):
        CriterionMatch(criterion, MatchStatus.MATCHED)  # type: ignore[arg-type]


@pytest.mark.parametrize("status", ["matched", None])
def test_criterion_match_rejects_invalid_status(status: object) -> None:
    with pytest.raises(DomainError):
        CriterionMatch(_criterion(), status)  # type: ignore[arg-type]


def test_matching_result_empty_defaults_and_counts_are_zero() -> None:
    result = MatchingResult()

    assert result.matches == ()
    assert result.matched == ()
    assert result.not_matched == ()
    assert result.total == 0
    assert result.matched_count == 0
    assert result.not_matched_count == 0


def test_matching_result_filters_statuses_and_preserves_order() -> None:
    python = CriterionMatch(_criterion("Python"), MatchStatus.MATCHED)
    fastapi = CriterionMatch(_criterion("FastAPI"), MatchStatus.MATCHED)
    docker = CriterionMatch(_criterion("Docker"), MatchStatus.NOT_MATCHED)
    english = CriterionMatch(_criterion("English"), MatchStatus.MATCHED)
    result = MatchingResult(matches=(python, fastapi, docker, english))

    assert result.total == 4
    assert result.matched_count == 3
    assert result.not_matched_count == 1
    assert result.matched == (python, fastapi, english)
    assert result.not_matched == (docker,)


def test_matching_result_rejects_a_list() -> None:
    with pytest.raises(DomainError):
        MatchingResult(matches=[])  # type: ignore[arg-type]


def test_matching_result_rejects_invalid_elements() -> None:
    valid_match = CriterionMatch(_criterion(), MatchStatus.MATCHED)

    with pytest.raises(DomainError):
        MatchingResult(matches=(valid_match, "invalid"))  # type: ignore[arg-type]


def test_matching_result_is_frozen_and_slotted() -> None:
    result = MatchingResult()

    with pytest.raises(FrozenInstanceError):
        result.matches = ()
    assert not hasattr(result, "__dict__")
