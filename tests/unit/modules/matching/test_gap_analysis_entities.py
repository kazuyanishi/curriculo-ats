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
    GapAnalysisResult,
    MatchStatus,
)


def _match(status: MatchStatus) -> CriterionMatch:
    return CriterionMatch(
        criterion=JobCriterion(
            category=CriterionCategory.SKILL,
            value="Communication",
            evidence="Communication required.",
            importance=CriterionImportance.REQUIRED,
        ),
        status=status,
    )


def test_gap_analysis_result_defaults_to_empty_collections() -> None:
    result = GapAnalysisResult()

    assert result.gaps == ()
    assert result.unsupported == ()


@pytest.mark.parametrize("field", ["gaps", "unsupported"])
def test_gap_analysis_result_requires_tuples(field: str) -> None:
    with pytest.raises(DomainError):
        GapAnalysisResult(**{field: [_match(MatchStatus.NOT_MATCHED)]})


def test_gap_analysis_result_requires_criterion_matches() -> None:
    with pytest.raises(DomainError):
        GapAnalysisResult(gaps=(object(),))  # type: ignore[arg-type]


def test_gap_analysis_result_is_frozen_and_slotted() -> None:
    result = GapAnalysisResult(gaps=(_match(MatchStatus.NOT_MATCHED),))

    with pytest.raises(FrozenInstanceError):
        result.gaps = ()
    assert not hasattr(result, "__dict__")
