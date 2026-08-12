from typing import get_type_hints

from resume_ai.modules.jobs.domain.entities import (
    CriterionCategory,
    CriterionImportance,
    EducationRequirement,
    ExperienceRequirement,
    JobCriterion,
)
from resume_ai.modules.matching.application.services import AnalyzeMatchingGaps
from resume_ai.modules.matching.domain.entities import (
    CriterionMatch,
    GapAnalysisResult,
    MatchingResult,
    MatchStatus,
)
from resume_ai.modules.matching.domain.services import DeterministicGapAnalyzer


def _match(status: MatchStatus, value: str) -> CriterionMatch:
    return CriterionMatch(
        criterion=JobCriterion(
            category=CriterionCategory.SKILL,
            value=value,
            evidence=f"{value} required.",
            importance=CriterionImportance.REQUIRED,
        ),
        status=status,
    )


def test_analyzer_returns_empty_result_for_empty_matching_result() -> None:
    assert DeterministicGapAnalyzer().analyze(MatchingResult()) == GapAnalysisResult()


def test_analyzer_ignores_matched_and_preserves_gap_order_and_identity() -> None:
    matched = _match(MatchStatus.MATCHED, "Python")
    first_gap = _match(MatchStatus.NOT_MATCHED, "FastAPI")
    unsupported = _match(MatchStatus.UNSUPPORTED, "Degree")
    second_gap = _match(MatchStatus.NOT_MATCHED, "Docker")
    result = DeterministicGapAnalyzer().analyze(
        MatchingResult(matches=(matched, first_gap, unsupported, second_gap))
    )

    assert result.gaps == (first_gap, second_gap)
    assert result.unsupported == (unsupported,)
    assert result.gaps[0] is first_gap
    assert result.gaps[1] is second_gap
    assert result.unsupported[0] is unsupported


def test_analyzer_preserves_required_preferred_order() -> None:
    required = _match(MatchStatus.NOT_MATCHED, "Required")
    preferred = CriterionMatch(
        criterion=JobCriterion(
            category=CriterionCategory.TOOL,
            value="Preferred",
            evidence="Preferred.",
            importance=CriterionImportance.PREFERRED,
        ),
        status=MatchStatus.NOT_MATCHED,
    )

    result = DeterministicGapAnalyzer().analyze(
        MatchingResult(matches=(preferred, required))
    )

    assert result.gaps == (preferred, required)


def test_analyzer_preserves_structured_criterion_references() -> None:
    education_requirement = EducationRequirement(field_of_study="Computer Science")
    education_criterion = JobCriterion(
        category=CriterionCategory.EDUCATION,
        value="Computer Science degree",
        evidence="Computer Science degree required.",
        education_requirement=education_requirement,
    )
    education_match = CriterionMatch(
        criterion=education_criterion,
        status=MatchStatus.NOT_MATCHED,
    )
    experience_requirement = ExperienceRequirement(role="Backend Developer")
    experience_criterion = JobCriterion(
        category=CriterionCategory.EXPERIENCE,
        value="Backend Developer experience",
        evidence="Backend Developer experience required.",
        experience_requirement=experience_requirement,
    )
    experience_match = CriterionMatch(
        criterion=experience_criterion,
        status=MatchStatus.NOT_MATCHED,
    )

    result = DeterministicGapAnalyzer().analyze(
        MatchingResult(matches=(education_match, experience_match))
    )

    assert result.gaps[0] is education_match
    assert result.gaps[1] is experience_match
    assert result.gaps[0].criterion is education_criterion
    assert result.gaps[1].criterion is experience_criterion
    assert result.gaps[0].criterion.education_requirement is education_requirement
    assert result.gaps[1].criterion.experience_requirement is experience_requirement


def test_analyze_matching_gaps_delegates_to_analyzer() -> None:
    class RecordingAnalyzer:
        def __init__(self) -> None:
            self.received = None
            self.output = GapAnalysisResult()

        def analyze(self, result: MatchingResult) -> GapAnalysisResult:
            self.received = result
            return self.output

    analyzer = RecordingAnalyzer()
    matching_result = MatchingResult()
    service = AnalyzeMatchingGaps(analyzer)  # type: ignore[arg-type]

    assert service.execute(matching_result) is analyzer.output
    assert analyzer.received is matching_result


def test_gap_analysis_type_hints() -> None:
    domain_hints = get_type_hints(DeterministicGapAnalyzer.analyze)
    application_hints = get_type_hints(AnalyzeMatchingGaps.execute)

    assert domain_hints["result"] is MatchingResult
    assert domain_hints["return"] is GapAnalysisResult
    assert application_hints["result"] is MatchingResult
    assert application_hints["return"] is GapAnalysisResult
