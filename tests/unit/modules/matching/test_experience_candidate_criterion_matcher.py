from datetime import date
from typing import get_type_hints

import pytest

from resume_ai.modules.candidate.domain.entities import (
    Achievement,
    Activity,
    Candidate,
    ContactInfo,
    Experience,
    PersonalInfo,
)
from resume_ai.modules.jobs.domain.entities import (
    CriterionCategory,
    CriterionImportance,
    ExperienceDurationUnit,
    ExperienceMinimumDuration,
    ExperienceRequirement,
    JobCriterion,
)
from resume_ai.modules.matching.domain.entities import CriterionMatch, MatchStatus
from resume_ai.modules.matching.domain.services import (
    ExactCandidateCriterionMatcher,
    ExperienceCandidateCriterionMatcher,
    complete_calendar_months,
)


def _candidate(*experiences: Experience) -> Candidate:
    return Candidate(
        personal_info=PersonalInfo("Jane Doe", "Curitiba", "PR", "Brazil"),
        contact_info=ContactInfo("jane@example.com", "+55"),
        experiences=experiences,
    )


def _experience(
    role: str = "Backend Developer",
    company: str = "Example Corp",
    *,
    start_date: date = date(2020, 1, 1),
    end_date: date | None = date(2023, 1, 1),
    activities: tuple[Activity, ...] = (),
    achievements: tuple[Achievement, ...] = (),
) -> Experience:
    return Experience(
        role=role,
        company=company,
        start_date=start_date,
        end_date=end_date,
        activities=activities,
        achievements=achievements,
    )


def _criterion(
    requirement: ExperienceRequirement | None = None,
    *,
    category: CriterionCategory = CriterionCategory.EXPERIENCE,
) -> JobCriterion:
    return JobCriterion(
        category=category,
        value="unrelated value",
        evidence="unrelated evidence",
        importance=CriterionImportance.PREFERRED,
        experience_requirement=requirement,
    )


@pytest.mark.parametrize(
    "criterion",
    [
        _criterion(category=CriterionCategory.SKILL),
        _criterion(),
    ],
)
def test_unsupported_category_or_missing_requirement_is_unsupported(
    criterion: JobCriterion,
) -> None:
    result = ExperienceCandidateCriterionMatcher().match(_candidate(_experience()), criterion)

    assert result.status is MatchStatus.UNSUPPORTED


def test_complete_calendar_months_counts_full_years() -> None:
    assert complete_calendar_months(date(2020, 1, 1), date(2023, 1, 1)) == 36


def test_complete_calendar_months_excludes_partial_month() -> None:
    assert complete_calendar_months(date(2020, 1, 15), date(2023, 1, 14)) == 35


def test_complete_calendar_months_returns_zero_for_same_date() -> None:
    same_date = date(2020, 1, 1)

    assert complete_calendar_months(same_date, same_date) == 0


def test_years_duration_matches_exact_calendar_months() -> None:
    requirement = ExperienceRequirement(
        role="Backend Developer",
        minimum_duration=ExperienceMinimumDuration(3, ExperienceDurationUnit.YEARS),
        minimum_duration_evidence="3 years",
    )

    result = ExperienceCandidateCriterionMatcher().match(
        _candidate(_experience()), _criterion(requirement)
    )

    assert result.status is MatchStatus.MATCHED


def test_years_duration_does_not_match_partial_year() -> None:
    requirement = ExperienceRequirement(
        role="Backend Developer",
        minimum_duration=ExperienceMinimumDuration(3, ExperienceDurationUnit.YEARS),
        minimum_duration_evidence="3 years",
    )
    experience = _experience(end_date=date(2022, 12, 31))

    result = ExperienceCandidateCriterionMatcher().match(
        _candidate(experience), _criterion(requirement)
    )

    assert result.status is MatchStatus.NOT_MATCHED


