from typing import get_type_hints

import pytest

from resume_ai.core.exceptions import DomainError
from resume_ai.modules.jobs.domain.entities import (
    CriterionCategory,
    CriterionImportance,
    EducationRequirement,
    JobCriteria,
    JobCriterion,
    JobPosting,
)
from resume_ai.modules.jobs.domain.services import JobCriteriaTruthGate


def _criterion(value: str, evidence: str) -> JobCriterion:
    return JobCriterion(
        category=CriterionCategory.TECHNOLOGY,
        value=value,
        evidence=evidence,
        importance=CriterionImportance.REQUIRED,
    )


def test_truth_gate_accepts_empty_criteria() -> None:
    JobCriteriaTruthGate().validate(JobPosting(description="Example description"), JobCriteria())


def test_truth_gate_accepts_exact_evidence() -> None:
    job = JobPosting(description="Python is required.")
    criteria = JobCriteria(criteria=(_criterion("Python", "Python is required."),))

    assert JobCriteriaTruthGate().validate(job, criteria) is None


def test_truth_gate_accepts_literal_substring() -> None:
    job = JobPosting(description="About us.\nPython is required.\nBenefits...")
    criteria = JobCriteria(criteria=(_criterion("Python", "Python is required."),))

    JobCriteriaTruthGate().validate(job, criteria)


@pytest.mark.parametrize(
    "evidence",
    [
        "Python knowledge is mandatory.",
        "python is required.",
        " Python is required. ",
    ],
)
def test_truth_gate_rejects_non_literal_evidence(evidence: str) -> None:
    job = JobPosting(description="Python is required.")
    criteria = JobCriteria(criteria=(_criterion("Python", evidence),))

    with pytest.raises(DomainError, match="evidence is not present"):
        JobCriteriaTruthGate().validate(job, criteria)


def test_truth_gate_preserves_line_ending_sensitivity() -> None:
    job = JobPosting(description="Python\r\nDocker")
    valid = JobCriteria(criteria=(_criterion("Python", "Python\r\nDocker"),))
    invalid = JobCriteria(criteria=(_criterion("Python", "Python\nDocker"),))

    JobCriteriaTruthGate().validate(job, valid)
    with pytest.raises(DomainError):
        JobCriteriaTruthGate().validate(job, invalid)


def test_truth_gate_requires_all_criteria_to_be_valid() -> None:
    job = JobPosting(description="Python is required.\nDocker is preferred.")
    criteria = JobCriteria(
        criteria=(
            _criterion("Python", "Python is required."),
            _criterion("Docker", "Docker is preferred."),
            _criterion("Kubernetes", "Kubernetes is required."),
        )
    )

    with pytest.raises(DomainError):
        JobCriteriaTruthGate().validate(job, criteria)

    assert len(criteria.criteria) == 3


def test_truth_gate_allows_multiple_criteria_with_same_evidence() -> None:
    evidence = "Experience with Python and FastAPI is required."
    job = JobPosting(description=evidence)
    criteria = JobCriteria(
        criteria=(_criterion("Python", evidence), _criterion("FastAPI", evidence))
    )

    JobCriteriaTruthGate().validate(job, criteria)


def test_truth_gate_does_not_validate_value_semantics() -> None:
    evidence = "Experience with PostgreSQL databases"
    job = JobPosting(description=evidence)
    criteria = JobCriteria(criteria=(_criterion("Postgres", evidence),))

    JobCriteriaTruthGate().validate(job, criteria)


def test_truth_gate_rejects_grounding_failure_after_global_evidence_passes() -> None:
    evidence = "Bachelor's degree required."
    criterion = JobCriterion(
        category=CriterionCategory.EDUCATION,
        value="Computer Science degree",
        evidence=evidence,
        education_requirement=EducationRequirement(
            degree_level="Bachelor's", field_of_study="Computer Science"
        ),
    )

    with pytest.raises(DomainError, match="field_of_study is not present"):
        JobCriteriaTruthGate().validate(
            JobPosting(description=evidence), JobCriteria(criteria=(criterion,))
        )


def test_truth_gate_runs_global_evidence_before_education_grounding() -> None:
    criterion = JobCriterion(
        category=CriterionCategory.EDUCATION,
        value="Computer Science degree",
        evidence="Invented evidence",
        education_requirement=EducationRequirement(field_of_study="Computer Science"),
    )

    with pytest.raises(DomainError, match="evidence is not present"):
        JobCriteriaTruthGate().validate(
            JobPosting(description="Bachelor's degree required."),
            JobCriteria(criteria=(criterion,)),
        )


def test_truth_gate_validate_type_hints() -> None:
    hints = get_type_hints(JobCriteriaTruthGate.validate)

    assert hints["job"] is JobPosting
    assert hints["criteria"] is JobCriteria
    assert hints["return"] is type(None)
