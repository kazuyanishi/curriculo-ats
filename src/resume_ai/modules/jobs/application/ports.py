from typing import Protocol

from resume_ai.modules.jobs.domain.entities import JobCriteria, JobPosting


class JobCriteriaExtractor(Protocol):
    """Contract for extracting structured criteria from a job posting."""

    def extract(self, job: JobPosting) -> JobCriteria:
        ...
