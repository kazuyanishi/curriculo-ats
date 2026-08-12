from dataclasses import FrozenInstanceError
from typing import get_type_hints

import pytest

from resume_ai.core.exceptions import DomainError
from resume_ai.modules.matching.domain.entities import MatchingScore


def test_matching_score_accepts_valid_float_values() -> None:
    assert MatchingScore(score=0.75, coverage=1.0) == MatchingScore(
        score=0.75, coverage=1.0
    )


@pytest.mark.parametrize(
    ("score", "coverage"),
    [(None, 0.0), (None, None), (0.0, 0.4), (1.0, 1.0)],
)
def test_matching_score_accepts_none_and_boundary_values(
    score: float | None, coverage: float | None
) -> None:
    result = MatchingScore(score=score, coverage=coverage)

    assert result.score == score
    assert result.coverage == coverage


@pytest.mark.parametrize("field", ["score", "coverage"])
@pytest.mark.parametrize("value", [-0.1, 1.1])
def test_matching_score_rejects_values_outside_interval(field: str, value: float) -> None:
    data = {"score": 0.5, "coverage": 0.5}
    data[field] = value

    with pytest.raises(DomainError):
        MatchingScore(**data)


@pytest.mark.parametrize("field", ["score", "coverage"])
@pytest.mark.parametrize("value", ["0.5", [], {}, 1, True])
def test_matching_score_rejects_non_float_values(field: str, value: object) -> None:
    data = {"score": 0.5, "coverage": 0.5}
    data[field] = value

    with pytest.raises(DomainError):
        MatchingScore(**data)


def test_matching_score_does_not_validate_relationship_between_fields() -> None:
    assert MatchingScore(score=0.5, coverage=0.0) == MatchingScore(
        score=0.5, coverage=0.0
    )
    assert MatchingScore(score=None, coverage=1.0) == MatchingScore(
        score=None, coverage=1.0
    )


def test_matching_score_is_frozen_and_slotted() -> None:
    result = MatchingScore(score=0.5, coverage=0.5)

    with pytest.raises(FrozenInstanceError):
        result.score = 0.75
    assert not hasattr(result, "__dict__")


def test_matching_score_type_hints() -> None:
    hints = get_type_hints(MatchingScore)

    assert hints["score"] == float | None
    assert hints["coverage"] == float | None
