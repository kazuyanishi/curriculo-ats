from typing import get_type_hints

import pytest

from resume_ai.integrations.ai.client import StructuredAIClient
from resume_ai.modules.jobs.application.ports import JobCriteriaExtractor
from resume_ai.modules.jobs.application.schemas import JobCriteriaInput
from resume_ai.modules.jobs.domain.entities import (
    CriterionCategory,
    EducationRequirementStatus,
    EducationRequirementStatusEvidence,
    ExperienceDurationUnit,
    JobCriteria,
    JobPosting,
)
from resume_ai.modules.jobs.infrastructure.ai_extractor import AIJobCriteriaExtractor
from resume_ai.modules.jobs.infrastructure.ai_prompts import JOB_CRITERIA_SYSTEM_PROMPT


class FakeStructuredAIClient:
    def __init__(self, result: JobCriteriaInput | None = None) -> None:
        self.result = JobCriteriaInput() if result is None else result
        self.calls = 0
        self.system_prompt = None
        self.user_prompt = None
        self.response_model = None

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[JobCriteriaInput],
    ) -> JobCriteriaInput:
        self.calls += 1
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self.response_model = response_model
        return self.result


class FailingStructuredAIClient:
    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[JobCriteriaInput],
    ) -> JobCriteriaInput:
        raise RuntimeError("AI failure")


def _extract(extractor: JobCriteriaExtractor, job: JobPosting) -> JobCriteria:
    return extractor.extract(job)


def test_ai_extractor_converts_response_to_domain() -> None:
    response = JobCriteriaInput(
        criteria=[
            {
                "category": "technology",
                "value": "Python",
                "evidence": "Python is required.",
                "importance": "required",
            }
        ]
    )
    client = FakeStructuredAIClient(response)
    job = JobPosting(description="Python is required.")

    result = AIJobCriteriaExtractor(client).extract(job)

    assert isinstance(result, JobCriteria)
    assert result.criteria[0].value == "Python"
    assert result.criteria[0].evidence == "Python is required."


def test_ai_extractor_converts_structured_education_response_to_domain() -> None:
    response = JobCriteriaInput(
        criteria=[
            {
                "category": "education",
                "value": "Bachelor's degree in Computer Science",
                "evidence": "Bachelor's degree in Computer Science is required.",
                "importance": "required",
                "education_requirement": {
                    "degree_level": "Bachelor's",
                    "field_of_study": "Computer Science",
                    "acceptable_statuses": ["completed"],
                },
            }
        ]
    )
    job = JobPosting(
        description="Bachelor's degree in Computer Science is required."
    )

    result = AIJobCriteriaExtractor(FakeStructuredAIClient(response)).extract(job)

    criterion = result.criteria[0]
    requirement = criterion.education_requirement
    assert criterion.category is CriterionCategory.EDUCATION
    assert requirement is not None
    assert requirement.degree_level == "Bachelor's"
    assert requirement.field_of_study == "Computer Science"
    assert requirement.institution is None
    assert requirement.acceptable_statuses == (EducationRequirementStatus.COMPLETED,)
    assert criterion.evidence == (
        "Bachelor's degree in Computer Science is required."
    )


def test_ai_extractor_converts_in_progress_status_provenance_to_domain() -> None:
    response = JobCriteriaInput(
        criteria=[
            {
                "category": "education",
                "value": "Currently pursuing Computer Science",
                "evidence": (
                    "Candidates currently pursuing a degree "
                    "in Computer Science may apply."
                ),
                "education_requirement": {
                    "field_of_study": "Computer Science",
                    "acceptable_statuses": ["in_progress"],
                    "status_evidence": [
                        {
                            "status": "in_progress",
                            "evidence": "currently pursuing",
                        }
                    ],
                },
            }
        ]
    )

    result = AIJobCriteriaExtractor(FakeStructuredAIClient(response)).extract(
        JobPosting(description=response.criteria[0].evidence)
    )

    status_evidence = result.criteria[0].education_requirement.status_evidence
    assert isinstance(status_evidence[0], EducationRequirementStatusEvidence)
    assert status_evidence[0].status is EducationRequirementStatus.IN_PROGRESS
    assert status_evidence[0].evidence == "currently pursuing"


