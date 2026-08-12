from resume_ai.bootstrap import build_analyze_matching_gaps
from resume_ai.modules.jobs.domain.entities import (
    CriterionCategory,
    JobCriterion,
)
from resume_ai.modules.matching.application.services import AnalyzeMatchingGaps
from resume_ai.modules.matching.domain.entities import (
    CriterionMatch,
    MatchingResult,
    MatchStatus,
)
from resume_ai.modules.matching.domain.services import DeterministicGapAnalyzer


def _not_matched() -> CriterionMatch:
    return CriterionMatch(
        criterion=JobCriterion(
            category=CriterionCategory.SKILL,
            value="Python",
            evidence="Python required.",
        ),
        status=MatchStatus.NOT_MATCHED,
    )


def test_bootstrap_builds_functional_gap_analysis_service() -> None:
    service = build_analyze_matching_gaps()
    match = _not_matched()

    result = service.execute(MatchingResult(matches=(match,)))

    assert isinstance(service, AnalyzeMatchingGaps)
    assert result.gaps == (match,)


def test_bootstrap_uses_expected_composition_types() -> None:
    service = build_analyze_matching_gaps()

    assert isinstance(service, AnalyzeMatchingGaps)
    assert isinstance(service._analyzer, DeterministicGapAnalyzer)
