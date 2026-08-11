from typing import get_type_hints

import pytest

from resume_ai.modules.jobs.application.services import LoadJob
from resume_ai.modules.jobs.domain.entities import JobPosting
from resume_ai.modules.jobs.domain.repositories import JobRepository


class FakeJobRepository:
    def __init__(self, job: JobPosting) -> None:
        self.job = job
        self.get_calls = 0

    def get(self) -> JobPosting:
        self.get_calls += 1
        return self.job


class FailingJobRepository:
    def get(self) -> JobPosting:
        raise RuntimeError("repository failure")


def test_load_job_returns_repository_job() -> None:
    job = JobPosting(description="Example job description", title="Backend Developer")
    repository = FakeJobRepository(job)

    result = LoadJob(repository).execute()

    assert result is job
    assert repository.get_calls == 1


def test_load_job_delegates_on_each_execution() -> None:
    job = JobPosting(description="Example job description")
    repository = FakeJobRepository(job)
    service = LoadJob(repository)

    service.execute()
    service.execute()

    assert repository.get_calls == 2


def test_load_job_propagates_repository_exception() -> None:
    with pytest.raises(RuntimeError, match="repository failure"):
        LoadJob(FailingJobRepository()).execute()


def test_load_job_constructor_uses_job_repository_contract() -> None:
    hints = get_type_hints(LoadJob.__init__)

    assert hints["repository"] is JobRepository


def test_load_job_execute_returns_job_posting() -> None:
    hints = get_type_hints(LoadJob.execute)

    assert hints["return"] is JobPosting
