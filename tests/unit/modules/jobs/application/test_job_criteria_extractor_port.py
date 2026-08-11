from typing import get_type_hints

from resume_ai.modules.jobs.application.ports import JobCriteriaExtractor
from resume_ai.modules.jobs.domain.entities import (
    CriterionCategory,
    CriterionImportance,
    JobCriteria,
    JobCriterion,
    JobPosting,
)


class FakeJobCriteriaExtractor:
    def __init__(self, criteria: JobCriteria) -> None:
        self.criteria = criteria

    def extract(self, job: JobPosting) -> JobCriteria:
        return self.criteria


def _extract(extractor: JobCriteriaExtractor, job: JobPosting) -> JobCriteria:
    return extractor.extract(job)


def test_job_criteria_extractor_supports_structural_implementations() -> None:
    job = JobPosting(description="Python is required.")
    criterion = JobCriterion(
        category=CriterionCategory.TECHNOLOGY,
        value="Python",
        evidence="Python is required.",
        importance=CriterionImportance.REQUIRED,
    )
    criteria = JobCriteria(criteria=(criterion,))

    result = _extract(FakeJobCriteriaExtractor(criteria), job)

    assert result is criteria


def test_job_criteria_extractor_job_parameter_type_hint() -> None:
    hints = get_type_hints(JobCriteriaExtractor.extract)

    assert hints["job"] is JobPosting


def test_job_criteria_extractor_return_type_hint() -> None:
    hints = get_type_hints(JobCriteriaExtractor.extract)

    assert hints["return"] is JobCriteria


def test_job_criteria_extractor_allows_empty_result() -> None:
    job = JobPosting(description="No reliable criteria")
    empty = JobCriteria()

    result = _extract(FakeJobCriteriaExtractor(empty), job)

    assert result is empty
