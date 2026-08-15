from pydantic import BaseModel, ConfigDict


class OptimizedExperienceStatementAI(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    text: str
    source_paths: tuple[str, ...]
    target_match_indexes: tuple[int, ...]


class ExperienceOptimizationAI(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    experience_index: int
    statements: tuple[OptimizedExperienceStatementAI, ...] = ()


class CandidateOptimizationAIResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    experiences: tuple[ExperienceOptimizationAI, ...]
