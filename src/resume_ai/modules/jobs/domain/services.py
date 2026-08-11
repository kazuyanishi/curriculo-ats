from resume_ai.core.exceptions import DomainError
from resume_ai.modules.jobs.domain.entities import JobCriteria, JobPosting


class JobCriteriaTruthGate:
    def validate(self, job: JobPosting, criteria: JobCriteria) -> None:
        for criterion in criteria.criteria:
            if criterion.evidence not in job.description:
                raise DomainError(
                    "Job criterion evidence is not present in the job description"
                )
