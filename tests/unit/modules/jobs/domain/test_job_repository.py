from typing import get_type_hints

from resume_ai.modules.jobs.domain.entities import JobPosting
from resume_ai.modules.jobs.domain.repositories import JobRepository


class FakeJobRepository:
    def __init__(self, job: JobPosting) -> None:
        self.job = job

    def get(self) -> JobPosting:
        return self.job


def _get_job(repository: JobRepository) -> JobPosting:
    return repository.get()


def test_job_repository_supports_structural_implementations() -> None:
    job = JobPosting(description="Example job description", title="Backend Developer")
    repository = FakeJobRepository(job)

    result = _get_job(repository)

    assert result is job


def test_job_repository_get_returns_job_posting() -> None:
    hints = get_type_hints(JobRepository.get)

    assert hints["return"] is JobPosting
