from resume_ai.modules.jobs.application.ports import JobCriteriaExtractor
from resume_ai.modules.jobs.domain.entities import JobCriteria, JobPosting
from resume_ai.modules.jobs.domain.repositories import JobRepository
from resume_ai.modules.jobs.domain.services import JobCriteriaTruthGate


class LoadJob:
    def __init__(self, repository: JobRepository) -> None:
        self._repository = repository

    def execute(self) -> JobPosting:
        return self._repository.get()


class ExtractJobCriteria:
    def __init__(
        self,
        extractor: JobCriteriaExtractor,
        truth_gate: JobCriteriaTruthGate,
    ) -> None:
        self._extractor = extractor
        self._truth_gate = truth_gate

    def execute(self, job: JobPosting) -> JobCriteria:
        criteria = self._extractor.extract(job)
        self._truth_gate.validate(job, criteria)
        return criteria
