from typing import Any

from pydantic import BaseModel, ConfigDict

from resume_ai.modules.candidate.application.schemas import CandidateInput
from resume_ai.modules.jobs.application.schemas import JobPostingInput


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate: CandidateInput
    job: JobPostingInput


class AnalyzeResponse(BaseModel):
    criteria: list[dict[str, Any]]
    matching: list[dict[str, Any]]
    score: dict[str, Any]
    gaps: dict[str, list[dict[str, Any]]]
    optimized_candidate: dict[str, Any]
