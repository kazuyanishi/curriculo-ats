from dataclasses import FrozenInstanceError

import pytest

from resume_ai.core.exceptions import DomainError
from resume_ai.modules.jobs.domain.entities import (
    EducationRequirement,
    EducationRequirementStatus,
    EducationRequirementStatusEvidence,
)


def _evidence(
    status: EducationRequirementStatus = EducationRequirementStatus.COMPLETED,
    text: str = "completed degree",
) -> EducationRequirementStatusEvidence:
    return EducationRequirementStatusEvidence(status=status, evidence=text)


def test_status_evidence_accepts_enum_and_literal_text() -> None:
    item = _evidence(EducationRequirementStatus.IN_PROGRESS, "currently pursuing")

    assert item.status is EducationRequirementStatus.IN_PROGRESS
    assert item.evidence == "currently pursuing"


def test_status_evidence_is_frozen_and_slotted() -> None:
    item = _evidence()

    with pytest.raises(FrozenInstanceError):
        item.status = EducationRequirementStatus.IN_PROGRESS
    with pytest.raises(FrozenInstanceError):
        item.evidence = "other evidence"
    assert not hasattr(item, "__dict__")


@pytest.mark.parametrize("status", ["completed", "in_progress", None])
def test_status_evidence_rejects_non_enum_status(status: object) -> None:
    with pytest.raises(DomainError):
        EducationRequirementStatusEvidence(status=status, evidence="graduates")  # type: ignore[arg-type]


@pytest.mark.parametrize("evidence", ["", "   ", "\n\t", 42, None])
def test_status_evidence_rejects_invalid_evidence(evidence: object) -> None:
    with pytest.raises(DomainError):
        EducationRequirementStatusEvidence(
            status=EducationRequirementStatus.COMPLETED,
            evidence=evidence,  # type: ignore[arg-type]
        )


def test_status_evidence_preserves_text_exactly() -> None:
    item = _evidence(
        EducationRequirementStatus.IN_PROGRESS,
        "  currently pursuing  ",
    )

    assert item.evidence == "  currently pursuing  "


def test_education_requirement_accepts_status_evidence_for_accepted_status() -> None:
    item = _evidence()
    requirement = EducationRequirement(
        field_of_study="Computer Science",
        acceptable_statuses=(EducationRequirementStatus.COMPLETED,),
        status_evidence=(item,),
    )

    assert requirement.status_evidence == (item,)
    assert requirement.status_evidence[0] is item


def test_education_requirement_accepts_independent_evidence_for_both_statuses() -> None:
    completed = _evidence(EducationRequirementStatus.COMPLETED, "graduates")
    in_progress = _evidence(
        EducationRequirementStatus.IN_PROGRESS,
        "currently enrolled",
    )
    requirement = EducationRequirement(
        field_of_study="Computer Science",
        acceptable_statuses=(
            EducationRequirementStatus.COMPLETED,
            EducationRequirementStatus.IN_PROGRESS,
        ),
        status_evidence=(completed, in_progress),
    )

    assert requirement.status_evidence == (completed, in_progress)
    assert requirement.status_evidence[0] is completed
    assert requirement.status_evidence[1] is in_progress


def test_status_evidence_must_be_a_tuple() -> None:
    with pytest.raises(DomainError):
        EducationRequirement(
            acceptable_statuses=(EducationRequirementStatus.IN_PROGRESS,),
            status_evidence=[_evidence(EducationRequirementStatus.IN_PROGRESS)],  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "invalid_item",
    ["currently pursuing", None, EducationRequirementStatus.IN_PROGRESS],
)
def test_status_evidence_tuple_rejects_invalid_elements(invalid_item: object) -> None:
    with pytest.raises(DomainError):
        EducationRequirement(
            acceptable_statuses=(EducationRequirementStatus.IN_PROGRESS,),
            status_evidence=(invalid_item,),  # type: ignore[arg-type]
        )


def test_status_evidence_status_must_be_acceptable() -> None:
    with pytest.raises(DomainError, match="acceptable education status"):
        EducationRequirement(
            field_of_study="Computer Science",
            acceptable_statuses=(EducationRequirementStatus.COMPLETED,),
            status_evidence=(_evidence(EducationRequirementStatus.IN_PROGRESS),),
        )


def test_status_evidence_without_acceptable_status_is_rejected() -> None:
    with pytest.raises(DomainError):
        EducationRequirement(
            field_of_study="Computer Science",
            status_evidence=(_evidence(),),
        )


def test_acceptable_statuses_remain_compatible_without_evidence() -> None:
    requirement = EducationRequirement(
        acceptable_statuses=(EducationRequirementStatus.COMPLETED,),
    )

    assert requirement.status_evidence == ()


def test_textual_requirement_remains_compatible_without_evidence() -> None:
    requirement = EducationRequirement(field_of_study="Computer Science")

    assert requirement.status_evidence == ()
