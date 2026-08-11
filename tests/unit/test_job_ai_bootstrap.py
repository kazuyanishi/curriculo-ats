import inspect
from typing import get_type_hints

import pytest

import resume_ai.bootstrap as bootstrap
from resume_ai.core.exceptions import DomainError
from resume_ai.integrations.ai.config import AIConfig
from resume_ai.modules.jobs.application.schemas import JobCriteriaInput
from resume_ai.modules.jobs.application.services import ExtractJobCriteria
from resume_ai.modules.jobs.domain.entities import (
    CriterionCategory,
    CriterionImportance,
    JobCriteria,
    JobPosting,
)


class FakeOpenAIStructuredAIClient:
    instances: list["FakeOpenAIStructuredAIClient"] = []
    result = JobCriteriaInput(
        criteria=[
            {
                "category": CriterionCategory.SKILL,
                "value": "Python",
                "evidence": "Python is required.",
                "importance": CriterionImportance.REQUIRED,
            }
        ]
    )

    def __init__(self, config: AIConfig) -> None:
        self.config = config
        self.__class__.instances.append(self)

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[JobCriteriaInput],
    ) -> JobCriteriaInput:
        assert system_prompt
        assert user_prompt == "Python is required."
        assert response_model is JobCriteriaInput
        return self.result


def test_builder_returns_extract_job_criteria(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(bootstrap, "OpenAIStructuredAIClient", FakeOpenAIStructuredAIClient)

    service = bootstrap.build_extract_job_criteria(AIConfig("key", "model"))

    assert isinstance(service, ExtractJobCriteria)


def test_builder_composes_the_pipeline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(bootstrap, "OpenAIStructuredAIClient", FakeOpenAIStructuredAIClient)
    service = bootstrap.build_extract_job_criteria(AIConfig("key", "model"))

    result = service.execute(JobPosting(description="Python is required."))

    assert isinstance(result, JobCriteria)
    assert result.criteria[0].value == "Python"
    assert result.criteria[0].evidence == "Python is required."


def test_builder_keeps_truth_gate_active(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class HallucinatingClient(FakeOpenAIStructuredAIClient):
        result = JobCriteriaInput(
            criteria=[
                {
                    "category": CriterionCategory.TOOL,
                    "value": "Kubernetes",
                    "evidence": "Kubernetes is required.",
                }
            ]
        )

    monkeypatch.setattr(bootstrap, "OpenAIStructuredAIClient", HallucinatingClient)
    service = bootstrap.build_extract_job_criteria(AIConfig("key", "model"))

    with pytest.raises(DomainError):
        service.execute(JobPosting(description="Python is required."))


def test_builder_passes_the_same_config_instance_to_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    FakeOpenAIStructuredAIClient.instances.clear()
    monkeypatch.setattr(bootstrap, "OpenAIStructuredAIClient", FakeOpenAIStructuredAIClient)
    config = AIConfig("key", "model")

    bootstrap.build_extract_job_criteria(config)

    assert FakeOpenAIStructuredAIClient.instances[0].config is config


def test_builder_type_hints() -> None:
    hints = get_type_hints(bootstrap.build_extract_job_criteria)
    parameters = inspect.signature(bootstrap.build_extract_job_criteria).parameters

    assert hints["config"] is AIConfig
    assert hints["return"] is ExtractJobCriteria
    assert parameters["config"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
