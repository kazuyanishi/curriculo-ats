from typing import get_type_hints

import pytest

from resume_ai.core.exceptions import DomainError
from resume_ai.modules.jobs.domain.entities import (
    CriterionCategory,
    ExperienceDurationUnit,
    ExperienceMinimumDuration,
    ExperienceRequirement,
    JobCriteria,
    JobCriterion,
    JobPosting,
)
from resume_ai.modules.jobs.domain.services import (
    ExperienceRequirementTruthGate,
    JobCriteriaTruthGate,
)


def _criterion(
    evidence: str,
    requirement: ExperienceRequirement | None = None,
) -> JobCriterion:
    return JobCriterion(
        category=CriterionCategory.EXPERIENCE,
        value="experience requirement",
        evidence=evidence,
        experience_requirement=requirement,
    )


def _duration() -> ExperienceMinimumDuration:
    return ExperienceMinimumDuration(3, ExperienceDurationUnit.YEARS)


def test_gate_is_noop_without_experience_requirement() -> None:
    assert ExperienceRequirementTruthGate().validate(_criterion("Experience required.")) is None


def test_gate_accepts_literal_role() -> None:
    requirement = ExperienceRequirement(role="Backend Developer")

    assert ExperienceRequirementTruthGate().validate(
        _criterion("3 years as Backend Developer", requirement)
    ) is None


def test_gate_rejects_missing_role() -> None:
    with pytest.raises(DomainError, match="experience role is not present"):
        ExperienceRequirementTruthGate().validate(
            _criterion(
                "3 years of experience required.",
                ExperienceRequirement(role="Backend Developer"),
            )
        )


def test_gate_role_is_case_sensitive() -> None:
    with pytest.raises(DomainError, match="experience role is not present"):
        ExperienceRequirementTruthGate().validate(
            _criterion(
                "3 years as backend developer",
                ExperienceRequirement(role="Backend Developer"),
            )
        )


def test_gate_accepts_literal_company() -> None:
    requirement = ExperienceRequirement(company="Example Corp")

    assert ExperienceRequirementTruthGate().validate(
        _criterion("Experience at Example Corp", requirement)
    ) is None


def test_gate_rejects_missing_company() -> None:
    with pytest.raises(DomainError, match="experience company is not present"):
        ExperienceRequirementTruthGate().validate(
            _criterion("Experience required.", ExperienceRequirement(company="Example Corp"))
        )


def test_gate_accepts_grounded_duration_evidence() -> None:
    requirement = ExperienceRequirement(
        minimum_duration=_duration(),
        minimum_duration_evidence="3 years",
    )

    assert ExperienceRequirementTruthGate().validate(
        _criterion("3 years of experience required.", requirement)
    ) is None


def test_gate_rejects_duration_without_evidence() -> None:
    with pytest.raises(DomainError, match="requires duration evidence"):
        ExperienceRequirementTruthGate().validate(
            _criterion(
                "3 years of experience required.",
                ExperienceRequirement(minimum_duration=_duration()),
            )
        )


def test_gate_rejects_duration_evidence_not_present() -> None:
    requirement = ExperienceRequirement(
        minimum_duration=_duration(),
        minimum_duration_evidence="4 years",
    )

    with pytest.raises(DomainError, match="experience duration evidence is not present"):
        ExperienceRequirementTruthGate().validate(
            _criterion("3 years of experience required.", requirement)
        )


def test_gate_does_not_interpret_duration_semantically() -> None:
    requirement = ExperienceRequirement(
        minimum_duration=ExperienceMinimumDuration(4, ExperienceDurationUnit.YEARS),
        minimum_duration_evidence="3 years",
    )

    assert ExperienceRequirementTruthGate().validate(
        _criterion("3 years of experience required.", requirement)
    ) is None


def test_gate_accepts_all_grounded_experience_dimensions() -> None:
    requirement = ExperienceRequirement(
        role="Backend Developer",
        company="Example Corp",
        minimum_duration=_duration(),
        minimum_duration_evidence="3 years",
    )

    assert ExperienceRequirementTruthGate().validate(
        _criterion(
            "3 years of experience as Backend Developer at Example Corp",
            requirement,
        )
    ) is None


def test_job_criteria_truth_gate_executes_experience_gate() -> None:
    evidence = "3 years of experience required."
    criterion = _criterion(evidence, ExperienceRequirement(role="Backend Developer"))

    with pytest.raises(DomainError, match="experience role is not present"):
        JobCriteriaTruthGate().validate(
            JobPosting(description=evidence), JobCriteria(criteria=(criterion,))
        )


def test_experience_truth_gate_type_hints() -> None:
    hints = get_type_hints(ExperienceRequirementTruthGate.validate)

    assert hints["criterion"] is JobCriterion
    assert hints["return"] is type(None)