def test_ai_extractor_converts_structured_experience_response_to_domain() -> None:
    response = JobCriteriaInput(
        criteria=[
            {
                "category": "experience",
                "value": "Backend Developer experience",
                "evidence": "3 years of experience as Backend Developer",
                "experience_requirement": {
                    "role": "Backend Developer",
                    "minimum_duration": {"value": 3, "unit": "years"},
                    "minimum_duration_evidence": "3 years",
                },
            }
        ]
    )

    result = AIJobCriteriaExtractor(FakeStructuredAIClient(response)).extract(
        JobPosting(description=response.criteria[0].evidence)
    )

    criterion = result.criteria[0]
    requirement = criterion.experience_requirement
    assert criterion.category is CriterionCategory.EXPERIENCE
    assert requirement is not None
    assert requirement.role == "Backend Developer"
    assert requirement.company is None
    assert requirement.minimum_duration is not None
    assert requirement.minimum_duration.value == 3
    assert requirement.minimum_duration.unit is ExperienceDurationUnit.YEARS
    assert requirement.minimum_duration_evidence == "3 years"
    assert criterion.evidence == "3 years of experience as Backend Developer"


def test_ai_extractor_preserves_independent_provenance_for_both_statuses() -> None:
    response = JobCriteriaInput(
        criteria=[
            {
                "category": "education",
                "value": "Graduates and currently enrolled students",
                "evidence": "Graduates and currently enrolled students may apply.",
                "education_requirement": {
                    "acceptable_statuses": ["completed", "in_progress"],
                    "status_evidence": [
                        {"status": "completed", "evidence": "Graduates"},
                        {
                            "status": "in_progress",
                            "evidence": "currently enrolled",
                        },
                    ],
                },
            }
        ]
    )

    result = AIJobCriteriaExtractor(FakeStructuredAIClient(response)).extract(
        JobPosting(description=response.criteria[0].evidence)
    )

    requirement = result.criteria[0].education_requirement
    assert requirement is not None
    assert [
        (item.status, item.evidence) for item in requirement.status_evidence
    ] == [
        (EducationRequirementStatus.COMPLETED, "Graduates"),
        (EducationRequirementStatus.IN_PROGRESS, "currently enrolled"),
    ]


def test_ai_extractor_calls_client_with_prompts_and_schema() -> None:
    client = FakeStructuredAIClient()
    job = JobPosting(description="  Python is required.\n")

    AIJobCriteriaExtractor(client).extract(job)

    assert client.calls == 1
    assert client.system_prompt == JOB_CRITERIA_SYSTEM_PROMPT
    assert client.user_prompt == job.description
    assert client.response_model is JobCriteriaInput


def test_ai_extractor_supports_structural_extractor_contract() -> None:
    job = JobPosting(description="Python is required.")

    result = _extract(AIJobCriteriaExtractor(FakeStructuredAIClient()), job)

    assert isinstance(result, JobCriteria)


def test_ai_extractor_converts_empty_response() -> None:
    result = AIJobCriteriaExtractor(FakeStructuredAIClient(JobCriteriaInput())).extract(
        JobPosting(description="No criteria")
    )

    assert result == JobCriteria()


def test_ai_extractor_calls_client_each_time() -> None:
    client = FakeStructuredAIClient()
    extractor = AIJobCriteriaExtractor(client)
    job = JobPosting(description="Python is required.")

    extractor.extract(job)
    extractor.extract(job)

    assert client.calls == 2


def test_ai_extractor_propagates_client_error() -> None:
    with pytest.raises(RuntimeError, match="AI failure"):
        AIJobCriteriaExtractor(FailingStructuredAIClient()).extract(
            JobPosting(description="Python is required.")
        )


def test_ai_extractor_type_hints() -> None:
    constructor_hints = get_type_hints(AIJobCriteriaExtractor.__init__)
    extract_hints = get_type_hints(AIJobCriteriaExtractor.extract)

    assert constructor_hints["client"] is StructuredAIClient
    assert extract_hints["job"] is JobPosting
    assert extract_hints["return"] is JobCriteria
