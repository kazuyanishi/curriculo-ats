from typing import get_type_hints

import pytest
from pydantic import ValidationError

from resume_ai.modules.jobs.application.schemas import (
    EducationRequirementInput,
    EducationRequirementStatusEvidenceInput,
    JobCriteriaInput,
    JobCriterionInput,
)
from resume_ai.modules.jobs.domain.entities import (
    CriterionCategory,
    EducationRequirementStatus,
    EducationRequirementStatusEvidence,
)


def test_status_evidence_input_converts_status_string_and_preserves_evidence() -> None:
    schema = EducationRequirementStatusEvidenceInput(
        status="in_progress", evidence="  currently pursuing  "
    )

    assert schema.status is EducationRequirementStatus.IN_PROGRESS
    assert schema.evidence == "  currently pursuing  "
    assert schema.to_domain() == EducationRequirementStatusEvidence(
        status=EducationRequirementStatus.IN_PROGRESS,
        evidence="  currently pursuing  ",
    )


@pytest.mark.parametrize("evidence", ["", "   ", "\n\t"])
def test_status_evidence_input_rejects_blank_evidence(evidence: str) -> None:
    with pytest.raises(ValidationError):
        EducationRequirementStatusEvidenceInput(status="completed", evidence=evidence)


def test_status_evidence_input_rejects_invalid_status_and_extra_fields() -> None:
    with pytest.raises(ValidationError):
        EducationRequirementStatusEvidenceInput(status="graduated", evidence="graduates")
    with pytest.raises(ValidationError):
        EducationRequirementStatusEvidenceInput(
            status="completed", evidence="graduates", source="job"
        )


def test_status_evidence_input_is_frozen() -> None:
    schema = EducationRequirementStatusEvidenceInput(
        status=EducationRequirementStatus.COMPLETED, evidence="graduates"
    )

    with pytest.raises(ValidationError):
        schema.evidence = "changed"


def test_education_requirement_status_evidence_defaults_to_empty_tuple() -> None:
    schema = EducationRequirementInput(acceptable_statuses=["completed"])

    assert schema.status_evidence == ()
    assert schema.to_domain().status_evidence == ()


def test_education_requirement_input_converts_list_to_tuple_and_preserves_order() -> None:
    schema = EducationRequirementInput(
        acceptable_statuses=["completed", "in_progress"],
        status_evidence=[
            {"status": "completed", "evidence": "graduates"},
            {"status": "in_progress", "evidence": "currently enrolled"},
            {"status": "completed", "evidence": "degree awarded"},
        ],
    )

    assert isinstance(schema.status_evidence, tuple)
    assert all(
        isinstance(item, EducationRequirementStatusEvidenceInput)
        for item in schema.status_evidence
    )
    assert [item.status for item in schema.status_evidence] == [
        EducationRequirementStatus.COMPLETED,
        EducationRequirementStatus.IN_PROGRESS,
        EducationRequirementStatus.COMPLETED,
    ]
    assert [item.evidence for item in schema.status_evidence] == [
        "graduates",
        "currently enrolled",
        "degree awarded",
    ]


@pytest.mark.parametrize("value", ["graduates", 1, None])
def test_education_requirement_input_rejects_primitive_status_evidence_items(
    value: object,
) -> None:
    with pytest.raises(ValidationError):
        EducationRequirementInput(
            acceptable_statuses=["completed"], status_evidence=[value]
        )


def test_education_requirement_input_rejects_nested_extra_fields() -> None:
    with pytest.raises(ValidationError):
        EducationRequirementInput(
            acceptable_statuses=["completed"],
            status_evidence=[
                {"status": "completed", "evidence": "graduates", "source": "job"}
            ],
        )


def test_status_evidence_must_use_an_acceptable_status() -> None:
    with pytest.raises(ValidationError):
        EducationRequirementInput(
            field_of_study="Computer Science",
            acceptable_statuses=["completed"],
            status_evidence=[
                {"status": "in_progress", "evidence": "currently enrolled"}
            ],
        )


def test_status_evidence_requires_acceptable_statuses() -> None:
    with pytest.raises(ValidationError):
        EducationRequirementInput(
            field_of_study="Computer Science",
            status_evidence=[{"status": "completed", "evidence": "graduates"}],
        )


def test_status_evidence_alone_does_not_define_a_requirement() -> None:
    with pytest.raises(ValidationError):
        EducationRequirementInput(
            status_evidence=[{"status": "completed", "evidence": "graduates"}]
        )


def test_education_requirement_input_converts_status_evidence_to_domain() -> None:
    schema = EducationRequirementInput(
        field_of_study="  Computer Science  ",
        acceptable_statuses=["completed", "in_progress"],
        status_evidence=[
            {"status": "completed", "evidence": "  graduates  "},
            {"status": "in_progress", "evidence": "  currently enrolled  "},
        ],
    )

    domain = schema.to_domain()

    assert all(
        isinstance(item, EducationRequirementStatusEvidence)
        for item in domain.status_evidence
    )
    assert [(item.status, item.evidence) for item in domain.status_evidence] == [
        (EducationRequirementStatus.COMPLETED, "  graduates  "),
        (EducationRequirementStatus.IN_PROGRESS, "  currently enrolled  "),
    ]


def test_job_criterion_input_propagates_status_evidence_to_domain() -> None:
    schema = JobCriterionInput(
        category="education",
        value="Computer Science degree",
        evidence="Degree required",
        education_requirement={
            "field_of_study": "Computer Science",
            "acceptable_statuses": ["completed"],
            "status_evidence": [
                {"status": "completed", "evidence": "graduates"}
            ],
        },
    )

    domain = schema.to_domain()

    assert domain.category is CriterionCategory.EDUCATION
    assert domain.education_requirement is not None
    assert isinstance(
        domain.education_requirement.status_evidence[0],
        EducationRequirementStatusEvidence,
    )
    assert domain.education_requirement.status_evidence[0].evidence == "graduates"


def test_job_criteria_input_propagates_external_status_evidence_payload() -> None:
    schema = JobCriteriaInput(
        criteria=[
            {
                "category": "education",
                "value": "Computer Science degree",
                "evidence": "Degree required",
                "education_requirement": {
                    "field_of_study": "Computer Science",
                    "acceptable_statuses": ["completed", "in_progress"],
                    "status_evidence": [
                        {"status": "completed", "evidence": "graduates"},
                        {
                            "status": "in_progress",
                            "evidence": "currently enrolled",
                        },
                    ],
                },
            }
        ]
    )

    domain = schema.to_domain()
    requirement = domain.criteria[0].education_requirement

    assert requirement is not None
    assert [(item.status, item.evidence) for item in requirement.status_evidence] == [
        (EducationRequirementStatus.COMPLETED, "graduates"),
        (EducationRequirementStatus.IN_PROGRESS, "currently enrolled"),
    ]


def test_status_evidence_to_domain_annotation_returns_domain_entity() -> None:
    assert (
        get_type_hints(EducationRequirementStatusEvidenceInput.to_domain)["return"]
        is EducationRequirementStatusEvidence
    )
