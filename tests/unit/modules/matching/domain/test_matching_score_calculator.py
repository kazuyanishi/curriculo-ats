from typing import get_type_hints

import pytest

from resume_ai.modules.jobs.domain.entities import (
    CriterionCategory,
    CriterionImportance,
    JobCriterion,
)
from resume_ai.modules.matching.domain.entities import (
    CriterionMatch,
    MatchingResult,
    MatchingScore,
    MatchStatus,
)
from resume_ai.modules.matching.domain.services import MatchingScoreCalculator


def _criterion(value: str) -> JobCriterion:
    return JobCriterion(
        category=CriterionCategory.TECHNOLOGY,
        value=value,
        evidence=f"{value} is required.",
        importance=CriterionImportance.REQUIRED,
    )


def _result(*statuses: MatchStatus) -> MatchingResult:
    return MatchingResult(
        matches=tuple(
            CriterionMatch(_criterion(f"criterion-{index}"), status)
            for index, status in enumerate(statuses)
        )
    )


def test_empty_result_has_no_score_or_coverage() -> None:
    result = MatchingScoreCalculator().calculate(MatchingResult())

    assert result == MatchingScore(score=None, coverage=None)


def test_three_matched_and_one_not_matched() -> None:
    result = MatchingScoreCalculator().calculate(
        _result(
            MatchStatus.MATCHED,
            MatchStatus.MATCHED,
            MatchStatus.MATCHED,
            MatchStatus.NOT_MATCHED,
        )
    )

    assert result == MatchingScore(score=0.75, coverage=1.0)


def test_unsupported_is_excluded_from_score_but_included_in_coverage() -> None:
    result = MatchingScoreCalculator().calculate(
        _result(
            MatchStatus.MATCHED,
            MatchStatus.MATCHED,
            MatchStatus.MATCHED,
            MatchStatus.NOT_MATCHED,
            MatchStatus.UNSUPPORTED,
            MatchStatus.UNSUPPORTED,
            MatchStatus.UNSUPPORTED,
            MatchStatus.UNSUPPORTED,
            MatchStatus.UNSUPPORTED,
        )
    )

    assert result.score == 0.75
    assert result.coverage == pytest.approx(4 / 9)


def test_all_not_matched_has_zero_score() -> None:
    result = MatchingScoreCalculator().calculate(
        _result(
            MatchStatus.NOT_MATCHED,
            MatchStatus.NOT_MATCHED,
            MatchStatus.NOT_MATCHED,
            MatchStatus.NOT_MATCHED,
        )
    )

    assert result == MatchingScore(score=0.0, coverage=1.0)


def test_only_unsupported_has_no_score_and_zero_coverage() -> None:
    result = MatchingScoreCalculator().calculate(
        _result(
            MatchStatus.UNSUPPORTED,
            MatchStatus.UNSUPPORTED,
            MatchStatus.UNSUPPORTED,
            MatchStatus.UNSUPPORTED,
        )
    )

    assert result == MatchingScore(score=None, coverage=0.0)


def test_only_matched_has_perfect_score_and_coverage() -> None:
    result = MatchingScoreCalculator().calculate(
        _result(MatchStatus.MATCHED, MatchStatus.MATCHED, MatchStatus.MATCHED)
    )

    assert result == MatchingScore(score=1.0, coverage=1.0)


def test_unsupported_keeps_score_but_reduces_coverage() -> None:
    without_unsupported = MatchingScoreCalculator().calculate(
        _result(
            MatchStatus.MATCHED,
            MatchStatus.MATCHED,
            MatchStatus.MATCHED,
            MatchStatus.NOT_MATCHED,
        )
    )
    with_unsupported = MatchingScoreCalculator().calculate(
        _result(
            MatchStatus.MATCHED,
            MatchStatus.MATCHED,
            MatchStatus.MATCHED,
            MatchStatus.NOT_MATCHED,
            MatchStatus.UNSUPPORTED,
            MatchStatus.UNSUPPORTED,
            MatchStatus.UNSUPPORTED,
            MatchStatus.UNSUPPORTED,
            MatchStatus.UNSUPPORTED,
        )
    )

    assert without_unsupported.score == with_unsupported.score == 0.75
    assert without_unsupported.coverage > with_unsupported.coverage


def test_calculator_type_hints() -> None:
    hints = get_type_hints(MatchingScoreCalculator.calculate)

    assert hints["result"] is MatchingResult
    assert hints["return"] is MatchingScore
