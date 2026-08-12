from datetime import date
from typing import get_type_hints

import pytest

from resume_ai.modules.candidate.domain.entities import (
    Candidate,
    ContactInfo,
    Education,
    EducationStatus,
    PersonalInfo,
)
from resume_ai.modules.jobs.domain.entities import (
    CriterionCategory,
    CriterionImportance,
    EducationRequirement,
    EducationRequirementStatus,
    EducationRequirementStatusEvidence,
    JobCriterion,
)
from resume_ai.modules.matching.domain.entities import CriterionMatch, MatchStatus
from resume_ai.modules.matching.domain.services import EducationCandidateCriterionMatcher


def _candidate(*education: Education) -> Candidate:
    return Candidate(
        personal_info=PersonalInfo("Jane Doe", "Curitiba", "PR", "Brazil"),
        contact_info=ContactInfo("jane@example.com", "+55"),
        education=education,
    )


def _criterion(
    requirement: EducationRequirement | None,
    *,
    category: CriterionCategory = CriterionCategory.EDUCATION,
    value: str = "ignored value",
    evidence: str = "ignored evidence",
    importance: CriterionImportance = CriterionImportance.REQUIRED,
) -> JobCriterion:
    return JobCriterion(
        category=category,
        value=value,
        evidence=evidence,
        importance=importance,
        education_requirement=requirement,
    )


def _education(
    course: str = "Computer Science",
    institution: str = "Example University",
    status: EducationStatus = EducationStatus.COMPLETED,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
) -> Education:
    return Education(
        institution=institution,
        course=course,
        status=status,
        start_date=start_date,
        end_date=end_date,
    )


def test_non_education_is_unsupported() -> None:
    result = EducationCandidateCriterionMatcher().match(
        _candidate(_education()), _criterion(None, category=CriterionCategory.TECHNOLOGY)
    )
    assert result.status is MatchStatus.UNSUPPORTED


@pytest.mark.parametrize(
    "requirement",
    [
        None,
        EducationRequirement(degree_level="Bachelor's", field_of_study="Computer Science"),
        EducationRequirement(
            degree_level="Bachelor's",
            field_of_study="Computer Science",
            institution="Example University",
        ),
        EducationRequirement(acceptable_statuses=(EducationRequirementStatus.COMPLETED,)),
    ],
)
def test_unsupported_education_requirements(requirement: EducationRequirement | None) -> None:
    result = EducationCandidateCriterionMatcher().match(
        _candidate(_education()), _criterion(requirement)
    )
    assert result.status is MatchStatus.UNSUPPORTED


def test_field_matches_case_insensitively_and_ignores_outer_whitespace() -> None:
    result = EducationCandidateCriterionMatcher().match(
        _candidate(_education(course="computer science")),
        _criterion(EducationRequirement(field_of_study=" Computer Science ")),
    )
    assert result.status is MatchStatus.MATCHED


def test_field_mismatch_is_not_matched() -> None:
    result = EducationCandidateCriterionMatcher().match(
        _candidate(_education(course="Information Systems")),
        _criterion(EducationRequirement(field_of_study="Computer Science")),
    )
    assert result.status is MatchStatus.NOT_MATCHED


def test_field_does_not_use_substring_or_aliases() -> None:
    for course in ("Computer Science", "Computing", "Computer Sciences"):
        result = EducationCandidateCriterionMatcher().match(
            _candidate(_education(course=course)),
            _criterion(EducationRequirement(field_of_study="Science")),
        )
        assert result.status is MatchStatus.NOT_MATCHED


def test_institution_matches_and_alias_does_not() -> None:
    matched = EducationCandidateCriterionMatcher().match(
        _candidate(_education(institution=" example university ")),
        _criterion(EducationRequirement(institution="Example University")),
    )
    not_matched = EducationCandidateCriterionMatcher().match(
        _candidate(_education(institution="UFPR")),
        _criterion(EducationRequirement(institution="Universidade Federal do Paraná")),
    )
    assert matched.status is MatchStatus.MATCHED
    assert not_matched.status is MatchStatus.NOT_MATCHED


def test_field_and_institution_must_match_the_same_record() -> None:
    requirement = EducationRequirement(
        field_of_study="Computer Science", institution="University B"
    )
    result = EducationCandidateCriterionMatcher().match(
        _candidate(
            _education(course="Computer Science", institution="University A"),
            _education(course="Business", institution="University B"),
        ),
        _criterion(requirement),
    )
    assert result.status is MatchStatus.NOT_MATCHED


def test_one_complete_record_is_enough() -> None:
    requirement = EducationRequirement(
        field_of_study="Computer Science", institution="Example University"
    )
    result = EducationCandidateCriterionMatcher().match(
        _candidate(
            _education(course="Business", institution="Other University"), _education()
        ),
        _criterion(requirement),
    )
    assert result.status is MatchStatus.MATCHED


def test_field_and_in_progress_status_match() -> None:
    requirement = EducationRequirement(
        field_of_study="Computer Science",
        acceptable_statuses=(EducationRequirementStatus.IN_PROGRESS,),
    )
    result = EducationCandidateCriterionMatcher().match(
        _candidate(_education(status=EducationStatus.IN_PROGRESS)),
        _criterion(requirement),
    )
    assert result.status is MatchStatus.MATCHED


