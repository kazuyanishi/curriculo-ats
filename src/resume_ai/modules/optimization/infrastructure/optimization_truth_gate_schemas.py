from pydantic import BaseModel, ConfigDict

from resume_ai.modules.optimization.application.proposals import OptimizationStatementVerdict


class OptimizationStatementVerificationAI(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    statement_index: int
    verdict: OptimizationStatementVerdict


class ExperienceOptimizationVerificationAI(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    experience_index: int
    statements: tuple[OptimizationStatementVerificationAI, ...]


class CandidateOptimizationVerificationAIResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    experiences: tuple[ExperienceOptimizationVerificationAI, ...]
