from resume_ai.integrations.ai.client import StructuredAIClient
from resume_ai.modules.jobs.application.schemas import JobCriteriaInput
from resume_ai.modules.jobs.domain.entities import JobCriteria, JobPosting
from resume_ai.modules.jobs.infrastructure.ai_prompts import (
    JOB_CRITERIA_SYSTEM_PROMPT,
    build_job_criteria_user_prompt,
)


class AIJobCriteriaExtractor:
    def __init__(self, client: StructuredAIClient) -> None:
        self._client = client

    def extract(self, job: JobPosting) -> JobCriteria:
        result = self._client.generate(
            system_prompt=JOB_CRITERIA_SYSTEM_PROMPT,
            user_prompt=build_job_criteria_user_prompt(job),
            response_model=JobCriteriaInput,
        )
        return result.to_domain()
