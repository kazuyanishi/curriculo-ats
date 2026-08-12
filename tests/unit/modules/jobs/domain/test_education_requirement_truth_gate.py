from typing import get_type_hints

import pytest

from resume_ai.core.exceptions import DomainError
from resume_ai.modules.jobs.domain.entities import (
    CriterionCategory,
    EducationRequirement,
    EducationRequirementStatus,
    EducationRequirementStatusEvidence,
    JobCriterion,
)
from resume_ai.modules.jobs.domain.services import EducationRequirementTruthGate


def _criterion(
    evidence: str,
    requirement: EducationRequirement | None = None,
    *,
    category: CriterionCategory = CriterionCategory.EDUCATION,
) -> JobCriterion:
    return JobCriterion(
        category=category,
        value="education criterion",
        evidence=evidence,
        education_requirement=requirement,
    )


def test_gate_is_noop_without_education_requirement() -> None:
    assert EducationRequirementTruthGate().validate(_criterion("Python")) is None
    assert (
        EducationRequirementTruthGate().validate(
            _criterion("Python", category=CriterionCategory.TECHNOLOGY)
        )
        is None
    )


def test_gate_accepts_education_without_structured_requirement() -> None:
    assert EducationRequirementTruthGate().validate(_criterion("Degree required.")) is None


def test_gate_accepts_all_grounded_textual_fields() -> None:
    evidence = "Bachelor's degree in Computer Science from Example University required."
    requirement = EducationRequirement(
        degree_level="Bachelor's",
        field_of_study="Computer Science",
        institution="Example University",
    )

    assert EducationRequirementTruthGate().validate(_criterion(evidence, requirement)) is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("degree_level", "Bachelor's"),
        ("field_of_study", "Computer Science"),
        ("institution", "Example University"),
    ],
)
def test_gate_rejects_ungrounded_textual_fields(field: str, value: str) -> None:
    requirement = EducationRequirement(**{field: value})

    with pytest.raises(DomainError, match=f"education {field} is not present"):
        EducationRequirementTruthGate().validate(
            _criterion("Degree required.", requirement)
        )


def test_gate_is_case_sensitive_and_does_not_strip_values() -> None:
    with pytest.raises(DomainError, match="degree_level is not present"):
        EducationRequirementTruthGate().validate(
            _criterion(
                "Bachelor's degree required.",
                EducationRequirement(degree_level="bachelor's"),
            )
        )
    with pytest.raises(DomainError, match="degree_level is not present"):
        EducationRequirementTruthGate().validate(
            _criterion(
                "Bachelor's degree required.",
                EducationRequirement(degree_level=" Bachelor's"),
            )
        )


def test_gate_accepts_grounded_status_provenance() -> None:
    evidence = "Candidates currently pursuing a degree may apply."
    requirement = EducationRequirement(
        acceptable_statuses=(EducationRequirementStatus.IN_PROGRESS,),
        status_evidence=(
            EducationRequirementStatusEvidence(
                status=EducationRequirementStatus.IN_PROGRESS,
                evidence="currently pursuing",
            ),
        ),
    )

    assert EducationRequirementTruthGate().validate(_criterion(evidence, requirement)) is None


def test_gate_rejects_ungrounded_status_provenance() -> None:
    requirement = EducationRequirement(
        acceptable_statuses=(EducationRequirementStatus.IN_PROGRESS,),
        status_evidence=(
            EducationRequirementStatusEvidence(
                status=EducationRequirementStatus.IN_PROGRESS,
                evidence="currently enrolled",
            ),
        ),
    )

    with pytest.raises(DomainError, match="status evidence is not present"):
        EducationRequirementTruthGate().validate(
            _criterion("Candidates currently pursuing a degree may apply.", requirement)
        )


