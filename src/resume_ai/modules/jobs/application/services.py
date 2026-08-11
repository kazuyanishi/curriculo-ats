from resume_ai.modules.jobs.domain.entities import JobPosting
from resume_ai.modules.jobs.domain.repositories import JobRepository


class LoadJob:
    def __init__(self, repository: JobRepository) -> None:
        self._repository = repository

    def execute(self) -> JobPosting:
        return self._repository.get()
