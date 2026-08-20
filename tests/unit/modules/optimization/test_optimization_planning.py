import inspect

import pytest

from resume_ai.core.exceptions import DomainError
from resume_ai.modules.candidate.domain.entities import (
    Achievement,
    Activity,
    Candidate,
    ContactInfo,
    Education,
    EducationStatus,
    Experience,
    PersonalInfo,
    Technology,
)
from resume_ai.modules.candidate.domain.value_objects import YearMonth
from resume_ai.modules.jobs.domain.entities import CriterionCategory, JobCriterion
from resume_ai.modules.matching.application.provenance import (
    MatchingProvenanceError,
    MatchingProvenanceGate,
)
from resume_ai.modules.matching.domain.entities import CriterionMatch, MatchingResult, MatchStatus
from resume_ai.modules.optimization.application.planning import (
    BuildCandidateOptimizationPlan,
    CandidateOptimizationPlan,
    ExperienceOptimizationContext,
    StandaloneOptimizationContext,
)


def candidate() -> Candidate:
    experiences = tuple(
        Experience(
            f"Example {index}",
            "Support Analyst",
            YearMonth("2020-01"),
            YearMonth("2024-01"),
            activities=(
                Activity(
                    "Controle e organização de demandas no Jira, com triagem e direcionamento."
                ),
                Activity(
                    "Atendimento e acompanhamento de chamados por telefone, e-mail e service desk."
                ),
            ),
            achievements=(Achievement("Redução de tempo de atendimento."),),
        )
        for index in range(3)
    )
    return Candidate(
        personal_info=PersonalInfo("Jane Doe", "Curitiba", "PR", "Brazil"),
        contact_info=ContactInfo("jane@example.test", "+55"),
        experiences=experiences,
        education=(Education("Example University", "Computer Science", EducationStatus.COMPLETED),),
        technologies=(Technology("PostgreSQL"), Technology("Docker"), Technology("Python")),
    )


def match(status: MatchStatus, *paths: str) -> CriterionMatch:
    criterion = JobCriterion(CriterionCategory.OTHER, "criterion", "criterion")
    return CriterionMatch(criterion, status, paths)


def planner() -> BuildCandidateOptimizationPlan:
    return BuildCandidateOptimizationPlan(MatchingProvenanceGate())


def test_single_experience_match_builds_one_context() -> None:
    path = "experiences[0].activities[0].description"

    plan = planner().execute(candidate(), MatchingResult((match(MatchStatus.MATCHED, path),)))

    assert plan == CandidateOptimizationPlan(
        experience_contexts=(ExperienceOptimizationContext(0, (0,), (path,)),),
    )


def test_matches_for_same_experience_share_context_and_preserve_jira_chamados_order() -> None:
    paths = (
        "experiences[0].activities[0].description",
        "experiences[0].activities[1].description",
    )
    matching = MatchingResult(
        (match(MatchStatus.MATCHED, paths[0]), match(MatchStatus.MATCHED, paths[1]))
    )

    plan = planner().execute(candidate(), matching)

    assert plan.experience_contexts == (ExperienceOptimizationContext(0, (0, 1), paths),)


def test_duplicate_paths_are_deduplicated_without_losing_match_indexes() -> None:
    path = "experiences[0].activities[0].description"

    plan = planner().execute(
        candidate(),
        MatchingResult((match(MatchStatus.MATCHED, path), match(MatchStatus.MATCHED, path))),
    )

    assert plan.experience_contexts == (ExperienceOptimizationContext(0, (0, 1), (path,)),)


def test_multi_experience_and_experience_technology_matches_stay_standalone() -> None:
    first = "experiences[0].activities[0].description"
    second = "experiences[1].activities[0].description"
    technology = "technologies[2].name"

    plan = planner().execute(
        candidate(),
        MatchingResult(
            (
                match(MatchStatus.MATCHED, first, second),
                match(MatchStatus.MATCHED, first, technology),
            )
        ),
    )

    assert plan.experience_contexts == ()
    assert plan.standalone_contexts == (
        StandaloneOptimizationContext(0, (first, second)),
        StandaloneOptimizationContext(1, (first, technology)),
    )


