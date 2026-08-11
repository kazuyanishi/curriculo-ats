from datetime import date

import pytest

from resume_ai.modules.candidate.domain.entities import (
    Activity,
    Candidate,
    Certification,
    ContactInfo,
    Experience,
    Language,
    PersonalInfo,
    ProficiencyLevel,
    Project,
    Skill,
    Technology,
    Tool,
)
from resume_ai.modules.jobs.domain.entities import (
    CriterionCategory,
    CriterionImportance,
    JobCriterion,
)
from resume_ai.modules.matching.application.ports import CandidateCriterionMatcher
from resume_ai.modules.matching.domain.entities import CriterionMatch, MatchStatus
from resume_ai.modules.matching.domain.services import ExactCandidateCriterionMatcher


def _candidate(
    *,
    skills: tuple[Skill, ...] = (),
    technologies: tuple[Technology, ...] = (),
    tools: tuple[Tool, ...] = (),
    languages: tuple[Language, ...] = (),
    certifications: tuple[Certification, ...] = (),
    experiences: tuple[Experience, ...] = (),
    projects: tuple[Project, ...] = (),
) -> Candidate:
    return Candidate(
        personal_info=PersonalInfo(
            full_name="Jane Doe",
            city="Curitiba",
            state="PR",
            country="Brazil",
        ),
        contact_info=ContactInfo(email="jane@example.com", phone="+55"),
        skills=skills,
        technologies=technologies,
        tools=tools,
        languages=languages,
        certifications=certifications,
        experiences=experiences,
        projects=projects,
    )


def _criterion(category: CriterionCategory, value: str) -> JobCriterion:
    return JobCriterion(
        category=category,
        value=value,
        evidence=f"{value} is required.",
        importance=CriterionImportance.REQUIRED,
    )


def test_technology_matches_case_insensitively_and_ignores_outer_whitespace() -> None:
    candidate = _candidate(technologies=(Technology("Python"),))
    criterion = _criterion(CriterionCategory.TECHNOLOGY, "  PYTHON  ")

    result = ExactCandidateCriterionMatcher().match(candidate, criterion)

    assert result.status is MatchStatus.MATCHED
    assert result.criterion is criterion


def test_real_difference_does_not_match_without_aliases() -> None:
    candidate = _candidate(technologies=(Technology("PostgreSQL"),))
    criterion = _criterion(CriterionCategory.TECHNOLOGY, "Postgres")

    result = ExactCandidateCriterionMatcher().match(candidate, criterion)

    assert result.status is MatchStatus.NOT_MATCHED
    assert result.criterion is criterion


@pytest.mark.parametrize(
    ("category", "candidate_item"),
    [
        (CriterionCategory.SKILL, Skill("Communication")),
        (CriterionCategory.TECHNOLOGY, Technology("Python")),
        (CriterionCategory.TOOL, Tool("Docker")),
        (CriterionCategory.LANGUAGE, Language("English")),
        (CriterionCategory.CERTIFICATION, Certification("AWS Certified Developer", "AWS")),
    ],
)
def test_supported_categories_use_their_direct_collection(
    category: CriterionCategory,
    candidate_item: object,
) -> None:
    collections = {
        CriterionCategory.SKILL: ("skills",),
        CriterionCategory.TECHNOLOGY: ("technologies",),
        CriterionCategory.TOOL: ("tools",),
        CriterionCategory.LANGUAGE: ("languages",),
        CriterionCategory.CERTIFICATION: ("certifications",),
    }
    candidate = _candidate(**{collections[category][0]: (candidate_item,)})
    criterion = _criterion(category, candidate_item.name)  # type: ignore[union-attr]

    result = ExactCandidateCriterionMatcher().match(candidate, criterion)

    assert result.status is MatchStatus.MATCHED


@pytest.mark.parametrize(
    "category",
    [
        CriterionCategory.SKILL,
        CriterionCategory.TECHNOLOGY,
        CriterionCategory.TOOL,
        CriterionCategory.LANGUAGE,
        CriterionCategory.CERTIFICATION,
    ],
)
def test_supported_category_without_a_name_is_not_matched(category: CriterionCategory) -> None:
    result = ExactCandidateCriterionMatcher().match(
        _candidate(), _criterion(category, "Python")
    )

    assert result.status is MatchStatus.NOT_MATCHED


def test_categories_are_isolated() -> None:
    candidate = _candidate(technologies=(Technology("Python"),))
    criterion = _criterion(CriterionCategory.SKILL, "Python")

    result = ExactCandidateCriterionMatcher().match(candidate, criterion)

    assert result.status is MatchStatus.NOT_MATCHED


@pytest.mark.parametrize(
    "category",
    [CriterionCategory.EDUCATION, CriterionCategory.EXPERIENCE, CriterionCategory.OTHER],
)
def test_unsupported_categories_return_unsupported_status(category: CriterionCategory) -> None:
    criterion = _criterion(category, "Example")

    result = ExactCandidateCriterionMatcher().match(_candidate(), criterion)

    assert result.status is MatchStatus.UNSUPPORTED
    assert result.criterion is criterion


def test_project_technologies_are_not_consulted() -> None:
    candidate = _candidate(
        technologies=(),
        projects=(
            Project(
                name="Backend API",
                description="Example project",
                technologies=("Python",),
            ),
        ),
    )
    criterion = _criterion(CriterionCategory.TECHNOLOGY, "Python")

    result = ExactCandidateCriterionMatcher().match(candidate, criterion)

    assert result.status is MatchStatus.NOT_MATCHED


def test_experience_text_is_not_consulted() -> None:
    candidate = _candidate(
        technologies=(),
        experiences=(
            Experience(
                company="Example Systems",
                role="Backend Developer",
                start_date=date(2024, 1, 1),
                activities=(Activity("Developed APIs using Python and FastAPI"),),
            ),
        ),
    )
    criterion = _criterion(CriterionCategory.TECHNOLOGY, "Python")

    result = ExactCandidateCriterionMatcher().match(candidate, criterion)

    assert result.status is MatchStatus.NOT_MATCHED


def test_candidate_item_levels_do_not_affect_matching() -> None:
    candidate = _candidate(
        technologies=(Technology("Python", level=ProficiencyLevel.BASIC),)
    )
    criterion = _criterion(CriterionCategory.TECHNOLOGY, "Python")

    result = ExactCandidateCriterionMatcher().match(candidate, criterion)

    assert result.status is MatchStatus.MATCHED


def test_importance_and_evidence_do_not_affect_matching() -> None:
    candidate = _candidate(tools=(Tool("Docker"),))
    criterion = JobCriterion(
        category=CriterionCategory.TOOL,
        value="Docker",
        evidence="An unrelated evidence.",
        importance=CriterionImportance.PREFERRED,
    )

    result = ExactCandidateCriterionMatcher().match(candidate, criterion)

    assert result.status is MatchStatus.MATCHED


def test_matcher_is_structurally_compatible_with_the_port() -> None:
    def _match(
        matcher: CandidateCriterionMatcher,
        candidate: Candidate,
        criterion: JobCriterion,
    ) -> CriterionMatch:
        return matcher.match(candidate, criterion)

    criterion = _criterion(CriterionCategory.TECHNOLOGY, "Python")
    result = _match(
        ExactCandidateCriterionMatcher(),
        _candidate(technologies=(Technology("Python"),)),
        criterion,
    )

    assert result.criterion is criterion
    assert result.status is MatchStatus.MATCHED
