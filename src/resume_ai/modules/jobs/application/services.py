from resume_ai.modules.jobs.application.ports import JobCriteriaExtractor
from resume_ai.modules.jobs.domain.entities import JobCriteria, JobPosting
from resume_ai.modules.jobs.domain.repositories import JobRepository


class LoadJob:
    def __init__(self, repository: JobRepository) -> None:
        self._repository = repository

    def execute(self) -> JobPosting:
        return self._repository.get()


class ExtractJobCriteria:
    def __init__(self, extractor: JobCriteriaExtractor) -> None:
        self._extractor = extractor

    def execute(self, job: JobPosting) -> JobCriteria:
        return self._extractor.extract(job)
