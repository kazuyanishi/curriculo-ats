from typing import get_type_hints

import pytest

from resume_ai.core.exceptions import DomainError
from resume_ai.modules.jobs.application.ports import JobCriteriaExtractor
from resume_ai.modules.jobs.application.services import ExtractJobCriteria
from resume_ai.modules.jobs.domain.entities import (
    CriterionCategory,
    CriterionImportance,
    JobCriteria,
    JobCriterion,
    JobPosting,
)
from resume_ai.modules.jobs.domain.services import JobCriteriaTruthGate


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


class RecordingTruthGate(JobCriteriaTruthGate):
    def __init__(self) -> None:
        self.calls = 0
        self.received: list[tuple[JobPosting, JobCriteria]] = []

    def validate(self, job: JobPosting, criteria: JobCriteria) -> None:
        self.calls += 1
        self.received.append((job, criteria))
        super().validate(job, criteria)


def _job(title: str = "Backend Developer") -> JobPosting:
    return JobPosting(description="Python is required.", title=title)


def _criteria(evidence: str = "Python is required.") -> JobCriteria:
    return JobCriteria(
        criteria=(
            JobCriterion(
                category=CriterionCategory.TECHNOLOGY,
                value="Python",
                evidence=evidence,
                importance=CriterionImportance.REQUIRED,
            ),
        )
    )


def test_extract_job_criteria_extracts_then_validates_and_preserves_identity() -> None:
    job = _job()
    criteria = _criteria()
    extractor = FakeJobCriteriaExtractor(criteria)
    truth_gate = RecordingTruthGate()

    result = ExtractJobCriteria(extractor, truth_gate).execute(job)

    assert result is criteria
    assert extractor.calls == 1
    assert extractor.received_jobs[0] is job
    assert truth_gate.calls == 1
    assert truth_gate.received[0][0] is job
    assert truth_gate.received[0][1] is criteria


def test_extract_job_criteria_delegates_extract_and_validate_on_each_execution() -> None:
    extractor = FakeJobCriteriaExtractor(_criteria())
    truth_gate = RecordingTruthGate()
    service = ExtractJobCriteria(extractor, truth_gate)
    job_a = _job("Backend Developer")
    job_b = _job("Python Developer")

    service.execute(job_a)
    service.execute(job_b)

    assert extractor.calls == 2
    assert truth_gate.calls == 2
    assert extractor.received_jobs == [job_a, job_b]
    assert truth_gate.received == [(job_a, extractor.criteria), (job_b, extractor.criteria)]
    assert truth_gate.received[0][0] is job_a
    assert truth_gate.received[1][0] is job_b


def test_extract_job_criteria_does_not_validate_when_extractor_fails() -> None:
    truth_gate = RecordingTruthGate()

    with pytest.raises(RuntimeError, match="extractor failure"):
        ExtractJobCriteria(FailingJobCriteriaExtractor(), truth_gate).execute(_job())

    assert truth_gate.calls == 0


def test_extract_job_criteria_propagates_truth_gate_failure_without_retry() -> None:
    extractor = FakeJobCriteriaExtractor(_criteria("Kubernetes is required."))
    truth_gate = RecordingTruthGate()

    with pytest.raises(DomainError, match="evidence is not present"):
        ExtractJobCriteria(extractor, truth_gate).execute(_job())

    assert extractor.calls == 1
    assert truth_gate.calls == 1


def test_extract_job_criteria_passes_empty_result_through_gate() -> None:
    empty = JobCriteria()
    extractor = FakeJobCriteriaExtractor(empty)
    truth_gate = RecordingTruthGate()

    result = ExtractJobCriteria(extractor, truth_gate).execute(_job())

    assert result is empty
    assert truth_gate.calls == 1
    assert truth_gate.received[0][1] is empty


def test_extract_job_criteria_constructor_type_hints() -> None:
    hints = get_type_hints(ExtractJobCriteria.__init__)

    assert hints["extractor"] is JobCriteriaExtractor
    assert hints["truth_gate"] is JobCriteriaTruthGate


def test_extract_job_criteria_execute_type_hints() -> None:
    hints = get_type_hints(ExtractJobCriteria.execute)

    assert hints["job"] is JobPosting
    assert hints["return"] is JobCriteria
