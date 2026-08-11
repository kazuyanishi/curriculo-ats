import pytest

from resume_ai.core.exceptions import DomainError
from resume_ai.modules.jobs.application.schemas import JobCriteriaInput
from resume_ai.modules.jobs.application.services import ExtractJobCriteria
from resume_ai.modules.jobs.domain.entities import CriterionCategory, JobCriteria, JobPosting
from resume_ai.modules.jobs.domain.services import JobCriteriaTruthGate
from resume_ai.modules.jobs.infrastructure.ai_extractor import AIJobCriteriaExtractor


class FakeStructuredAIClient:
    def __init__(self, result: JobCriteriaInput) -> None:
        self.result = result
        self.calls = 0

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[JobCriteriaInput],
    ) -> JobCriteriaInput:
        self.calls += 1
        return self.result


def _pipeline(response: JobCriteriaInput) -> tuple[FakeStructuredAIClient, ExtractJobCriteria]:
    client = FakeStructuredAIClient(response)
    extractor = AIJobCriteriaExtractor(client)
    service = ExtractJobCriteria(extractor, JobCriteriaTruthGate())
    return client, service


def test_ai_job_criteria_pipeline_accepts_grounded_criteria() -> None:
    job = JobPosting(description="Python is required.\nDocker is preferred.")
    response = JobCriteriaInput(
        criteria=[
            {
                "category": "technology",
                "value": "Python",
                "evidence": "Python is required.",
                "importance": "required",
            },
            {
                "category": "tool",
                "value": "Docker",
                "evidence": "Docker is preferred.",
                "importance": "preferred",
            },
        ]
    )
    client, service = _pipeline(response)

    result = service.execute(job)

    assert isinstance(result, JobCriteria)
    assert [criterion.value for criterion in result.criteria] == ["Python", "Docker"]
    assert [criterion.category for criterion in result.criteria] == [
        CriterionCategory.TECHNOLOGY,
        CriterionCategory.TOOL,
    ]
    assert [criterion.importance.value for criterion in result.criteria] == [
        "required",
        "preferred",
    ]
    assert client.calls == 1


def test_ai_job_criteria_pipeline_blocks_ungrounded_evidence() -> None:
    job = JobPosting(description="Python is required.")
    response = JobCriteriaInput(
        criteria=[
            {
                "category": "technology",
                "value": "Python",
                "evidence": "Python is required.",
            },
            {
                "category": "technology",
                "value": "Kubernetes",
                "evidence": "Kubernetes is required.",
            },
        ]
    )
    client, service = _pipeline(response)

    with pytest.raises(DomainError):
        service.execute(job)

    assert client.calls == 1


def test_ai_job_criteria_pipeline_accepts_empty_result() -> None:
    client, service = _pipeline(JobCriteriaInput())

    result = service.execute(JobPosting(description="No reliable criteria."))

    assert result == JobCriteria()
    assert client.calls == 1