@pytest.mark.parametrize(
    ("paths", "is_experience_context"),
    [
        (("experiences[0].activities[0].description",), True),
        (
            (
                "experiences[0].activities[0].description",
                "experiences[0].activities[1].description",
            ),
            True,
        ),
        (("experiences[0].role",), False),
        (("experiences[0].achievements[0].description",), False),
        (("experiences[0].activities[0].description", "experiences[0].role"), False),
        (
            (
                "experiences[0].activities[0].description",
                "experiences[1].activities[0].description",
            ),
            False,
        ),
    ],
)
def test_only_activity_description_paths_build_experience_contexts(
    paths: tuple[str, ...],
    is_experience_context: bool,
) -> None:
    plan = planner().execute(candidate(), MatchingResult((match(MatchStatus.MATCHED, *paths),)))

    if is_experience_context:
        assert plan.experience_contexts[0].evidence_paths == paths
        assert plan.standalone_contexts == ()
    else:
        assert plan.experience_contexts == ()
        assert plan.standalone_contexts == (StandaloneOptimizationContext(0, paths),)


def test_technology_and_education_matches_stay_standalone() -> None:
    plan = planner().execute(
        candidate(),
        MatchingResult(
            (
                match(MatchStatus.MATCHED, "technologies[2].name"),
                match(MatchStatus.MATCHED, "education[0].course", "education[0].status"),
            )
        ),
    )

    assert plan.standalone_contexts == (
        StandaloneOptimizationContext(0, ("technologies[2].name",)),
        StandaloneOptimizationContext(1, ("education[0].course", "education[0].status")),
    )


def test_non_matches_are_ignored_and_zero_matched_is_valid() -> None:
    plan = planner().execute(
        candidate(),
        MatchingResult(
            (
                match(MatchStatus.NOT_MATCHED),
                match(MatchStatus.UNSUPPORTED),
            )
        ),
    )

    assert plan == CandidateOptimizationPlan()


def test_experience_contexts_follow_first_matching_occurrence() -> None:
    matching = MatchingResult(
        (
            match(MatchStatus.MATCHED, "experiences[2].activities[0].description"),
            match(MatchStatus.MATCHED, "experiences[0].activities[0].description"),
            match(MatchStatus.MATCHED, "experiences[2].activities[1].description"),
            match(MatchStatus.MATCHED, "experiences[1].activities[0].description"),
        )
    )

    plan = planner().execute(candidate(), matching)

    assert [context.experience_index for context in plan.experience_contexts] == [2, 0, 1]
    assert plan.experience_contexts[0].match_indexes == (0, 2)


@pytest.mark.parametrize(
    "matching",
    [
        MatchingResult((match(MatchStatus.MATCHED),)),
        MatchingResult((match(MatchStatus.MATCHED, "projects[999].description"),)),
        MatchingResult((match(MatchStatus.NOT_MATCHED, "technologies[2].name"),)),
    ],
)
def test_invalid_provenance_is_rejected_before_planning(matching: MatchingResult) -> None:
    with pytest.raises(MatchingProvenanceError):
        planner().execute(candidate(), matching)


def test_planner_preserves_candidate_and_matching_immutably() -> None:
    subject = candidate()
    matching = MatchingResult(
        (match(MatchStatus.MATCHED, "experiences[0].activities[0].description"),)
    )
    candidate_before = subject
    matching_before = matching

    planner().execute(subject, matching)

    assert subject == candidate_before
    assert matching == matching_before


def test_plan_contexts_validate_basic_invariants_and_planner_has_no_ai_dependency() -> None:
    with pytest.raises(DomainError):
        ExperienceOptimizationContext(-1, (0,), ("experiences[0].role",))
    with pytest.raises(DomainError):
        StandaloneOptimizationContext(0, ("technologies[0].name",) * 2)

    parameters = inspect.signature(BuildCandidateOptimizationPlan.__init__).parameters
    assert tuple(parameters) == ("self", "provenance_gate")
