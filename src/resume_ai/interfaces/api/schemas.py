from pydantic import BaseModel, ConfigDict

from resume_ai.modules.candidate.application.schemas import CandidateInput
from resume_ai.modules.jobs.application.schemas import JobPostingInput
from resume_ai.modules.jobs.domain.entities import (
    CriterionCategory,
    CriterionImportance,
    EducationRequirementStatus,
    ExperienceDurationUnit,
)
from resume_ai.modules.matching.domain.entities import MatchStatus


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate: CandidateInput
    job: JobPostingInput


class EducationStatusEvidenceResponse(BaseModel):
    status: EducationRequirementStatus
    evidence: str


class EducationRequirementResponse(BaseModel):
    degree_level: str | None = None
    field_of_study: str | None = None
    institution: str | None = None
    acceptable_statuses: list[EducationRequirementStatus] = []
    status_evidence: list[EducationStatusEvidenceResponse] = []


class ExperienceMinimumDurationResponse(BaseModel):
    value: int
    unit: ExperienceDurationUnit


class ExperienceRequirementResponse(BaseModel):
    role: str | None = None
    company: str | None = None
    minimum_duration: ExperienceMinimumDurationResponse | None = None
    minimum_duration_evidence: str | None = None


class JobCriterionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: CriterionCategory
    value: str
    evidence: str
    importance: CriterionImportance
    education_requirement: EducationRequirementResponse | None = None
    experience_requirement: ExperienceRequirementResponse | None = None


class CriterionMatchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criterion: JobCriterionResponse
    status: MatchStatus


class MatchingScoreResponse(BaseModel):
    score: float | None
    coverage: float | None


class GapAnalysisResponse(BaseModel):
    gaps: list[CriterionMatchResponse]
    unsupported: list[CriterionMatchResponse]


class AnalyzeResponse(BaseModel):
    criteria: list[JobCriterionResponse]
    matching: list[CriterionMatchResponse]
    score: MatchingScoreResponse
    gaps: GapAnalysisResponse
    optimized_candidate: CandidateInput
