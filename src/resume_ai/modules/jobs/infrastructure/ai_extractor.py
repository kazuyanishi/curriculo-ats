import logging
import re
from dataclasses import replace

from resume_ai.integrations.ai.client import StructuredAIClient
from resume_ai.modules.jobs.application.schemas import JobCriteriaInput
from resume_ai.modules.jobs.domain.entities import (
    CriterionCategory,
    JobCriteria,
    JobCriterion,
    JobPosting,
)
from resume_ai.modules.jobs.infrastructure.ai_prompts import (
    JOB_CRITERIA_SYSTEM_PROMPT,
    build_job_criteria_user_prompt,
)

logger = logging.getLogger(__name__)


class AIJobCriteriaExtractor:
    def __init__(self, client: StructuredAIClient, *, best_effort_grounding: bool = False) -> None:
        self._client = client
        self._best_effort_grounding = best_effort_grounding

    def extract(self, job: JobPosting) -> JobCriteria:
        result = self._client.generate(
            system_prompt=JOB_CRITERIA_SYSTEM_PROMPT,
            user_prompt=build_job_criteria_user_prompt(job),
            response_model=JobCriteriaInput,
        )
        criteria = result.to_domain()
        return (
            self._ground_model_evidence(job, criteria)
            if self._best_effort_grounding
            else criteria
        )

    @staticmethod
    def _ground_model_evidence(job: JobPosting, criteria: JobCriteria) -> JobCriteria:
        grounded: list[JobCriterion] = []
        dropped = 0
        for criterion in criteria.criteria:
            if criterion.evidence in job.description:
                grounded.append(criterion)
                continue

            value = criterion.value.strip()
            match = (
                re.search(re.escape(value), job.description, flags=re.IGNORECASE)
                if value
                else None
            )
            if match is None:
                dropped += 1
                continue

            # Keep only literal text from the job. Structured sub-requirements
            # are retained only when their own evidence remains grounded.
            grounded.append(
                replace(
                    criterion,
                    evidence=match.group(0),
                    education_requirement=(
                        criterion.education_requirement
                        if criterion.category is CriterionCategory.EDUCATION
                        and AIJobCriteriaExtractor._requirement_is_grounded(
                            criterion.education_requirement, match.group(0)
                        )
                        else None
                    ),
                    experience_requirement=(
                        criterion.experience_requirement
                        if criterion.category is CriterionCategory.EXPERIENCE
                        and AIJobCriteriaExtractor._requirement_is_grounded(
                            criterion.experience_requirement, match.group(0)
                        )
                        else None
                    ),
                )
            )

        if dropped:
            logger.warning(
                "Dropped %d job criteria that could not be grounded in the description",
                dropped,
            )
        return JobCriteria(criteria=tuple(grounded))

    @staticmethod
    def _requirement_is_grounded(requirement: object, evidence: str) -> bool:
        if requirement is None:
            return False
        for field in ("degree_level", "field_of_study", "institution", "role", "company"):
            value = getattr(requirement, field, None)
            if value is not None and value not in evidence:
                return False
        duration_evidence = getattr(requirement, "minimum_duration_evidence", None)
        if duration_evidence is not None and duration_evidence not in evidence:
            return False
        for item in getattr(requirement, "status_evidence", ()):
            if item.evidence not in evidence:
                return False
        return True
