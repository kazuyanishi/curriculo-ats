from typing import get_type_hints

import pytest

from resume_ai.modules.jobs.application.ports import JobCriteriaExtractor
from resume_ai.modules.jobs.application.services import ExtractJobCriteria
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
        self.calls = 0
        self.received_jobs: list[JobPosting] = []

    def extract(self, job: JobPosting) -> JobCriteria:
        self.calls += 1
        self.received_jobs.append(job)
        return self.criteria


class FailingJobCriteriaExtractor:
    def extract(self, job: JobPosting) -> JobCriteria:
        raise RuntimeError("extractor failure")


def _job() -> JobPosting:
    return JobPosting(description="Python is required.", title="Backend Developer")


def _criteria() -> JobCriteria:
    return JobCriteria(
        criteria=(
            JobCriterion(
                category=CriterionCategory.TECHNOLOGY,
                value="Python",
                evidence="Python is required.",
                importance=CriterionImportance.REQUIRED,
            ),
        )
    )


def test_extract_job_criteria_returns_same_result_and_passes_same_job() -> None:
    job = _job()
    criteria = _criteria()
    extractor = FakeJobCriteriaExtractor(criteria)

    result = ExtractJobCriteria(extractor).execute(job)

    assert result is criteria
    assert extractor.received_jobs == [job]
    assert extractor.received_jobs[0] is job
    assert extractor.calls == 1


def test_extract_job_criteria_delegates_on_each_execution() -> None:
    extractor = FakeJobCriteriaExtractor(_criteria())
    service = ExtractJobCriteria(extractor)
    job_a = _job()
    job_b = JobPosting(description="Docker is preferred.")

    service.execute(job_a)
    service.execute(job_b)

    assert extractor.calls == 2
    assert extractor.received_jobs == [job_a, job_b]
    assert extractor.received_jobs[0] is job_a
    assert extractor.received_jobs[1] is job_b


def test_extract_job_criteria_propagates_extractor_exception() -> None:
    with pytest.raises(RuntimeError, match="extractor failure"):
        ExtractJobCriteria(FailingJobCriteriaExtractor()).execute(_job())


def test_extract_job_criteria_constructor_type_hint() -> None:
    hints = get_type_hints(ExtractJobCriteria.__init__)

    assert hints["extractor"] is JobCriteriaExtractor


def test_extract_job_criteria_execute_type_hints() -> None:
    hints = get_type_hints(ExtractJobCriteria.execute)

    assert hints["job"] is JobPosting
    assert hints["return"] is JobCriteria


def test_extract_job_criteria_allows_empty_result() -> None:
    empty = JobCriteria()

    result = ExtractJobCriteria(FakeJobCriteriaExtractor(empty)).execute(_job())

    assert result is empty