def test_months_duration_matches_exact_months() -> None:
    requirement = ExperienceRequirement(
        role="Backend Developer",
        minimum_duration=ExperienceMinimumDuration(3, ExperienceDurationUnit.MONTHS),
        minimum_duration_evidence="3 months",
    )

    result = ExperienceCandidateCriterionMatcher().match(
        _candidate(_experience(end_date=date(2020, 4, 1))), _criterion(requirement)
    )

    assert result.status is MatchStatus.MATCHED


def test_partial_month_does_not_count_for_duration() -> None:
    requirement = ExperienceRequirement(
        role="Backend Developer",
        minimum_duration=ExperienceMinimumDuration(3, ExperienceDurationUnit.MONTHS),
        minimum_duration_evidence="3 months",
    )

    result = ExperienceCandidateCriterionMatcher().match(
        _candidate(_experience(end_date=date(2020, 3, 31))), _criterion(requirement)
    )

    assert result.status is MatchStatus.NOT_MATCHED


def test_relevant_open_experience_is_unsupported_for_duration() -> None:
    requirement = ExperienceRequirement(
        role="Backend Developer",
        minimum_duration=ExperienceMinimumDuration(3, ExperienceDurationUnit.YEARS),
        minimum_duration_evidence="3 years",
    )

    result = ExperienceCandidateCriterionMatcher().match(
        _candidate(_experience(end_date=None)), _criterion(requirement)
    )

    assert result.status is MatchStatus.UNSUPPORTED


def test_no_relevant_experience_is_not_matched_for_duration() -> None:
    requirement = ExperienceRequirement(
        role="Backend Developer",
        minimum_duration=ExperienceMinimumDuration(3, ExperienceDurationUnit.YEARS),
        minimum_duration_evidence="3 years",
    )

    result = ExperienceCandidateCriterionMatcher().match(
        _candidate(_experience(role="Support Analyst")), _criterion(requirement)
    )

    assert result.status is MatchStatus.NOT_MATCHED


def test_multiple_relevant_experiences_are_unsupported_for_duration() -> None:
    requirement = ExperienceRequirement(
        role="Backend Developer",
        minimum_duration=ExperienceMinimumDuration(3, ExperienceDurationUnit.YEARS),
        minimum_duration_evidence="3 years",
    )

    result = ExperienceCandidateCriterionMatcher().match(
        _candidate(_experience(), _experience()), _criterion(requirement)
    )

    assert result.status is MatchStatus.UNSUPPORTED


def test_role_and_duration_must_match_same_experience() -> None:
    requirement = ExperienceRequirement(
        role="Backend Developer",
        minimum_duration=ExperienceMinimumDuration(3, ExperienceDurationUnit.YEARS),
        minimum_duration_evidence="3 years",
    )
    candidate = _candidate(
        _experience(end_date=date(2022, 1, 1)),
        _experience(role="Support Analyst", end_date=date(2024, 1, 1)),
    )

    result = ExperienceCandidateCriterionMatcher().match(candidate, _criterion(requirement))

    assert result.status is MatchStatus.NOT_MATCHED


def test_company_and_duration_use_same_experience() -> None:
    requirement = ExperienceRequirement(
        company="Example Corp",
        minimum_duration=ExperienceMinimumDuration(3, ExperienceDurationUnit.YEARS),
        minimum_duration_evidence="3 years",
    )
    candidate = _candidate(
        _experience(company="Example Corp", end_date=date(2022, 1, 1)),
        _experience(company="Other Corp", end_date=date(2024, 1, 1)),
    )

    result = ExperienceCandidateCriterionMatcher().match(candidate, _criterion(requirement))

    assert result.status is MatchStatus.NOT_MATCHED


def test_role_matches_with_strip_casefold() -> None:
    result = ExperienceCandidateCriterionMatcher().match(
        _candidate(_experience(role="  backend developer  ")),
        _criterion(ExperienceRequirement(role=" BACKEND DEVELOPER ")),
    )

    assert result.status is MatchStatus.MATCHED