def test_gate_rejects_case_mismatch_in_status_provenance() -> None:
    requirement = EducationRequirement(
        acceptable_statuses=(EducationRequirementStatus.IN_PROGRESS,),
        status_evidence=(
            EducationRequirementStatusEvidence(
                status=EducationRequirementStatus.IN_PROGRESS,
                evidence="currently pursuing",
            ),
        ),
    )

    with pytest.raises(DomainError):
        EducationRequirementTruthGate().validate(
            _criterion("Currently pursuing a degree.", requirement)
        )


def test_gate_rejects_status_without_provenance() -> None:
    requirement = EducationRequirement(
        acceptable_statuses=(EducationRequirementStatus.IN_PROGRESS,)
    )

    with pytest.raises(DomainError, match="acceptable status requires status evidence"):
        EducationRequirementTruthGate().validate(
            _criterion("Currently pursuing a degree.", requirement)
        )


def test_gate_requires_provenance_for_each_distinct_status() -> None:
    requirement = EducationRequirement(
        acceptable_statuses=(
            EducationRequirementStatus.COMPLETED,
            EducationRequirementStatus.IN_PROGRESS,
        ),
        status_evidence=(
            EducationRequirementStatusEvidence(
                status=EducationRequirementStatus.IN_PROGRESS,
                evidence="currently enrolled",
            ),
        ),
    )

    with pytest.raises(DomainError, match="acceptable status requires status evidence"):
        EducationRequirementTruthGate().validate(
            _criterion("Graduates and currently enrolled students may apply.", requirement)
        )


def test_gate_accepts_two_statuses_with_independent_provenance() -> None:
    requirement = EducationRequirement(
        acceptable_statuses=(
            EducationRequirementStatus.COMPLETED,
            EducationRequirementStatus.IN_PROGRESS,
        ),
        status_evidence=(
            EducationRequirementStatusEvidence(
                status=EducationRequirementStatus.COMPLETED, evidence="Graduates"
            ),
            EducationRequirementStatusEvidence(
                status=EducationRequirementStatus.IN_PROGRESS,
                evidence="currently enrolled",
            ),
        ),
    )

    assert EducationRequirementTruthGate().validate(
        _criterion("Graduates and currently enrolled students may apply.", requirement)
    ) is None


def test_gate_accepts_duplicate_acceptable_status_with_one_provenance() -> None:
    requirement = EducationRequirement(
        acceptable_statuses=(
            EducationRequirementStatus.COMPLETED,
            EducationRequirementStatus.COMPLETED,
        ),
        status_evidence=(
            EducationRequirementStatusEvidence(
                status=EducationRequirementStatus.COMPLETED, evidence="Graduates"
            ),
        ),
    )

    assert EducationRequirementTruthGate().validate(
        _criterion("Graduates are welcome.", requirement)
    ) is None


def test_gate_checks_duplicate_status_evidence_individually() -> None:
    requirement = EducationRequirement(
        acceptable_statuses=(EducationRequirementStatus.COMPLETED,),
        status_evidence=(
            EducationRequirementStatusEvidence(
                status=EducationRequirementStatus.COMPLETED, evidence="Graduates"
            ),
            EducationRequirementStatusEvidence(
                status=EducationRequirementStatus.COMPLETED, evidence="invented"
            ),
        ),
    )

    with pytest.raises(DomainError, match="status evidence is not present"):
        EducationRequirementTruthGate().validate(
            _criterion("Graduates are welcome.", requirement)
        )


def test_gate_does_not_interpret_status_evidence_semantics() -> None:
    requirement = EducationRequirement(
        acceptable_statuses=(EducationRequirementStatus.COMPLETED,),
        status_evidence=(
            EducationRequirementStatusEvidence(
                status=EducationRequirementStatus.COMPLETED,
                evidence="currently pursuing",
            ),
        ),
    )

    assert EducationRequirementTruthGate().validate(
        _criterion("currently pursuing a degree.", requirement)
    ) is None


def test_gate_type_hints() -> None:
    hints = get_type_hints(EducationRequirementTruthGate.validate)

    assert hints["criterion"] is JobCriterion
    assert hints["return"] is type(None)