def test_wrong_or_interrupted_status_is_not_matched() -> None:
    requirement = EducationRequirement(
        field_of_study="Computer Science",
        acceptable_statuses=(EducationRequirementStatus.IN_PROGRESS,),
    )
    for status in (EducationStatus.COMPLETED, EducationStatus.INTERRUPTED):
        result = EducationCandidateCriterionMatcher().match(
            _candidate(_education(status=status)), _criterion(requirement)
        )
        assert result.status is MatchStatus.NOT_MATCHED


def test_empty_status_requirement_ignores_candidate_status() -> None:
    result = EducationCandidateCriterionMatcher().match(
        _candidate(_education(status=EducationStatus.INTERRUPTED)),
        _criterion(EducationRequirement(field_of_study="Computer Science")),
    )
    assert result.status is MatchStatus.MATCHED


def test_institution_and_status_match() -> None:
    requirement = EducationRequirement(
        institution="Example University",
        acceptable_statuses=(EducationRequirementStatus.COMPLETED,),
    )
    result = EducationCandidateCriterionMatcher().match(
        _candidate(_education()), _criterion(requirement)
    )
    assert result.status is MatchStatus.MATCHED


def test_field_institution_and_status_match_or_fail_as_one_record() -> None:
    requirement = EducationRequirement(
        field_of_study="Computer Science",
        institution="Example University",
        acceptable_statuses=(EducationRequirementStatus.COMPLETED,),
    )
    matched = EducationCandidateCriterionMatcher().match(
        _candidate(_education()), _criterion(requirement)
    )
    not_matched = EducationCandidateCriterionMatcher().match(
        _candidate(_education(status=EducationStatus.IN_PROGRESS)),
        _criterion(requirement),
    )
    assert matched.status is MatchStatus.MATCHED
    assert not_matched.status is MatchStatus.NOT_MATCHED


def test_multiple_acceptable_statuses_are_or() -> None:
    requirement = EducationRequirement(
        field_of_study="Computer Science",
        acceptable_statuses=(
            EducationRequirementStatus.COMPLETED,
            EducationRequirementStatus.IN_PROGRESS,
        ),
    )
    for status in (EducationStatus.COMPLETED, EducationStatus.IN_PROGRESS):
        result = EducationCandidateCriterionMatcher().match(
            _candidate(_education(status=status)), _criterion(requirement)
        )
        assert result.status is MatchStatus.MATCHED


def test_empty_candidate_education_is_not_matched() -> None:
    result = EducationCandidateCriterionMatcher().match(
        _candidate(), _criterion(EducationRequirement(field_of_study="Computer Science"))
    )
    assert result.status is MatchStatus.NOT_MATCHED


def test_provenance_value_evidence_importance_and_dates_do_not_affect_matching() -> None:
    result = EducationCandidateCriterionMatcher().match(
        _candidate(
            _education(start_date=date(2018, 1, 1), end_date=date(2022, 1, 1))
        ),
        _criterion(
            EducationRequirement(field_of_study="Computer Science"),
            value="completely different",
            evidence="not candidate data",
            importance=CriterionImportance.PREFERRED,
        ),
    )
    assert result.status is MatchStatus.MATCHED


def test_status_evidence_text_does_not_affect_education_matching() -> None:
    requirement = EducationRequirement(
        field_of_study="Computer Science",
        acceptable_statuses=(EducationRequirementStatus.IN_PROGRESS,),
        status_evidence=(
            EducationRequirementStatusEvidence(
                status=EducationRequirementStatus.IN_PROGRESS,
                evidence="currently pursuing",
            ),
        ),
    )
    criterion = _criterion(requirement)

    result = EducationCandidateCriterionMatcher().match(
        _candidate(
            _education(
                course="Computer Science",
                institution="Example University",
                status=EducationStatus.IN_PROGRESS,
            )
        ),
        criterion,
    )

    assert result.status is MatchStatus.MATCHED
    assert result.criterion is criterion


def test_status_evidence_text_does_not_mask_incompatible_candidate_status() -> None:
    requirement = EducationRequirement(
        field_of_study="Computer Science",
        acceptable_statuses=(EducationRequirementStatus.IN_PROGRESS,),
        status_evidence=(
            EducationRequirementStatusEvidence(
                status=EducationRequirementStatus.IN_PROGRESS,
                evidence="currently pursuing",
            ),
        ),
    )

    result = EducationCandidateCriterionMatcher().match(
        _candidate(
            _education(
                course="Computer Science",
                institution="Example University",
                status=EducationStatus.COMPLETED,
            )
        ),
        _criterion(requirement),
    )

    assert result.status is MatchStatus.NOT_MATCHED


def test_result_preserves_criterion_identity() -> None:
    criterion = _criterion(EducationRequirement(field_of_study="Computer Science"))
    result = EducationCandidateCriterionMatcher().match(_candidate(_education()), criterion)
    assert result.criterion is criterion


def test_type_hints() -> None:
    hints = get_type_hints(EducationCandidateCriterionMatcher.match)
    assert hints["candidate"] is Candidate
    assert hints["criterion"] is JobCriterion
    assert hints["return"] is CriterionMatch
