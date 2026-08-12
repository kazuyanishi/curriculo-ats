import inspect
from typing import get_type_hints

from resume_ai.bootstrap import (
    build_calculate_matching_score,
    build_match_and_score_candidate_to_job,
    build_match_candidate_to_job,
)
from resume_ai.modules.candidate.domain.entities import (
    Candidate,
    ContactInfo,
    Language,
    PersonalInfo,
    Skill,
    Technology,
    Tool,
)
from resume_ai.modules.jobs.domain.entities import (
    CriterionCategory,
    CriterionImportance,
    JobCriteria,
    JobCriterion,
)
from resume_ai.modules.matching.application.services import (
    CalculateMatchingScore,
    MatchAndScoreCandidateToJob,
    MatchCandidateToJob,
)
from resume_ai.modules.matching.domain.entities import (
    MatchingResult,
    MatchingScore,
    MatchStatus,
)


def _candidate() -> Candidate:
    return Candidate(
        personal_info=PersonalInfo(
            full_name="Jane Doe",
            city="Curitiba",
            state="PR",
            country="Brazil",
        ),
        contact_info=ContactInfo(email="jane@example.com", phone="+55"),
        skills=(Skill("Communication"),),
        technologies=(Technology("Python"),),
        tools=(Tool("Docker"),),
        languages=(Language("English"),),
    )


def _criterion(category: CriterionCategory, value: str) -> JobCriterion:
    return JobCriterion(
        category=category,
        value=value,
        evidence=f"{value} is required.",
        importance=CriterionImportance.REQUIRED,
    )


def test_builder_composes_real_matching_pipeline() -> None:
    python = _criterion(CriterionCategory.TECHNOLOGY, "PYTHON")
    fastapi = _criterion(CriterionCategory.TECHNOLOGY, "FastAPI")
    docker = _criterion(CriterionCategory.TOOL, "Docker")
    english = _criterion(CriterionCategory.LANGUAGE, "English")

    result = build_match_candidate_to_job().execute(
        _candidate(), JobCriteria(criteria=(python, fastapi, docker, english))
    )

    assert result.total == 4
    assert result.matched_count == 3
    assert result.not_matched_count == 1
    assert [match.status for match in result.matches] == [
        MatchStatus.MATCHED,
        MatchStatus.NOT_MATCHED,
        MatchStatus.MATCHED,
        MatchStatus.MATCHED,
    ]
    assert [match.criterion for match in result.matches] == [python, fastapi, docker, english]
    assert all(
        match.criterion is criterion
        for match, criterion in zip(
            result.matches, (python, fastapi, docker, english), strict=True
        )
    )


def test_builder_supports_empty_criteria() -> None:
    result = build_match_candidate_to_job().execute(_candidate(), JobCriteria())

    assert result.matches == ()
    assert result.total == 0
    assert result.matched_count == 0
    assert result.not_matched_count == 0


def test_builder_returns_unsupported_and_continues_processing() -> None:
    python = _criterion(CriterionCategory.TECHNOLOGY, "Python")
    education = _criterion(CriterionCategory.EDUCATION, "Computer Science")
    docker = _criterion(CriterionCategory.TOOL, "Docker")
    experience = _criterion(CriterionCategory.EXPERIENCE, "Backend Developer")
    english = _criterion(CriterionCategory.LANGUAGE, "English")
    criteria = JobCriteria(criteria=(python, education, docker, experience, english))

    result = build_match_candidate_to_job().execute(_candidate(), criteria)

    assert result.total == 5
    assert result.matched_count == 3
    assert result.not_matched_count == 0
    assert result.unsupported_count == 2
    assert [match.status for match in result.matches] == [
        MatchStatus.MATCHED,
        MatchStatus.UNSUPPORTED,
        MatchStatus.MATCHED,
        MatchStatus.UNSUPPORTED,
        MatchStatus.MATCHED,
    ]
    assert all(
        match.criterion is criterion
        for match, criterion in zip(
            result.matches, criteria.criteria, strict=True
        )
    )


def test_builder_returns_independent_service_instances() -> None:
    service_a = build_match_candidate_to_job()
    service_b = build_match_candidate_to_job()

    assert service_a is not service_b


def test_builder_signature_and_type_hints() -> None:
    hints = get_type_hints(build_match_candidate_to_job)
    signature = inspect.signature(build_match_candidate_to_job)

    assert hints["return"] is MatchCandidateToJob
    assert signature.parameters == {}


def test_score_builder_returns_calculate_matching_score() -> None:
    service = build_calculate_matching_score()

    assert isinstance(service, CalculateMatchingScore)


def test_score_builder_processes_empty_matching_result() -> None:
    result = build_calculate_matching_score().execute(MatchingResult())

    assert result == MatchingScore(score=None, coverage=None)


def test_score_builder_returns_independent_service_instances() -> None:
    first = build_calculate_matching_score()
    second = build_calculate_matching_score()

    assert first is not second


def test_score_builder_signature_and_type_hints() -> None:
    hints = get_type_hints(build_calculate_matching_score)
    signature = inspect.signature(build_calculate_matching_score)

    assert hints["return"] is CalculateMatchingScore
    assert signature.parameters == {}


def test_match_and_score_builder_returns_pipeline_service() -> None:
    service = build_match_and_score_candidate_to_job()

    assert isinstance(service, MatchAndScoreCandidateToJob)


def test_match_and_score_builder_signature_and_type_hints() -> None:
    hints = get_type_hints(build_match_and_score_candidate_to_job)
    signature = inspect.signature(build_match_and_score_candidate_to_job)

    assert hints["return"] is MatchAndScoreCandidateToJob
    assert signature.parameters == {}


def test_match_and_score_builder_runs_real_pipeline() -> None:
    criterion = _criterion(CriterionCategory.TECHNOLOGY, "Python")

    matching_result, matching_score = build_match_and_score_candidate_to_job().execute(
        _candidate(), JobCriteria(criteria=(criterion,))
    )

    assert isinstance(matching_result, MatchingResult)
    assert isinstance(matching_score, MatchingScore)
    assert matching_result.total == 1
    assert matching_result.matched_count == 1
    assert matching_score.score == 1.0
    assert matching_score.coverage == 1.0


def test_match_and_score_builder_returns_independent_service_instances() -> None:
    first = build_match_and_score_candidate_to_job()
    second = build_match_and_score_candidate_to_job()

    assert first is not second
