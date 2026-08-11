from typing import Protocol

from resume_ai.modules.jobs.domain.entities import JobPosting


class JobRepository(Protocol):
    """Repository contract for retrieving the current job posting."""

    def get(self) -> JobPosting:
        ...
