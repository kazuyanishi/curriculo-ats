from typing import get_type_hints

import pytest

from resume_ai.modules.matching.application.services import CalculateMatchingScore
from resume_ai.modules.matching.domain.entities import MatchingResult, MatchingScore
from resume_ai.modules.matching.domain.services import MatchingScoreCalculator


class FakeMatchingScoreCalculator:
    def __init__(self, score: MatchingScore) -> None:
        self.score = score
        self.calls = 0
        self.received_result: MatchingResult | None = None

    def calculate(self, result: MatchingResult) -> MatchingScore:
        self.calls += 1
        self.received_result = result
        return self.score


class FailingMatchingScoreCalculator:
    def calculate(self, result: MatchingResult) -> MatchingScore:
        raise RuntimeError("calculator failure")


def test_execute_delegates_once_with_same_result_and_returns_same_score() -> None:
    matching_result = MatchingResult()
    matching_score = MatchingScore(score=0.75, coverage=1.0)
    calculator = FakeMatchingScoreCalculator(matching_score)

    result = CalculateMatchingScore(calculator).execute(matching_result)  # type: ignore[arg-type]

    assert calculator.calls == 1
    assert calculator.received_result is matching_result
    assert result is matching_score


def test_execute_propagates_calculator_error() -> None:
    with pytest.raises(RuntimeError, match="calculator failure"):
        CalculateMatchingScore(FailingMatchingScoreCalculator()).execute(MatchingResult())  # type: ignore[arg-type]


def test_calculate_matching_score_type_hints() -> None:
    constructor_hints = get_type_hints(CalculateMatchingScore.__init__)
    execute_hints = get_type_hints(CalculateMatchingScore.execute)

    assert constructor_hints["calculator"] is MatchingScoreCalculator
    assert execute_hints["result"] is MatchingResult
    assert execute_hints["return"] is MatchingScore