@pytest.mark.parametrize("role", ["Backend", "Software Engineer"])
def test_role_requires_exact_normalized_equality_without_aliases_or_substrings(
    role: str,
) -> None:
    result = ExperienceCandidateCriterionMatcher().match(
        _candidate(_experience(role="Backend Developer")),
        _criterion(ExperienceRequirement(role=role)),
    )

    assert result.status is MatchStatus.NOT_MATCHED


def test_company_matches_with_strip_casefold() -> None:
    result = ExperienceCandidateCriterionMatcher().match(
        _candidate(_experience(company="  example corp  ")),
        _criterion(ExperienceRequirement(company=" EXAMPLE CORP ")),
    )

    assert result.status is MatchStatus.MATCHED


def test_different_company_is_not_matched() -> None:
    result = ExperienceCandidateCriterionMatcher().match(
        _candidate(_experience(company="Other Corp")),
        _criterion(ExperienceRequirement(company="Example Corp")),
    )

    assert result.status is MatchStatus.NOT_MATCHED


def test_role_and_company_must_match_on_the_same_experience() -> None:
    candidate = _candidate(
        _experience(role="Backend Developer", company="Other Corp"),
        _experience(role="Support Analyst", company="Example Corp"),
    )

    result = ExperienceCandidateCriterionMatcher().match(
        candidate,
        _criterion(
            ExperienceRequirement(role="Backend Developer", company="Example Corp")
        ),
    )

    assert result.status is MatchStatus.NOT_MATCHED


def test_one_complete_experience_matches_among_many() -> None:
    candidate = _candidate(
        _experience(role="Support Analyst", company="Other Corp"),
        _experience(role="Backend Developer", company="Example Corp"),
    )

    result = ExperienceCandidateCriterionMatcher().match(
        candidate,
        _criterion(
            ExperienceRequirement(role="Backend Developer", company="Example Corp")
        ),
    )

    assert result.status is MatchStatus.MATCHED


def test_evaluable_requirement_with_empty_experiences_is_not_matched() -> None:
    result = ExperienceCandidateCriterionMatcher().match(
        _candidate(), _criterion(ExperienceRequirement(role="Backend Developer"))
    )

    assert result.status is MatchStatus.NOT_MATCHED


def test_dates_activities_and_achievements_do_not_affect_matching() -> None:
    result = ExperienceCandidateCriterionMatcher().match(
        _candidate(
            _experience(
                start_date=date(2025, 1, 1),
                end_date=None,
                activities=(Activity("Different role text"),),
                achievements=(Achievement("Different company text"),),
            )
        ),
        _criterion(ExperienceRequirement(role="Backend Developer", company="Example Corp")),
    )

    assert result.status is MatchStatus.MATCHED


def test_match_preserves_original_criterion() -> None:
    criterion = _criterion(ExperienceRequirement(role="Backend Developer"))

    result = ExperienceCandidateCriterionMatcher().match(
        _candidate(_experience()), criterion
    )

    assert isinstance(result, CriterionMatch)
    assert result.criterion is criterion


def test_experience_matcher_type_hints() -> None:
    hints = get_type_hints(ExperienceCandidateCriterionMatcher.match)

    assert hints["candidate"] is Candidate
    assert hints["criterion"] is JobCriterion
    assert hints["return"] is CriterionMatch


def test_exact_matcher_delegates_evaluable_experience() -> None:
    criterion = _criterion(ExperienceRequirement(role="Backend Developer"))

    result = ExactCandidateCriterionMatcher().match(_candidate(_experience()), criterion)

    assert result.status is MatchStatus.MATCHED


def test_exact_matcher_delegates_supported_duration() -> None:
    criterion = _criterion(
        ExperienceRequirement(
            role="Backend Developer",
            minimum_duration=ExperienceMinimumDuration(
                3, ExperienceDurationUnit.YEARS
            ),
            minimum_duration_evidence="3 years",
        )
    )

    result = ExactCandidateCriterionMatcher().match(_candidate(_experience()), criterion)

    assert result.status is MatchStatus.MATCHED
